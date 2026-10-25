//! Test-only FEN adapter; production board values remain notation-independent.
use chess::{
    Board, CastlingRights, Color, FullmoveNumber, HalfmoveClock, Piece, PieceKind, Square,
};

pub(crate) fn board(fen: &str) -> Board {
    let [placement, side, castling, en_passant, halfmove, fullmove]: [&str; 6] = fen
        .split_whitespace()
        .collect::<Vec<_>>()
        .try_into()
        .expect("fixture FEN must have six fields");
    let ranks: [&str; 8] = placement
        .split('/')
        .collect::<Vec<_>>()
        .try_into()
        .expect("fixture FEN must have eight ranks");
    let mut board = Board::empty();
    for (rank, text) in (0_u8..8).rev().zip(ranks) {
        let mut file = 0_u8;
        for symbol in text.chars() {
            if let '1'..='8' = symbol {
                file += symbol as u8 - b'0';
            } else {
                assert!(file < 8);
                let color = if symbol.is_ascii_uppercase() {
                    Color::White
                } else {
                    Color::Black
                };
                let kind = match symbol.to_ascii_lowercase() {
                    'p' => PieceKind::Pawn,
                    'n' => PieceKind::Knight,
                    'b' => PieceKind::Bishop,
                    'r' => PieceKind::Rook,
                    'q' => PieceKind::Queen,
                    'k' => PieceKind::King,
                    _ => panic!("invalid FEN piece: {symbol}"),
                };
                let square = Square::try_from(rank * 8 + file).unwrap();
                board.set_piece(Piece::new(color, kind, square));
                file += 1;
            }
        }
        assert_eq!(file, 8);
    }
    board.set_side_to_move(match side {
        "w" => Color::White,
        "b" => Color::Black,
        _ => panic!("invalid FEN side"),
    });
    let mut rights = CastlingRights::NONE;
    if castling != "-" {
        for symbol in castling.chars() {
            match symbol {
                'K' => rights.grant_kingside(Color::White),
                'Q' => rights.grant_queenside(Color::White),
                'k' => rights.grant_kingside(Color::Black),
                'q' => rights.grant_queenside(Color::Black),
                _ => panic!("invalid FEN castling rights"),
            }
        }
    }
    board.set_castling_rights(rights);
    board.set_en_passant_target(if en_passant == "-" {
        None
    } else {
        Some(en_passant.parse().unwrap())
    });
    board.set_halfmove_clock(HalfmoveClock::new(halfmove.parse().unwrap()));
    board.set_fullmove_number(FullmoveNumber::new(fullmove.parse().unwrap()).unwrap());
    board
}

#[test]
fn initial_fen_matches_the_engines_known_board() {
    assert_eq!(
        board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        Board::INITIAL
    );
}
