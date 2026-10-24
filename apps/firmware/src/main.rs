use std::{env, io};

use firmware::{
    board::GPIO_CHIP, hardware::button_panel::ButtonPanel, runtime::Firmware, tuning::Tuning,
    updater::installed,
};
use logger::{LevelFilter, error, implementations::SystemdLogger, info, register};

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);

fn main() -> io::Result<()> {
    if env::args().nth(1).as_deref() == Some("--version") {
        println!("{} {}", installed::NAME, installed::version());
        return Ok(());
    }

    register(&LOGGER).map_err(|_| io::Error::other("firmware logger already registered"))?;
    info!("starting {} {}", installed::NAME, installed::version());
    let tuning = Tuning::from_env().map_err(|cause| {
        error!("{cause}; fix it in /etc/default/firmware. Firmware startup cannot continue");
        io::Error::new(io::ErrorKind::InvalidInput, cause)
    })?;

    tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()?
        .block_on(async {
            let mut firmware = Firmware::start()?;
            let _buttons = ButtonPanel::open(GPIO_CHIP, &firmware.events(), tuning.buttons)?;
            firmware.wait().await
        })
}
