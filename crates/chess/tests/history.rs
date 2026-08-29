use chess::{
    Board, ChessMove, Color, Game, GameSyncError, HistoryError, MoveHash, MoveHistory, MoveStep,
    Piece, PieceKind, Ply, Square,
};

fn synchronization_board(pawn_square: Square) -> Board {
    let mut board = Board::empty();
    for piece in [
        Piece::new(Color::White, PieceKind::King, Square::H1),
        Piece::new(Color::White, PieceKind::Pawn, pawn_square),
        Piece::new(Color::Black, PieceKind::King, Square::H8),
    ] {
        board.set_piece(piece);
    }
    board
}

#[test]
fn every_link_stores_a_cumulative_hash_and_previous_tip() {
    let mut history = MoveHistory::new();
    let first = history.push(ChessMove::new(Square::E2, Square::E4));
    let second = history.push(ChessMove::new(Square::E7, Square::E5));

    assert_eq!(first.ply(), Ply::FIRST);
    assert_eq!(first.previous_hash(), MoveHash::GENESIS);
    assert_eq!(
        first.hash().to_string(),
        "ea0fc25719e0cca4c5f9d507e5f67de36d2918b331de690b40e3283f13dcd59b"
    );
    assert_eq!(second.ply(), Ply::new(2).unwrap());
    assert_eq!(second.previous_hash(), first.hash());
    assert_eq!(history.tip(), second.hash());
    assert_eq!(history.len().value(), 2);
    assert_eq!(history.iter().copied().collect::<Vec<_>>(), [first, second]);
    assert_eq!(history.verify(), Ok(()));
}

#[test]
fn peers_verify_all_previous_moves_before_accepting_the_latest() {
    let mut sender = Game::new();
    let mut receiver = Game::new();

    let first = sender
        .piece_at(Square::E2)
        .unwrap()
        .move_to(Square::E4, &mut sender)
        .unwrap();

    assert!(receiver.history().is_synced_before(first));
    receiver.accept(first).unwrap();
    assert_eq!(receiver.board(), sender.board());
    assert_eq!(receiver.history(), sender.history());

    let second = sender
        .piece_at(Square::E7)
        .unwrap()
        .move_to(Square::E5, &mut sender)
        .unwrap();
    assert!(receiver.history().is_synced_before(second));
    receiver.accept(second).unwrap();
    assert_eq!(receiver.history().tip(), sender.history().tip());
}

#[test]
fn initial_board_is_part_of_game_synchronization() {
    let first_board = synchronization_board(Square::A2);
    let second_board = synchronization_board(Square::B2);
    let mut sender = Game::from_board(first_board);
    let mut receiver = Game::from_board(second_board);
    let step = sender
        .piece_at(Square::H1)
        .unwrap()
        .move_to(Square::G1, &mut sender)
        .unwrap();

    assert_ne!(sender.history().anchor(), receiver.history().anchor());
    assert!(matches!(
        receiver.accept(step),
        Err(GameSyncError::History(HistoryError::PreviousHash { .. }))
    ));
}

#[test]
fn divergent_or_corrupted_steps_are_rejected_without_mutation() {
    let mut local = Game::new();
    local
        .piece_at(Square::D2)
        .unwrap()
        .move_to(Square::D4, &mut local)
        .unwrap();
    let before = local.clone();

    let mut other = Game::new();
    let divergent = other
        .piece_at(Square::E2)
        .unwrap()
        .move_to(Square::E4, &mut other)
        .unwrap();
    assert!(matches!(
        local.accept(divergent),
        Err(GameSyncError::History(HistoryError::Ply { .. }))
    ));
    assert_eq!(local, before);

    let mut source = MoveHistory::new();
    let valid = source.push(ChessMove::new(Square::E2, Square::E4));
    let mut bytes = valid.hash().to_bytes();
    bytes[0] ^= 0xff;
    let corrupted = MoveStep::from_parts(
        valid.ply(),
        valid.chess_move(),
        valid.previous_hash(),
        MoveHash::from_bytes(bytes),
    );
    let mut empty = MoveHistory::new();
    assert!(matches!(
        empty.try_append(corrupted),
        Err(HistoryError::Hash { .. })
    ));
    assert!(empty.is_empty());
    assert_eq!(empty.tip(), MoveHash::GENESIS);
}

#[test]
fn popping_restores_the_previous_cumulative_hash() {
    let mut history = MoveHistory::new();
    let first = history.push(ChessMove::new(Square::E2, Square::E4));
    let second = history.push(ChessMove::new(Square::E7, Square::E5));

    assert_eq!(history.pop(), Some(second));
    assert_eq!(history.tip(), first.hash());
    assert_eq!(history.pop(), Some(first));
    assert_eq!(history.tip(), MoveHash::GENESIS);
    assert_eq!(history.pop(), None);
}
