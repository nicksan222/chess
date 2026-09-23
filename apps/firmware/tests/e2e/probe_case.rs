/// Cases understood by the Linux probe executable and its Rust test harness.
#[derive(Clone, Copy, Debug)]
pub enum ProbeCase {
    DisconnectedAndScan,
    OpenNetworkWithoutRadio,
    PersonalNetworkWithoutRadio,
    HotspotWithoutRadio,
    WifiJourney,
}

impl ProbeCase {
    pub const fn as_arg(self) -> &'static str {
        match self {
            Self::DisconnectedAndScan => "disconnected_and_scan",
            Self::OpenNetworkWithoutRadio => "open_network",
            Self::PersonalNetworkWithoutRadio => "personal_network",
            Self::HotspotWithoutRadio => "hotspot",
            Self::WifiJourney => "wifi_journey",
        }
    }

    pub fn from_arg(arg: &str) -> Option<Self> {
        [
            Self::DisconnectedAndScan,
            Self::OpenNetworkWithoutRadio,
            Self::PersonalNetworkWithoutRadio,
            Self::HotspotWithoutRadio,
            Self::WifiJourney,
        ]
        .into_iter()
        .find(|case| case.as_arg() == arg)
    }
}

#[cfg(test)]
mod tests {
    use super::ProbeCase;

    #[test]
    fn every_probe_case_round_trips_through_its_cli_argument() {
        for case in [
            ProbeCase::DisconnectedAndScan,
            ProbeCase::OpenNetworkWithoutRadio,
            ProbeCase::PersonalNetworkWithoutRadio,
            ProbeCase::HotspotWithoutRadio,
            ProbeCase::WifiJourney,
        ] {
            assert_eq!(
                ProbeCase::from_arg(case.as_arg()).unwrap().as_arg(),
                case.as_arg()
            );
        }
    }
}
