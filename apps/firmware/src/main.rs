use std::{env, thread};

use logger::{LevelFilter, implementations::SystemdLogger, info, register};

pub mod generated_pins;

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);

fn main() {
    if env::args().nth(1).as_deref() == Some("--version") {
        println!("firmware {}", env!("CARGO_PKG_VERSION"));
        return;
    }

    register(&LOGGER).expect("the firmware registers its logger only once");
    info!("starting firmware {}", env!("CARGO_PKG_VERSION"));

    // Hardware and provisioning workers will be added behind this supervised
    // process. SIGTERM retains its default behavior, allowing systemd to stop
    // the firmware without application-specific signal handling.
    loop {
        thread::park();
    }
}
