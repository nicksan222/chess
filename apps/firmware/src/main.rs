use std::{env, thread};

use logger::{LevelFilter, implementations::SystemdLogger, info};

fn main() {
    if env::args().nth(1).as_deref() == Some("--version") {
        println!("firmware {}", env!("CARGO_PKG_VERSION"));
        return;
    }

    let logger = SystemdLogger::new(LevelFilter::Info);
    info!(logger, "starting firmware {}", env!("CARGO_PKG_VERSION"));

    // Hardware and provisioning workers will be added behind this supervised
    // process. SIGTERM retains its default behavior, allowing systemd to stop
    // the firmware without application-specific signal handling.
    loop {
        thread::park();
    }
}
