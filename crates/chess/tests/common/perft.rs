use chess::{Board, CastlingRights, Color, Game, Piece, PieceKind, Square};

pub fn count(game: &Game, depth: u8) -> u64 {
    if depth == 0 {
        return 1;
    }

    game.legal_moves()
        .map(|chess_move| {
            let mut next = game.clone();
            chess_move.play(&mut next).expect("generated move is legal");
            count(&next, depth - 1)
        })
        .sum()
}

pub fn kiwipete() -> Game {
    use Color::{Black, White};
    use PieceKind::{Bishop, King, Knight, Pawn, Queen, Rook};

    // r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1
    let mut board = Board::from_pieces([
        Piece::new(White, King, Square::E1),
        Piece::new(White, Queen, Square::F3),
        Piece::new(White, Rook, Square::A1),
        Piece::new(White, Rook, Square::H1),
        Piece::new(White, Bishop, Square::D2),
        Piece::new(White, Bishop, Square::E2),
        Piece::new(White, Knight, Square::C3),
        Piece::new(White, Knight, Square::E5),
        Piece::new(White, Pawn, Square::A2),
        Piece::new(White, Pawn, Square::B2),
        Piece::new(White, Pawn, Square::C2),
        Piece::new(White, Pawn, Square::D5),
        Piece::new(White, Pawn, Square::E4),
        Piece::new(White, Pawn, Square::F2),
        Piece::new(White, Pawn, Square::G2),
        Piece::new(White, Pawn, Square::H2),
        Piece::new(Black, King, Square::E8),
        Piece::new(Black, Queen, Square::E7),
        Piece::new(Black, Rook, Square::A8),
        Piece::new(Black, Rook, Square::H8),
        Piece::new(Black, Bishop, Square::A6),
        Piece::new(Black, Bishop, Square::G7),
        Piece::new(Black, Knight, Square::B6),
        Piece::new(Black, Knight, Square::F6),
        Piece::new(Black, Pawn, Square::A7),
        Piece::new(Black, Pawn, Square::B4),
        Piece::new(Black, Pawn, Square::C7),
        Piece::new(Black, Pawn, Square::D7),
        Piece::new(Black, Pawn, Square::E6),
        Piece::new(Black, Pawn, Square::F7),
        Piece::new(Black, Pawn, Square::G6),
        Piece::new(Black, Pawn, Square::H3),
    ]);
    board.set_castling_rights(CastlingRights::ALL);
    Game::from_board(board)
}
