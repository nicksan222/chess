use std::{env, thread};

fn main() {
    if env::args().nth(1).as_deref() == Some("--version") {
        println!("firmware {}", env!("CARGO_PKG_VERSION"));
        return;
    }

    println!("starting firmware {}", env!("CARGO_PKG_VERSION"));

    // Hardware and provisioning workers will be added behind this supervised
    // process. SIGTERM retains its default behavior, allowing systemd to stop
    // the firmware without application-specific signal handling.
    loop {
        thread::park();
    }
}
