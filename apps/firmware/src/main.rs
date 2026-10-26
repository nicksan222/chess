use std::{env, io};

use firmware::{
    board::{GPIO_CHIP, I2C_BUS},
    hardware::{button_panel::ButtonPanel, hall::HallSensors},
    modules::firmware::{NAME, version},
    runtime::Firmware,
    tuning::Tuning,
};
use logger::{LevelFilter, error, implementations::SystemdLogger, info, register};

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);

#[allow(
    clippy::print_stdout,
    reason = "--version prints to stdout by CLI convention; diagnostics go through logger"
)]
fn print_version() {
    println!("{} {}", NAME, version());
}

fn main() -> io::Result<()> {
    if env::args().nth(1).as_deref() == Some("--version") {
        print_version();
        return Ok(());
    }

    register(&LOGGER).map_err(|_| io::Error::other("firmware logger already registered"))?;
    info!("starting {} {}", NAME, version());
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
            let _hall = HallSensors::open(I2C_BUS, &firmware.events(), tuning.hall)?;
            firmware.wait().await
        })
}
