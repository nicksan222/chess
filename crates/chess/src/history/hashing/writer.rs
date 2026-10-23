//! Typed byte sink shared by every canonical hash encoding.

use sha2::{Digest, Sha256};

use crate::{Color, Square};

use super::super::{HistoryHash, Ply};

/// Declares a `#[repr(u8)]` tag enum whose discriminants are the wire bytes.
///
/// Discriminants count up from zero in declaration order, so reordering or
/// inserting variants changes stored hashes. The golden vectors in the
/// hashing tests guard against that.
macro_rules! tag_enum {
    ($(#[$meta:meta])* $vis:vis $name:ident { $($variant:ident),+ $(,)? }) => {
        $(#[$meta])*
        #[derive(Clone, Copy)]
        #[repr(u8)]
        $vis enum $name {
            $($variant),+
        }

        impl From<$name> for u8 {
            fn from(tag: $name) -> Self {
                tag as Self
            }
        }
    };
}

/// A SHA-256 digest fed through the canonical field encodings.
pub(super) struct HashWriter(Sha256);

impl HashWriter {
    /// Starts a digest under a domain-separation prefix.
    pub(super) fn new(domain: &[u8]) -> Self {
        let mut digest = Sha256::new();
        digest.update(domain);
        Self(digest)
    }

    /// Writes a variant tag byte.
    pub(super) fn tag(&mut self, tag: impl Into<u8>) -> &mut Self {
        self.byte(tag.into())
    }

    /// Writes one raw byte.
    pub(super) fn byte(&mut self, byte: u8) -> &mut Self {
        self.0.update([byte]);
        self
    }

    /// Writes raw bytes.
    pub(super) fn bytes(&mut self, bytes: &[u8]) -> &mut Self {
        self.0.update(bytes);
        self
    }

    /// Writes a ply as eight big-endian bytes.
    pub(super) fn ply(&mut self, ply: Ply) -> &mut Self {
        self.bytes(&ply.value().to_be_bytes())
    }

    /// Writes a hash as its 32 raw bytes.
    pub(super) fn hash(&mut self, hash: &HistoryHash) -> &mut Self {
        self.bytes(hash.as_bytes())
    }

    /// Writes a color as `0` for White and `1` for Black.
    pub(super) fn color(&mut self, color: Color) -> &mut Self {
        self.byte(color_code(color))
    }

    /// Writes a square as its board index.
    pub(super) fn square(&mut self, square: Square) -> &mut Self {
        self.byte(square.index().value())
    }

    /// Completes the digest.
    pub(super) fn finish(self) -> HistoryHash {
        HistoryHash::from_bytes(self.0.finalize().into())
    }
}

/// Returns the stable hash code for a color.
///
/// The code keeps mover, winner, and piece-color encodings stable inside
/// board anchors and cumulative event hashes.
pub(super) const fn color_code(color: Color) -> u8 {
    match color {
        Color::White => 0,
        Color::Black => 1,
    }
}
