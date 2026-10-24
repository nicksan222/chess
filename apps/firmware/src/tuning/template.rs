//! Renders the env file shipped as `/etc/default/firmware`.

use std::fmt::Write;

use super::Tuning;

const HEADER: &str = "\
# Firmware tuning, read by firmware.service when the firmware starts.
#
# Every value is commented out at its built-in default. To override one,
# uncomment it, change the value, then run `systemctl restart firmware`.
# A value that is not a whole number or is outside its range stops the
# firmware; `journalctl -u firmware` names the variable and its range.
";

/// The env file listing every variable at its default, grouped and documented.
/// The image ships exactly this text; a test keeps the two identical.
pub fn env_file() -> String {
    let mut file = String::from(HEADER);
    let mut group = None;
    for variable in Tuning::VARIABLES {
        if group != Some(variable.group) {
            group = Some(variable.group);
            file.push('\n');
            comment(&mut file, "## ", variable.group);
        }
        file.push('\n');
        comment(&mut file, "# ", variable.doc);
        let (min, max, unit) = (variable.min, variable.max, variable.unit);
        let _ = writeln!(file, "# Range: {min} to {max} {unit}.");
        let _ = writeln!(file, "#{}={}", variable.name, variable.default);
    }
    file
}

fn comment(file: &mut String, prefix: &str, doc: &str) {
    for line in doc.lines() {
        let _ = writeln!(file, "{prefix}{}", line.trim());
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SHIPPED_PATH: &str =
        "apps/firmware/yocto/meta-firmware/recipes-firmware/firmware/files/firmware.env";
    const SHIPPED: &str =
        include_str!("../../yocto/meta-firmware/recipes-firmware/firmware/files/firmware.env");

    #[test]
    fn the_shipped_env_file_matches_the_declarations() {
        let expected = env_file();
        assert!(
            SHIPPED == expected,
            "{SHIPPED_PATH} is out of date; replace it with:\n{expected}"
        );
    }

    #[test]
    fn every_variable_appears_commented_at_its_default() {
        let file = env_file();
        for variable in Tuning::VARIABLES {
            let entry = format!("\n#{}={}\n", variable.name, variable.default);
            assert!(file.contains(&entry), "{entry:?} missing from:\n{file}");
        }
        assert!(
            file.lines()
                .all(|line| line.is_empty() || line.starts_with('#'))
        );
    }
}
