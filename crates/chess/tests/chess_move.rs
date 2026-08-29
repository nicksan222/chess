use std::collections::HashSet;

use chess::{ChessMove, InvalidPromotion, PieceKind, Square};

fn assert_value_traits<T>()
where
    T: Copy + Clone + std::fmt::Debug + Eq + Ord + std::hash::Hash + Send + Sync + 'static,
{
}

#[test]
fn moves_own_their_origin_destination_and_optional_promotion() {
    let ordinary = ChessMove::new(Square::E2, Square::E4);
    let promotion = ChessMove::promotion(Square::A7, Square::A8, PieceKind::Knight).unwrap();

    assert_eq!(ordinary.from(), Square::E2);
    assert_eq!(ordinary.to(), Square::E4);
    assert_eq!(ordinary.promotion_kind(), None);
    assert_eq!(ordinary.to_string(), "e2e4");

    assert_eq!(promotion.from(), Square::A7);
    assert_eq!(promotion.to(), Square::A8);
    assert_eq!(promotion.promotion_kind(), Some(PieceKind::Knight));
    assert_eq!(promotion.to_string(), "a7a8n");
}

#[test]
fn every_origin_and_destination_pair_is_a_distinct_move_value() {
    let moves = Square::all()
        .flat_map(|from| Square::all().map(move |to| ChessMove::new(from, to)))
        .collect::<Vec<_>>();
    let unique = moves.iter().copied().collect::<HashSet<_>>();

    assert_eq!(moves.len(), Square::COUNT * Square::COUNT);
    assert_eq!(unique.len(), moves.len());
    for chess_move in moves {
        let notation = chess_move.to_string();
        assert_eq!(notation.len(), 4);
        assert_eq!(&notation[..2], chess_move.from().to_string());
        assert_eq!(&notation[2..], chess_move.to().to_string());
    }
}

#[test]
fn every_valid_promotion_is_distinct_and_formats_canonically() {
    let expected = [
        (PieceKind::Knight, 'n'),
        (PieceKind::Bishop, 'b'),
        (PieceKind::Rook, 'r'),
        (PieceKind::Queen, 'q'),
    ];
    let promotions = Square::all()
        .flat_map(|from| {
            Square::all().flat_map(move |to| {
                expected.map(move |(kind, _)| ChessMove::promotion(from, to, kind).unwrap())
            })
        })
        .collect::<HashSet<_>>();

    assert_eq!(
        promotions.len(),
        Square::COUNT * Square::COUNT * expected.len()
    );
    for (kind, suffix) in expected {
        let chess_move = ChessMove::promotion(Square::H7, Square::H8, kind).unwrap();
        assert_eq!(chess_move.promotion_kind(), Some(kind));
        assert_eq!(chess_move.to_string(), format!("h7h8{suffix}"));
        assert_ne!(chess_move, ChessMove::new(Square::H7, Square::H8));
    }
}

#[test]
fn promotions_reject_pawns_and_kings_without_losing_context() {
    for kind in [PieceKind::Pawn, PieceKind::King] {
        let error = ChessMove::promotion(Square::A7, Square::A8, kind).unwrap_err();

        assert_eq!(error.kind(), kind);
        assert_eq!(
            error.to_string(),
            format!("a pawn cannot promote to a {kind}")
        );
    }
}

#[test]
fn moves_and_errors_have_value_semantics() {
    assert_value_traits::<ChessMove>();
    assert_value_traits::<InvalidPromotion>();

    let ordinary = ChessMove::new(Square::A1, Square::A2);
    let promoted = ChessMove::promotion(Square::A1, Square::A2, PieceKind::Knight).unwrap();
    assert!(ordinary < promoted);
}

#[test]
fn construction_and_accessors_are_const_compatible() {
    const ORDINARY: ChessMove = ChessMove::new(Square::E2, Square::E4);
    const PROMOTION: Result<ChessMove, InvalidPromotion> =
        ChessMove::promotion(Square::A7, Square::A8, PieceKind::Queen);
    const FROM: Square = ORDINARY.from();
    const TO: Square = ORDINARY.to();
    const KIND: Option<PieceKind> = match PROMOTION {
        Ok(chess_move) => chess_move.promotion_kind(),
        Err(_) => None,
    };

    assert_eq!(FROM, Square::E2);
    assert_eq!(TO, Square::E4);
    assert_eq!(KIND, Some(PieceKind::Queen));
}
