//! The `firmware` executable's command line. Startup, logging and signal handling are
//! not asserted here: their intended behaviour is not decided yet.

use std::process::Command;

#[test]
fn version_flag_prints_the_name_and_version_and_exits_successfully() {
    let output = Command::new(env!("CARGO_BIN_EXE_firmware"))
        .arg("--version")
        .output()
        .expect("run the firmware executable");

    assert!(output.status.success(), "{:?}", output.status);
    assert_eq!(
        String::from_utf8(output.stdout).unwrap(),
        format!("firmware {}\n", env!("CARGO_PKG_VERSION"))
    );
    assert!(output.stderr.is_empty(), "{:?}", output.stderr);
}
