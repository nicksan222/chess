use chess::{
    Board, ChessMove, Color, FinalState, Game, GameSyncError, HistoryError, HistoryEvent,
    InvalidState, MoveHash, MoveHistory, MoveStep, Piece, PieceKind, Ply, Square,
};

fn synchronization_board(pawn_square: Square) -> Board {
    Board::from_pieces([
        Piece::new(Color::White, PieceKind::King, Square::H1),
        Piece::new(Color::White, PieceKind::Pawn, pawn_square),
        Piece::new(Color::Black, PieceKind::King, Square::H8),
    ])
}

#[test]
fn every_link_stores_a_cumulative_hash_and_previous_tip() {
    let mut history = MoveHistory::new();
    let first = history
        .push(HistoryEvent::Move(ChessMove::new(Square::E2, Square::E4)))
        .unwrap();
    let second = history
        .push(HistoryEvent::Move(ChessMove::new(Square::E7, Square::E5)))
        .unwrap();

    assert_eq!(first.ply(), Ply::FIRST);
    assert_eq!(first.previous_hash(), MoveHash::GENESIS);
    assert_eq!(
        first.hash().to_string(),
        "59c8f0c8e610d5d3f71e08c7d6f8749bb8759167e8208c8c144f36650a44d5e6"
    );
    assert_eq!(second.ply(), Ply::new(2).unwrap());
    assert_eq!(second.previous_hash(), first.hash());
    assert_eq!(history.tip(), second.hash());
    assert_eq!(history.len().value(), 2);
    assert_eq!(history.iter().copied().collect::<Vec<_>>(), [first, second]);
    assert_eq!(history.verify(), Ok(()));
}

#[test]
fn every_event_kind_participates_in_the_hash_chain() {
    let event_hash = |event| {
        let mut history = MoveHistory::new();
        history.push(event).unwrap().hash()
    };
    let moved = event_hash(HistoryEvent::Move(ChessMove::new(Square::E2, Square::E4)));
    let invalid = event_hash(HistoryEvent::Invalid(InvalidState::PendingInvalid));
    let final_hash = event_hash(HistoryEvent::Final(FinalState::Stalemate));

    assert_ne!(moved, invalid);
    assert_ne!(invalid, final_hash);
    assert_ne!(moved, final_hash);
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
    let valid = source
        .push(HistoryEvent::Move(ChessMove::new(Square::E2, Square::E4)))
        .unwrap();
    let mut bytes = valid.hash().to_bytes();
    bytes[0] ^= 0xff;
    let corrupted = MoveStep::from_parts(
        valid.ply(),
        valid.event(),
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
fn invalid_states_resolve_in_reverse_and_other_events_cannot_be_popped() {
    let mut history = MoveHistory::new();
    let moved = history
        .push(HistoryEvent::Move(ChessMove::new(Square::E2, Square::E4)))
        .unwrap();
    let first = history
        .push(HistoryEvent::Invalid(InvalidState::PendingInvalid))
        .unwrap();
    let second = history
        .push(HistoryEvent::Invalid(InvalidState::PendingInvalid))
        .unwrap();

    assert!(matches!(
        history.push(HistoryEvent::Move(ChessMove::new(Square::E7, Square::E5))),
        Err(HistoryError::InvalidTransition { .. })
    ));
    assert_eq!(history.resolve_latest_invalid(), Ok(second));
    assert_eq!(history.resolve_latest_invalid(), Ok(first));
    assert_eq!(history.tip(), moved.hash());
    assert!(matches!(
        history.resolve_latest_invalid(),
        Err(HistoryError::NothingToResolve { .. })
    ));
}

#[test]
fn final_events_permanently_seal_history() {
    let mut history = MoveHistory::new();
    let final_step = history
        .push(HistoryEvent::Final(FinalState::Stalemate))
        .unwrap();

    assert_eq!(history.latest(), Some(final_step));
    assert!(matches!(
        history.push(HistoryEvent::Invalid(InvalidState::PendingInvalid)),
        Err(HistoryError::InvalidTransition { .. })
    ));
    assert!(matches!(
        history.resolve_latest_invalid(),
        Err(HistoryError::NothingToResolve { .. })
    ));
}
