//! An in-memory Wi-Fi stack for unit tests of [`Connectivity`](super::Connectivity).
//!
//! It models only what the earlier Linux VM runs (real NetworkManager, hostapd and
//! `mac80211_hwsim`, since removed) showed NetworkManager to do:
//! - an active access point's SSID is what `current_ssid` reports (a running hotspot
//!   looked like `Connected("ChessSetup")`);
//! - there is one radio, so activating an access point or joining a network replaces
//!   whatever was active;
//! - `forget` removes the profile and deactivates it, and forgetting an unknown
//!   profile succeeds (starting a hotspot forgets its own name first);
//! - joining with a wrong passphrase fails with `AuthFailed`, and joining a network
//!   that is not visible fails with `NotFound`.
//!
//! Cloning shares the same stack, so two [`Connectivity`](super::Connectivity)
//! values can stand for two runs of the firmware on one board.

use std::sync::{Arc, Mutex, MutexGuard};

use super::{
    Credentials, Error, Hotspot, Ssid,
    backend::{VisibleNetwork, WifiBackend},
};

/// One backend operation, in the order the product code issued it.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Call {
    CurrentSsid,
    Scan,
    Forget(String),
    StartAccessPoint(Hotspot),
    Join(Ssid, Credentials),
}

/// The operations a scripted failure can target.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Operation {
    Scan,
    Forget,
    StartAccessPoint,
    Join,
}

/// A failure the fake can be told to report once.
#[derive(Clone, Copy, Debug)]
pub enum Failure {
    AuthFailed,
    NotFound,
    Timeout,
}

impl Failure {
    fn error(self) -> Error {
        match self {
            Self::AuthFailed => Error::NetworkManager(Box::new(nmrs::ConnectionError::AuthFailed)),
            Self::NotFound => Error::NetworkManager(Box::new(nmrs::ConnectionError::NotFound)),
            Self::Timeout => Error::NetworkManager(Box::new(nmrs::ConnectionError::Timeout)),
        }
    }
}

/// How a visible network authenticates.
#[derive(Clone, Debug)]
enum Auth {
    Open,
    Wpa(String),
    Enterprise,
}

/// A network in range of the board.
#[derive(Clone, Debug)]
pub struct Network {
    ssid: String,
    strength: Option<u8>,
    auth: Auth,
}

impl Network {
    pub fn open(ssid: &str, strength: u8) -> Self {
        Self::new(ssid, Some(strength), Auth::Open)
    }

    pub fn wpa(ssid: &str, strength: u8, passphrase: &str) -> Self {
        Self::new(ssid, Some(strength), Auth::Wpa(passphrase.to_owned()))
    }

    pub fn enterprise(ssid: &str, strength: u8) -> Self {
        Self::new(ssid, Some(strength), Auth::Enterprise)
    }

    /// The stack does not report a signal strength for this network.
    pub fn without_strength(mut self) -> Self {
        self.strength = None;
        self
    }

    fn new(ssid: &str, strength: Option<u8>, auth: Auth) -> Self {
        Self {
            ssid: ssid.to_owned(),
            strength,
            auth,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
enum Active {
    Client(String),
    AccessPoint(String),
}

#[derive(Default)]
struct State {
    visible: Vec<Network>,
    profiles: Vec<String>,
    active: Option<Active>,
    calls: Vec<Call>,
    failures: Vec<(Operation, Failure)>,
}

impl State {
    fn fail_if_scripted(&mut self, operation: Operation) -> Result<(), Error> {
        match self
            .failures
            .iter()
            .position(|(next, _)| *next == operation)
        {
            Some(index) => Err(self.failures.remove(index).1.error()),
            None => Ok(()),
        }
    }

    fn save_profile(&mut self, ssid: &str) {
        if !self.profiles.iter().any(|known| known == ssid) {
            self.profiles.push(ssid.to_owned());
        }
    }
}

/// The fake Wi-Fi stack. Clones share one state.
#[derive(Clone, Default)]
pub struct FakeWifi {
    state: Arc<Mutex<State>>,
}

impl FakeWifi {
    fn state(&self) -> MutexGuard<'_, State> {
        self.state.lock().unwrap()
    }

    pub fn with_network(self, network: Network) -> Self {
        self.state().visible.push(network);
        self
    }

    /// Makes `ssid` the active client connection, as reported (even if invalid).
    pub fn with_active_client(self, ssid: &str) -> Self {
        self.state().active = Some(Active::Client(ssid.to_owned()));
        self
    }

    /// The next call of `operation` fails with `failure`; later calls succeed again.
    pub fn fail_next(&self, operation: Operation, failure: Failure) {
        self.state().failures.push((operation, failure));
    }

    /// Every backend call so far, in order.
    pub fn calls(&self) -> Vec<Call> {
        self.state().calls.clone()
    }

    pub fn clear_calls(&self) {
        self.state().calls.clear();
    }

    /// The SSID of the access point currently running, if any.
    pub fn access_point(&self) -> Option<String> {
        match &self.state().active {
            Some(Active::AccessPoint(ssid)) => Some(ssid.clone()),
            _ => None,
        }
    }

    /// Saved profiles, in the order they were created.
    pub fn profiles(&self) -> Vec<String> {
        self.state().profiles.clone()
    }
}

impl WifiBackend for FakeWifi {
    async fn current_ssid(&self) -> Option<String> {
        let mut state = self.state();
        state.calls.push(Call::CurrentSsid);
        match &state.active {
            Some(Active::Client(ssid) | Active::AccessPoint(ssid)) => Some(ssid.clone()),
            None => None,
        }
    }

    async fn scan(&self) -> Result<Vec<VisibleNetwork>, Error> {
        let mut state = self.state();
        state.calls.push(Call::Scan);
        state.fail_if_scripted(Operation::Scan)?;
        let active = match &state.active {
            Some(Active::Client(ssid)) => Some(ssid.clone()),
            _ => None,
        };
        Ok(state
            .visible
            .iter()
            .map(|network| VisibleNetwork {
                ssid: network.ssid.clone(),
                strength: network.strength,
                // Enterprise networks advertise authentication too.
                secured: !matches!(network.auth, Auth::Open),
                enterprise: matches!(network.auth, Auth::Enterprise),
                active: active.as_deref() == Some(network.ssid.as_str()),
                known: state.profiles.contains(&network.ssid),
            })
            .collect())
    }

    async fn forget(&self, ssid: &str) -> Result<(), Error> {
        let mut state = self.state();
        state.calls.push(Call::Forget(ssid.to_owned()));
        state.fail_if_scripted(Operation::Forget)?;
        state.profiles.retain(|known| known != ssid);
        if matches!(&state.active,
            Some(Active::Client(active) | Active::AccessPoint(active)) if active == ssid)
        {
            state.active = None;
        }
        Ok(())
    }

    async fn start_access_point(&self, hotspot: &Hotspot) -> Result<(), Error> {
        let mut state = self.state();
        state.calls.push(Call::StartAccessPoint(hotspot.clone()));
        state.fail_if_scripted(Operation::StartAccessPoint)?;
        let ssid = hotspot.ssid.as_str().to_owned();
        state.save_profile(&ssid);
        state.active = Some(Active::AccessPoint(ssid)); // One radio: replaces the client link.
        Ok(())
    }

    async fn join(&self, ssid: &Ssid, credentials: &Credentials) -> Result<(), Error> {
        let mut state = self.state();
        state
            .calls
            .push(Call::Join(ssid.clone(), credentials.clone()));
        state.fail_if_scripted(Operation::Join)?;
        let Some(network) = state
            .visible
            .iter()
            .find(|network| network.ssid == ssid.as_str())
            .cloned()
        else {
            return Err(Failure::NotFound.error());
        };
        match (&network.auth, credentials) {
            (Auth::Open, Credentials::Open) => {}
            (Auth::Wpa(expected), Credentials::Personal(given)) if given.expose() == expected => {}
            _ => return Err(Failure::AuthFailed.error()),
        }
        state.save_profile(ssid.as_str());
        state.active = Some(Active::Client(ssid.as_str().to_owned()));
        Ok(())
    }
}
