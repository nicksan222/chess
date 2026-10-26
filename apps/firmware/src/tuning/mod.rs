//! Values worth adjusting on a prototype without rebuilding the firmware.
//!
//! Each value has a built-in default and a `FIRMWARE_*` environment variable.
//! systemd reads overrides from `/etc/default/firmware`, which the image ships
//! with every variable commented out at its default (see [`env_file`]).
//! Adding a value is one line in the `tuning!` declaration below.

#[macro_use]
mod macros;
mod error;
mod template;

use logger::{info, warn};

pub use error::TuningError;
use error::parse;
pub use template::env_file;

tuning! {
    /// Hall-sensor scanning; see `docs/host.md#reading-the-board`.
    hall: HallTuning {
        /// Target period of one complete eight-bank scan.
        scan_interval: 25 ms in 5..=1000 from "FIRMWARE_HALL_SCAN_INTERVAL_MS";
        /// Consecutive complete scans that must agree before a piece change is
        /// reported. The sensors themselves only sample every 27-75 ms.
        stable_scans: 2 scans in 1..=20 from "FIRMWARE_HALL_STABLE_SCANS";
    }
    /// Control-panel buttons.
    buttons: ButtonTuning {
        /// How often each button line is sampled.
        poll_interval: 5 ms in 1..=100 from "FIRMWARE_BUTTON_POLL_INTERVAL_MS";
        /// How long a new level must hold before it counts as a press or release.
        debounce: 20 ms in 1..=500 from "FIRMWARE_BUTTON_DEBOUNCE_MS";
    }
}

/// Every tuning variable shares this prefix; other names are not ours.
const PREFIX: &str = "FIRMWARE_";

/// One tunable value as it is written in the environment.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Variable {
    /// The environment variable, such as `FIRMWARE_BUTTON_DEBOUNCE_MS`.
    pub name: &'static str,
    /// Documentation of the group the variable belongs to.
    pub group: &'static str,
    /// What the variable controls.
    pub doc: &'static str,
    /// The built-in value, in `unit`.
    pub default: u64,
    /// The smallest accepted value, in `unit`.
    pub min: u64,
    /// The largest accepted value, in `unit`.
    pub max: u64,
    /// The unit the value is written in, such as `ms`.
    pub unit: &'static str,
}

/// What reading one environment variable did.
#[derive(Debug, Eq, PartialEq)]
enum Applied {
    Overridden,
    Unknown,
    Unrelated,
}

impl Tuning {
    /// Reads overrides from the process environment.
    ///
    /// # Errors
    ///
    /// Returns [`TuningError`] for a `FIRMWARE_*` value that is not a number or is
    /// out of range.
    #[allow(
        clippy::disallowed_methods,
        reason = "tuning is the only reader of the process environment"
    )]
    pub fn from_env() -> Result<Self, TuningError> {
        Self::from_vars(std::env::vars_os().map(|(name, value)| {
            (
                name.to_string_lossy().into_owned(),
                value.to_string_lossy().into_owned(),
            )
        }))
    }

    /// Starts from [`Tuning::DEFAULT`] and applies every `FIRMWARE_*`
    /// variable, logging each override. An unknown `FIRMWARE_*` name, most
    /// likely a typo, is logged as a warning and ignored; a value that is not
    /// a number or is out of range is an error.
    ///
    /// # Errors
    ///
    /// Returns [`TuningError`] for a value that is not a number or is out of
    /// range.
    pub fn from_vars(
        vars: impl IntoIterator<Item = (String, String)>,
    ) -> Result<Self, TuningError> {
        let mut tuning = Self::DEFAULT;
        for (name, value) in vars {
            match tuning.apply(&name, &value)? {
                Applied::Overridden => info!("tuning override: {name}={value}"),
                Applied::Unknown => warn!("ignoring unknown tuning variable {name}"),
                Applied::Unrelated => {}
            }
        }
        Ok(tuning)
    }

    fn apply(&mut self, name: &str, value: &str) -> Result<Applied, TuningError> {
        if !name.starts_with(PREFIX) {
            return Ok(Applied::Unrelated);
        }
        Ok(if self.set(name, value)? {
            Applied::Overridden
        } else {
            Applied::Unknown
        })
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use super::*;

    fn vars(pairs: &[(&str, &str)]) -> Vec<(String, String)> {
        pairs
            .iter()
            .map(|&(name, value)| (name.to_owned(), value.to_owned()))
            .collect()
    }

    #[test]
    fn button_defaults_match_the_previous_constants() {
        assert_eq!(Tuning::DEFAULT, Tuning::default());
        assert_eq!(
            Tuning::DEFAULT.buttons,
            ButtonTuning {
                poll_interval: Duration::from_millis(5),
                debounce: Duration::from_millis(20),
            }
        );
    }

    #[test]
    fn defaults_lie_within_their_ranges_and_both_bounds_fit_the_field() {
        for variable in Tuning::VARIABLES {
            assert!(variable.name.starts_with(PREFIX), "{variable:?}");
            assert!(variable.min <= variable.max, "{variable:?}");
            assert!(
                (variable.min..=variable.max).contains(&variable.default),
                "{variable:?}"
            );
            for bound in [variable.min, variable.max, variable.default] {
                let mut tuning = Tuning::DEFAULT;
                assert_eq!(tuning.set(variable.name, &bound.to_string()), Ok(true));
            }
        }
    }

    #[test]
    fn variable_names_are_unique() {
        let mut names: Vec<_> = Tuning::VARIABLES.iter().map(|v| v.name).collect();
        names.sort_unstable();
        names.dedup();
        assert_eq!(names.len(), Tuning::VARIABLES.len());
    }

    #[test]
    fn no_variables_gives_the_defaults() {
        assert_eq!(Tuning::from_vars(Vec::new()), Ok(Tuning::DEFAULT));
    }

    #[test]
    fn overrides_replace_only_their_own_value() {
        let tuning = Tuning::from_vars(vars(&[
            ("PATH", "/usr/bin"),
            ("FIRMWARE_BUTTON_DEBOUNCE_MS", " 45 "),
        ]))
        .unwrap();
        assert_eq!(tuning.buttons.debounce, Duration::from_millis(45));
        assert_eq!(
            tuning.buttons.poll_interval,
            ButtonTuning::DEFAULT.poll_interval
        );
    }

    #[test]
    fn a_value_that_is_not_a_number_is_rejected() {
        let error =
            Tuning::from_vars(vars(&[("FIRMWARE_BUTTON_DEBOUNCE_MS", "20ms")])).unwrap_err();
        assert_eq!(
            error,
            TuningError::NotANumber {
                name: "FIRMWARE_BUTTON_DEBOUNCE_MS",
                value: "20ms".to_owned(),
                range: 1..=500,
                unit: "ms",
            }
        );
        assert_eq!(
            error.to_string(),
            r#"FIRMWARE_BUTTON_DEBOUNCE_MS="20ms" is not a whole number; expected 1 to 500 ms"#
        );
    }

    #[test]
    fn a_value_out_of_range_is_rejected() {
        for value in ["0", "101", "-5"] {
            let error = Tuning::from_vars(vars(&[("FIRMWARE_BUTTON_POLL_INTERVAL_MS", value)]))
                .unwrap_err();
            assert!(
                error
                    .to_string()
                    .starts_with(&format!("FIRMWARE_BUTTON_POLL_INTERVAL_MS={value:?} ")),
                "{error}"
            );
            assert!(
                error.to_string().ends_with("expected 1 to 100 ms"),
                "{error}"
            );
        }
        assert_eq!(
            Tuning::from_vars(vars(&[("FIRMWARE_BUTTON_POLL_INTERVAL_MS", "101")]))
                .unwrap_err()
                .to_string(),
            r#"FIRMWARE_BUTTON_POLL_INTERVAL_MS="101" is out of range; expected 1 to 100 ms"#
        );
    }

    #[test]
    fn unknown_firmware_variables_are_reported_and_others_ignored() {
        let mut tuning = Tuning::DEFAULT;
        assert_eq!(
            tuning.apply("FIRMWARE_BUTTON_DEBOUNCE", "30"),
            Ok(Applied::Unknown)
        );
        assert_eq!(tuning.apply("HOME", "/root"), Ok(Applied::Unrelated));
        assert_eq!(
            tuning.apply("FIRMWARE_BUTTON_DEBOUNCE_MS", "30"),
            Ok(Applied::Overridden)
        );
        // A typo is a warning, not a startup failure.
        assert_eq!(
            Tuning::from_vars(vars(&[("FIRMWARE_BUTTON_DEBOUNCE", "abc")])),
            Ok(Tuning::DEFAULT)
        );
    }

    /// The full `u8` range of the `scans` unit, beyond any range the firmware declares.
    mod scans {
        #![allow(
            unreachable_pub,
            reason = "the macro declares pub items inside a test-only module"
        )]

        use super::super::{TuningError, Variable, parse};

        tuning! {
            /// A test group.
            sensors: SensorTuning {
                /// Consecutive agreeing scans before a change counts.
                agree: 3 scans in 1..=255 from "FIRMWARE_TEST_AGREE_SCANS";
            }
        }

        #[test]
        fn scans_are_u8_counts() {
            let mut tuning = Tuning::DEFAULT;
            assert_eq!(tuning.sensors.agree, 3_u8);
            assert_eq!(tuning.set("FIRMWARE_TEST_AGREE_SCANS", "255"), Ok(true));
            assert_eq!(tuning.sensors.agree, u8::MAX);
            assert!(matches!(
                tuning.set("FIRMWARE_TEST_AGREE_SCANS", "256"),
                Err(TuningError::OutOfRange { .. })
            ));
            assert_eq!(Tuning::VARIABLES[0].unit, "scans");
            assert_eq!(Tuning::VARIABLES[0].group, SensorTuning::DOC);
        }
    }
}
