pub(crate) mod backend_contract;

/// Instantiates the complete behavioral contract for one concrete backend.
///
/// Every implementation module invokes this macro with a fresh-store factory;
/// adding a backend without the invocation leaves its e2e module visibly empty.
macro_rules! backend_contract_tests {
    ($factory:ident) => {
        mod shared_backend_contract {
            use super::$factory;
            use crate::common::backend_contract;

            #[test]
            fn missing_values_are_unambiguous() {
                backend_contract::missing_values_are_unambiguous(&mut $factory());
            }

            #[test]
            fn binary_values_round_trip_and_overwrite() {
                backend_contract::binary_values_round_trip_and_overwrite(&mut $factory());
            }

            #[test]
            fn undersized_buffers_are_never_partially_written() {
                backend_contract::undersized_buffers_are_never_partially_written(&mut $factory());
            }

            #[test]
            fn empty_keys_and_values_remain_distinct_from_missing() {
                backend_contract::empty_keys_and_values_remain_distinct_from_missing(
                    &mut $factory(),
                );
            }

            #[test]
            fn removal_and_flush_are_consistent() {
                backend_contract::removal_and_flush_are_consistent(&mut $factory());
            }
        }
    };
}

pub(crate) use backend_contract_tests;
