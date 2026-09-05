use std::{env, io};

use firmware::runtime::Firmware;
use logger::{LevelFilter, implementations::SystemdLogger, info, register};

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);

fn main() -> io::Result<()> {
    if env::args().nth(1).as_deref() == Some("--version") {
        println!("firmware {}", env!("CARGO_PKG_VERSION"));
        return Ok(());
    }

    register(&LOGGER).map_err(|_| io::Error::other("firmware logger already registered"))?;
    info!("starting firmware {}", env!("CARGO_PKG_VERSION"));

    tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()?
        .block_on(async {
            let mut firmware = Firmware::start()?;
            // Physical adapters will attach to firmware.events().
            firmware.wait().await
        })
}
