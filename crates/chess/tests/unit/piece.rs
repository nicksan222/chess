use std::collections::HashSet;

use chess::{Color, Piece, PieceKind, Square, SquareIndex};

fn assert_value_traits<T>()
where
    T: Copy + Clone + std::fmt::Debug + Eq + Ord + std::hash::Hash + Send + Sync + 'static,
{
}

fn all_pieces() -> impl Iterator<Item = Piece> {
    Color::ALL
        .into_iter()
        .flat_map(|color| PieceKind::ALL.map(move |kind| (color, kind)))
        .enumerate()
        .map(|(index, (color, kind))| {
            Piece::new(
                color,
                kind,
                Square::from_index(SquareIndex::new(index as u8).unwrap()),
            )
        })
}

#[test]
fn domain_values_implement_expected_value_traits() {
    assert_value_traits::<Color>();
    assert_value_traits::<PieceKind>();
    assert_value_traits::<Piece>();
}

#[test]
fn colors_have_stable_order_and_opposites() {
    assert_eq!(Color::ALL, [Color::White, Color::Black]);
    assert_eq!(Color::White.opposite(), Color::Black);
    assert_eq!(Color::Black.opposite(), Color::White);
    assert_eq!(Color::White.to_string(), "white");
    assert_eq!(Color::Black.to_string(), "black");
}

#[test]
fn piece_kinds_have_stable_order_and_names() {
    let expected = [
        (PieceKind::Pawn, "pawn"),
        (PieceKind::Knight, "knight"),
        (PieceKind::Bishop, "bishop"),
        (PieceKind::Rook, "rook"),
        (PieceKind::Queen, "queen"),
        (PieceKind::King, "king"),
    ];

    assert_eq!(PieceKind::ALL.len(), expected.len());
    for (actual, (kind, name)) in PieceKind::ALL.into_iter().zip(expected) {
        assert_eq!(actual, kind);
        assert_eq!(kind.to_string(), name);
    }
    assert_eq!(
        PieceKind::PROMOTIONS,
        [
            PieceKind::Knight,
            PieceKind::Bishop,
            PieceKind::Rook,
            PieceKind::Queen,
        ]
    );
}

#[test]
fn pieces_are_the_cartesian_product_of_color_and_kind() {
    let pieces = all_pieces().collect::<Vec<_>>();

    assert_eq!(pieces.len(), Color::ALL.len() * PieceKind::ALL.len());
    assert_eq!(pieces.iter().copied().collect::<HashSet<_>>().len(), 12);
    assert!(pieces.windows(2).all(|pair| pair[0] < pair[1]));

    for piece in pieces {
        assert!(Color::ALL.contains(&piece.color()));
        assert!(PieceKind::ALL.contains(&piece.kind()));
        assert!(Square::all().any(|square| square == piece.square()));
    }
}

#[test]
fn constructor_and_accessors_are_const_compatible() {
    const PIECE: Piece = Piece::new(Color::Black, PieceKind::Queen, Square::D5);
    const COLOR: Color = PIECE.color();
    const KIND: PieceKind = PIECE.kind();
    const SQUARE: Square = PIECE.square();

    assert_eq!(COLOR, Color::Black);
    assert_eq!(KIND, PieceKind::Queen);
    assert_eq!(SQUARE, Square::D5);
    assert_eq!(PIECE, Piece::new(COLOR, KIND, SQUARE));
}
