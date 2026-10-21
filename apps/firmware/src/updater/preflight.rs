//! Checks that must pass before a release request can succeed.
//!
//! They run cheapest first, so a failure names its cause (no clock, no
//! internet, unreachable host) instead of surfacing as a TLS error or timeout.

use std::{
    net::{IpAddr, SocketAddr},
    time::{Duration, SystemTime},
};

use reqwest::Url;
use tokio::{
    net::{TcpStream, lookup_host},
    time::timeout,
};

use super::Error;

/// No firmware with this code was built before 2026-01-01T00:00:00Z, so an
/// earlier clock was never set; certificate validation would fail.
const EARLIEST_PLAUSIBLE: Duration = Duration::from_secs(1_767_225_600);
/// Bounds each network probe, well under the request timeout.
const PROBE: Duration = Duration::from_secs(5);

/// Runs every check against the host serving `feed`.
pub(super) async fn run(feed: &str) -> Result<(), Error> {
    clock(SystemTime::now())?;
    let url = Url::parse(feed).map_err(|error| Error::InvalidFeed(error.to_string()))?;
    let (Some(host), Some(port)) = (url.host_str(), url.port_or_known_default()) else {
        return Err(Error::InvalidFeed(feed.to_owned()));
    };
    // URLs bracket IPv6 literals; literals need no name resolution.
    let addresses = match host
        .trim_start_matches('[')
        .trim_end_matches(']')
        .parse::<IpAddr>()
    {
        Ok(ip) => vec![SocketAddr::new(ip, port)],
        Err(_) => resolve(host, port).await?,
    };
    reach(host, &addresses).await
}

/// The system clock must be set for TLS certificates to validate.
fn clock(now: SystemTime) -> Result<(), Error> {
    let since_epoch = now
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap_or_default();
    if since_epoch < EARLIEST_PLAUSIBLE {
        return Err(Error::ClockNotSet);
    }
    Ok(())
}

/// Name resolution fails first when the device has no internet connection.
///
/// The name is resolved fully qualified: otherwise the resolver may append a
/// local search domain, and some routers answer every name under theirs, so
/// an unknown host would appear to resolve.
async fn resolve(host: &str, port: u16) -> Result<Vec<SocketAddr>, Error> {
    let offline = || Error::Offline {
        host: host.to_owned(),
    };
    let qualified = if host.ends_with('.') {
        host.to_owned()
    } else {
        format!("{host}.")
    };
    let addresses: Vec<_> = timeout(PROBE, lookup_host((qualified.as_str(), port)))
        .await
        .map_err(|_| offline())?
        .map_err(|_| offline())?
        .collect();
    if addresses.is_empty() {
        return Err(offline());
    }
    Ok(addresses)
}

/// The host must accept a connection on one of its addresses.
async fn reach(host: &str, addresses: &[SocketAddr]) -> Result<(), Error> {
    for address in addresses {
        if let Ok(Ok(_)) = timeout(PROBE, TcpStream::connect(address)).await {
            return Ok(());
        }
    }
    Err(Error::Unreachable {
        host: host.to_owned(),
    })
}

#[cfg(test)]
mod tests {
    use std::net::TcpListener;

    use super::*;

    #[test]
    fn an_unset_clock_fails_before_any_request() {
        assert_eq!(clock(SystemTime::UNIX_EPOCH), Err(Error::ClockNotSet));
        assert_eq!(clock(SystemTime::now()), Ok(()));
    }

    #[test]
    fn the_clock_floor_is_inclusive() {
        let floor = SystemTime::UNIX_EPOCH + EARLIEST_PLAUSIBLE;
        assert_eq!(clock(floor), Ok(()));
        assert_eq!(
            clock(floor - Duration::from_secs(1)),
            Err(Error::ClockNotSet)
        );
    }

    #[tokio::test]
    async fn an_ip_literal_feed_needs_no_name_resolution() {
        // Port 9 on 127.0.0.2 is closed, so this reaches the TCP probe: had it
        // gone through DNS first, a resolver failure would report Offline.
        assert_eq!(
            run("http://127.0.0.2:9/").await,
            Err(Error::Unreachable {
                host: "127.0.0.2".into()
            })
        );
    }

    #[tokio::test]
    async fn a_feed_without_a_host_is_rejected() {
        assert!(matches!(
            run("file:///releases/latest").await,
            Err(Error::InvalidFeed(_))
        ));
    }

    #[tokio::test]
    async fn a_listening_host_passes() {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let feed = format!("http://{}/", listener.local_addr().unwrap());
        assert_eq!(run(&feed).await, Ok(()));
    }

    #[tokio::test]
    async fn a_closed_port_is_unreachable() {
        let port = TcpListener::bind("127.0.0.1:0")
            .unwrap()
            .local_addr()
            .unwrap()
            .port();
        assert_eq!(
            run(&format!("http://127.0.0.1:{port}/")).await,
            Err(Error::Unreachable {
                host: "127.0.0.1".into()
            })
        );
    }

    #[tokio::test]
    async fn an_unresolvable_host_means_offline() {
        // `.invalid` never resolves (RFC 6761), as when there is no internet,
        // even where the resolver's search domain answers every name.
        assert_eq!(
            run("https://update-check.invalid/").await,
            Err(Error::Offline {
                host: "update-check.invalid".into()
            })
        );
    }

    #[tokio::test]
    async fn a_malformed_feed_is_rejected() {
        assert!(matches!(run("not a url").await, Err(Error::InvalidFeed(_))));
    }
}
