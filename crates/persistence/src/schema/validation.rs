/// Validates the keys emitted by `persistence_schema!` during const evaluation.
#[doc(hidden)]
pub const fn validate_keys(keys: &[&[u8]]) {
    let mut left = 0;
    while left < keys.len() {
        assert!(
            !keys[left].is_empty(),
            "persistence field keys must not be empty"
        );

        let mut right = left + 1;
        while right < keys.len() {
            assert!(
                !equal(keys[left], keys[right]),
                "persistence field keys must be unique"
            );
            right += 1;
        }
        left += 1;
    }
}

const fn equal(left: &[u8], right: &[u8]) -> bool {
    if left.len() != right.len() {
        return false;
    }

    let mut index = 0;
    while index < left.len() {
        if left[index] != right[index] {
            return false;
        }
        index += 1;
    }
    true
}

#[cfg(test)]
mod tests {
    use super::validate_keys;

    #[test]
    fn distinct_nonempty_keys_are_valid() {
        validate_keys(&[b"one", b"two", b"three"]);
    }

    #[test]
    #[should_panic(expected = "persistence field keys must not be empty")]
    fn empty_keys_are_rejected() {
        validate_keys(&[b""]);
    }

    #[test]
    #[should_panic(expected = "persistence field keys must be unique")]
    fn duplicate_keys_are_rejected() {
        validate_keys(&[b"same", b"same"]);
    }
}
