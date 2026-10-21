use std::{env, io};

use firmware::{hardware::button_panel::ButtonPanel, runtime::Firmware, updater::installed};
use logger::{LevelFilter, implementations::SystemdLogger, info, register};

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);

fn main() -> io::Result<()> {
    if env::args().nth(1).as_deref() == Some("--version") {
        println!("{} {}", installed::NAME, installed::version());
        return Ok(());
    }

    register(&LOGGER).map_err(|_| io::Error::other("firmware logger already registered"))?;
    info!("starting {} {}", installed::NAME, installed::version());

    tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()?
        .block_on(async {
            let mut firmware = Firmware::start()?;
            let _buttons = ButtonPanel::open("/dev/gpiochip0", &firmware.events())?;
            firmware.wait().await
        })
}
