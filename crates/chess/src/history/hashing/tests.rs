//! Golden vectors pinning the canonical hash encodings byte for byte.
//!
//! These hashes are committed to stored and exchanged histories, so any change
//! to an encoding is a format break and must fail here.

extern crate std;

use std::{string::String, vec::Vec};

use crate::{
    Board, ChessMove, Color, DrawClaim, DrawReason, FinalState, GameSyncError, HistoryError,
    HistoryEvent, HistoryEventKind, HistoryHash, InvalidState, MoveError, PieceKind, Ply, Square,
};

use super::{calculate_board_anchor, calculate_hash};

fn ply(value: u64) -> Ply {
    Ply::new(value).expect("nonzero ply")
}

fn hash(byte: u8) -> HistoryHash {
    HistoryHash::from_bytes([byte; HistoryHash::BYTE_COUNT])
}

fn promotion() -> ChessMove {
    ChessMove::promotion(Square::E7, Square::E8, PieceKind::Knight).expect("valid promotion")
}

fn events() -> Vec<HistoryEvent> {
    let plain = ChessMove::new(Square::E2, Square::E4);
    let move_errors = [
        MoveError::GameOver {
            final_state: FinalState::Stalemate,
        },
        MoveError::PendingInvalid,
        MoveError::NoPiece { square: Square::C3 },
        MoveError::WrongSide {
            expected: Color::White,
            actual: Color::Black,
        },
        MoveError::IllegalDestination {
            from: Square::A1,
            to: Square::H8,
        },
        MoveError::UnexpectedPromotion,
        MoveError::InvalidPromotion,
        MoveError::NonCanonicalPromotion,
        MoveError::StalePiece,
    ];
    let history_errors = [
        HistoryError::Ply {
            expected: ply(2),
            actual: ply(5),
        },
        HistoryError::PreviousHash {
            ply: ply(3),
            expected: hash(1),
            actual: hash(2),
        },
        HistoryError::Hash {
            ply: ply(4),
            expected: hash(3),
            actual: hash(4),
        },
        HistoryError::InvalidTransition {
            current: Some(HistoryEventKind::Final),
            incoming: HistoryEventKind::Move,
        },
        HistoryError::InvalidTransition {
            current: None,
            incoming: HistoryEventKind::Invalid,
        },
        HistoryError::NothingToResolve {
            current: Some(HistoryEventKind::Move),
        },
        HistoryError::NothingToResolve { current: None },
        HistoryError::Tip {
            expected: hash(5),
            actual: hash(6),
        },
    ];
    let finals = [
        FinalState::Checkmate {
            winner: Color::White,
        },
        FinalState::Checkmate {
            winner: Color::Black,
        },
        FinalState::Stalemate,
        FinalState::Draw {
            reason: DrawReason::Claimed(DrawClaim::ThreefoldRepetition),
        },
        FinalState::Draw {
            reason: DrawReason::Claimed(DrawClaim::FiftyMoveRule),
        },
        FinalState::Draw {
            reason: DrawReason::InsufficientMaterial,
        },
        FinalState::Draw {
            reason: DrawReason::FivefoldRepetition,
        },
        FinalState::Draw {
            reason: DrawReason::SeventyFiveMoveRule,
        },
        FinalState::DrawAfter {
            claim: DrawClaim::ThreefoldRepetition,
            chess_move: plain,
        },
        FinalState::DrawAfter {
            claim: DrawClaim::FiftyMoveRule,
            chess_move: promotion(),
        },
    ];

    let mut events = Vec::new();
    events.push(HistoryEvent::Move(plain));
    events.push(HistoryEvent::Move(promotion()));
    for error in move_errors {
        events.push(HistoryEvent::Invalid(InvalidState::Move(error)));
        events.push(HistoryEvent::Invalid(InvalidState::Synchronization(
            GameSyncError::Move(error),
        )));
    }
    for error in history_errors {
        events.push(HistoryEvent::Invalid(InvalidState::Synchronization(
            GameSyncError::History(error),
        )));
    }
    events.push(HistoryEvent::Invalid(InvalidState::DrawClaim {
        claim: DrawClaim::ThreefoldRepetition,
    }));
    events.push(HistoryEvent::Invalid(InvalidState::DrawClaim {
        claim: DrawClaim::FiftyMoveRule,
    }));
    events.push(HistoryEvent::Invalid(InvalidState::PendingInvalid));
    for final_state in finals {
        events.push(HistoryEvent::Final(final_state));
    }
    events
}

#[test]
fn event_hashes_match_golden_vectors() {
    let actual: Vec<String> = events()
        .into_iter()
        .enumerate()
        .map(|(index, event)| {
            std::format!(
                "{}",
                calculate_hash(
                    hash(u8::try_from(index).unwrap()),
                    ply(index as u64 + 1),
                    event
                )
            )
        })
        .collect();
    assert_eq!(actual.len(), EVENT_GOLDEN.len(), "{actual:#?}");
    for (index, (actual, expected)) in actual.iter().zip(EVENT_GOLDEN).enumerate() {
        assert_eq!(actual, expected, "event vector {index}");
    }
}

#[test]
fn board_anchors_match_golden_vectors() {
    let mut moved = Board::INITIAL;
    moved
        .make_move(ChessMove::new(Square::E2, Square::E4))
        .unwrap();
    let actual = [
        std::format!("{}", calculate_board_anchor(&Board::INITIAL)),
        std::format!("{}", calculate_board_anchor(&moved)),
    ];
    assert_eq!(actual, ANCHOR_GOLDEN);
}

const ANCHOR_GOLDEN: [&str; 2] = [
    "b6acaf814cd8504693dda45177590750d3648479d0da7ef53615c8dbbc10565f",
    "381c2032ed9a3dd099ed52b407f43b353061a0358f9a371eb23498d116fd1d8d",
];

const EVENT_GOLDEN: [&str; 41] = [
    "59c8f0c8e610d5d3f71e08c7d6f8749bb8759167e8208c8c144f36650a44d5e6",
    "3d122b85baf6a60057d302381f291b78c18538b79ba046d7f5f571a6ea589fba",
    "28b43dc223046be94c711b61fc123e39b79224b9bfe44d518517cbbbbf7231a3",
    "008fbcbe5392fd1a9122a2f0855f9ebaec7bb12410403bdce513834f96bffc6e",
    "856aa2b50f1203a53f27cb3f03c3eac3eb70f09ae596d907e3aaa24ee606d654",
    "248dbcc67fbb999cd2bac142a0f01f9b5d28310466b59c52539a4d1e96198236",
    "d4cd5f1e3e57edd2cd528cd15bf8638e7547883b87de73f9d9d64197937fa02d",
    "4789ae3ccaa8c4a5ec4f809d8d4a1b0725fe29e65505546dfd85ce3fd418eb8b",
    "ac5f4660489fa5cc8216c3489ad3b73983ea6eb26e4caa27442a761ef19f2953",
    "faa0fd5487ff835a94adb80785d36feb08d28597e4474ccd8759b5bfd6df7867",
    "476b045c1af33ab32d6361e72a484fb152e236c66869f983e7a731712e952947",
    "2fa8790e569a2e459f10f3ae9ad0c1587ff0581ed7efb6dba99432f50a3af401",
    "71572c941e07556e119b3462a743a8bf198420321ee5aa75055e67f2d489236e",
    "af2d8963521b333225e9400e7e221b1d0d2421448d8f43ea89156af4ed2be3fb",
    "04f1ca6ee8a750e32c12cbf88bb458f6ffcc8e85c348f2abe78630073af0f370",
    "00a185ad9d1669b67e3b5636b1a1db91c91686a9530ad020f9467c4e2d3e4851",
    "ada7786f83f1e72af03b6d7d73b748cbd061702a97df9abc354aee763725fa7b",
    "ece5d41e16e1c8b8240a77bc454a6a6cb68ad53455fdfa72bdb367cae80d6ddc",
    "d6ca93ee860e0b4d21a94eeb37df2b1edf448dd78df95ed08b2a23d39df5c4b0",
    "624b61530d04879219ed36e5278a86b9fe1f98af5b8bc30952dcf8bc24f03f65",
    "e60f3d1560cc8ced50f0424be2e187c0e71e23363662444b2fea0f612bc2cacf",
    "99d6955454d77629a285c9100d506ac3fe909ec2793794429257fadf54011c3c",
    "a7828d199614d91bb253a51eed93db83884ce64fee1b40ad46f3d972375ac9e6",
    "9ed973242ecf386ff0c2928135de42e70dd224af40af582d46dbe57ace077036",
    "4b0d0ef29a18eba22c934472796553f92e0bc6524ebbe6b104a8ec026db80b81",
    "f5371e8c928bfa3697d1b05d314049b002e482e24921d61817bacbe510ff8bf6",
    "e952ef53f2a6b89897f27c39d7bd2c0abb67902553ea724b54affdac0a2f53f0",
    "e8b35ba1660e20bfafb671a9c174c0cb5e70d1b19ff5b2ea8b6ca4cfd6a61888",
    "a2c2f61a80a157b8bd2abfd7ef5296d8163ce9a104b41418479df03d0c3ca491",
    "3bfa3148af41d617b12ff5556d3078d878c5ba5159e0d00b19c3be345daac667",
    "d635ac85145c96ea2ce06566a4c54275819ac6d83122dc3fd6d3429e1fe886f6",
    "1d7e5e412928c925a71e86d54722751a640281398da0df5e7abf645b3ece6bb0",
    "6b42aadac49ca725c7becc19a9506ae0525de762ba56597eda807503c28e8cc6",
    "b18c4ca0089dea9ccc9d787d48e97fbff5cf093d3e227d41fd77b299f404c82f",
    "87532c427e25ed5b4c374c7d861fbd92d39bb78b72b68be11f302b36d676d32f",
    "e9576a8d20a11e62664d8bf22476a6f0801d17b734684f4b8f2cc833fb673d3c",
    "4e7f33a922c9a28248c20b04cbc449096eaa505b1c53e1984f06632df72a99e3",
    "d3a128e33695817b64103700fe4cd5d4b5d8e304c7e69575ffc4a4ff286a6c6e",
    "b918c3e943333c434d9009093b498f201a2187996046c097cb8409b4e888a14d",
    "bf1f0bff0644bdbd64939bb07511b17d2a28dced779889aa85858122a2d9416a",
    "5f49e06a58368270240e45af23304272148a655c8cc6a98a87942ad26600fd8e",
];
