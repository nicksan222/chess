use chess::{
    Color, Piece, PieceKind,
    notation::fen::{PieceSymbolError, decode_piece, encode_piece},
};

fn all_pieces() -> impl Iterator<Item = Piece> {
    Color::ALL
        .into_iter()
        .flat_map(|color| PieceKind::ALL.map(|kind| Piece::new(color, kind)))
}

#[test]
fn every_piece_round_trips_through_its_fen_symbol() {
    let expected = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k'];

    for (piece, symbol) in all_pieces().zip(expected) {
        assert_eq!(encode_piece(piece), symbol);
        assert_eq!(decode_piece(symbol), Ok(piece));
    }
}

#[test]
fn symbol_case_encodes_piece_color() {
    for kind in PieceKind::ALL {
        let white = encode_piece(Piece::new(Color::White, kind));
        let black = encode_piece(Piece::new(Color::Black, kind));

        assert!(white.is_ascii_uppercase());
        assert!(black.is_ascii_lowercase());
        assert_eq!(white.to_ascii_lowercase(), black);
    }
}

#[test]
fn invalid_symbols_return_the_rejected_character() {
    for symbol in ['x', ' ', '1', '♟'] {
        let error = decode_piece(symbol).expect_err("symbol is invalid");

        assert_eq!(error.symbol(), symbol);
        assert_eq!(
            error.to_string(),
            format!("'{symbol}' is not a FEN piece symbol")
        );
    }
}

#[test]
fn conversions_are_const_compatible() {
    const PIECE: Piece = Piece::new(Color::Black, PieceKind::Knight);
    const SYMBOL: char = encode_piece(PIECE);
    const DECODED: Result<Piece, PieceSymbolError> = decode_piece(SYMBOL);

    assert_eq!(SYMBOL, 'n');
    assert_eq!(DECODED, Ok(PIECE));
}
