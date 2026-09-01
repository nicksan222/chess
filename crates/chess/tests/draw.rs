use chess::{
    Board, ChessMove, Color, DrawClaim, DrawClaimError, DrawClaims, DrawReason, Game, GameStatus,
    HalfmoveClock, MoveError, Piece, PieceKind, Square,
};

fn board_with(pieces: impl IntoIterator<Item = Piece>) -> Board {
    Board::from_pieces(pieces)
}

fn play(game: &mut Game, from: Square, to: Square) {
    ChessMove::new(from, to).play(game).expect("legal move");
}

fn kings_and(piece: Option<Piece>) -> Board {
    board_with(
        [
            Some(Piece::new(Color::White, PieceKind::King, Square::A1)),
            Some(Piece::new(Color::Black, PieceKind::King, Square::H8)),
            piece,
        ]
        .into_iter()
        .flatten(),
    )
}

#[test]
fn insufficient_material_ends_the_game_and_prevents_further_play() {
    let positions = [
        kings_and(None),
        kings_and(Some(Piece::new(
            Color::White,
            PieceKind::Bishop,
            Square::C1,
        ))),
        kings_and(Some(Piece::new(
            Color::Black,
            PieceKind::Knight,
            Square::F6,
        ))),
        board_with([
            Piece::new(Color::White, PieceKind::King, Square::A1),
            Piece::new(Color::White, PieceKind::Bishop, Square::C1),
            Piece::new(Color::Black, PieceKind::Bishop, Square::E3),
            Piece::new(Color::Black, PieceKind::King, Square::H8),
        ]),
    ];

    for board in positions {
        let mut game = Game::from_board(board);
        let expected = GameStatus::Draw {
            reason: DrawReason::InsufficientMaterial,
        };
        assert_eq!(game.status(), expected);
        assert!(game.is_draw());
        assert!(game.status().is_terminal());
        assert_eq!(game.legal_moves().count(), 0);
        assert!(matches!(
            ChessMove::new(Square::A1, Square::A2).play(&mut game),
            Err(MoveError::GameOver {
                final_state: chess::FinalState::Draw {
                    reason: DrawReason::InsufficientMaterial,
                },
            })
        ));
        assert!(matches!(
            game.history().latest().unwrap().event(),
            chess::HistoryEvent::Final(_)
        ));
    }
}

#[test]
fn mating_material_is_not_declared_insufficient() {
    let positions = [
        board_with([
            Piece::new(Color::White, PieceKind::King, Square::A1),
            Piece::new(Color::White, PieceKind::Knight, Square::B1),
            Piece::new(Color::White, PieceKind::Knight, Square::C3),
            Piece::new(Color::Black, PieceKind::King, Square::H8),
        ]),
        board_with([
            Piece::new(Color::White, PieceKind::King, Square::A1),
            Piece::new(Color::White, PieceKind::Bishop, Square::C1),
            Piece::new(Color::Black, PieceKind::Bishop, Square::C2),
            Piece::new(Color::Black, PieceKind::King, Square::H8),
        ]),
        board_with([
            Piece::new(Color::White, PieceKind::King, Square::A1),
            Piece::new(Color::White, PieceKind::Knight, Square::B1),
            Piece::new(Color::White, PieceKind::Bishop, Square::C1),
            Piece::new(Color::Black, PieceKind::King, Square::H8),
        ]),
        kings_and(Some(Piece::new(Color::White, PieceKind::Rook, Square::B1))),
    ];

    for board in positions {
        assert_eq!(Game::from_board(board).status(), GameStatus::InProgress);
    }
}

#[test]
fn unavailable_and_illegal_draw_claims_are_typed_errors() {
    let mut game = Game::new();
    assert_eq!(
        game.claim_draw(DrawClaim::ThreefoldRepetition),
        Err(DrawClaimError::Unavailable {
            claim: DrawClaim::ThreefoldRepetition,
        })
    );
    assert!(matches!(
        game.claim_draw_after(
            ChessMove::new(Square::A3, Square::A4),
            DrawClaim::ThreefoldRepetition,
        ),
        Err(DrawClaimError::Move(MoveError::PendingInvalid))
    ));
    assert!(matches!(
        game.status(),
        GameStatus::Invalid {
            state: chess::InvalidState::DrawClaim {
                claim: DrawClaim::ThreefoldRepetition,
            },
        }
    ));
    assert_eq!(game.legal_moves().count(), 0);
    game.resolve_latest_invalid().unwrap();
    game.resolve_latest_invalid().unwrap();
    assert_eq!(game.status(), GameStatus::InProgress);
}

#[test]
fn threefold_is_claimable_and_fivefold_is_automatic() {
    let mut game = Game::new();
    let cycle = [
        (Square::G1, Square::F3),
        (Square::G8, Square::F6),
        (Square::F3, Square::G1),
        (Square::F6, Square::G8),
    ];

    for _ in 0..2 {
        for (from, to) in cycle {
            play(&mut game, from, to);
        }
    }

    let claims = game.draw_claims();
    assert!(claims.contains(DrawClaim::ThreefoldRepetition));
    assert!(!claims.contains(DrawClaim::FiftyMoveRule));
    assert_eq!(game.status(), GameStatus::DrawClaimAvailable(claims));
    assert!(!game.status().is_terminal());

    let mut claimed = game.clone();
    claimed.claim_draw(DrawClaim::ThreefoldRepetition).unwrap();
    assert_eq!(
        claimed.status(),
        GameStatus::Draw {
            reason: DrawReason::Claimed(DrawClaim::ThreefoldRepetition),
        }
    );
    assert_eq!(claimed.legal_moves().count(), 0);

    for _ in 0..2 {
        for (from, to) in cycle {
            play(&mut game, from, to);
        }
    }

    assert_eq!(
        game.status(),
        GameStatus::Draw {
            reason: DrawReason::FivefoldRepetition,
        }
    );
    assert_eq!(game.legal_moves().count(), 0);
}

#[test]
fn a_repetition_can_be_claimed_by_announcing_the_next_move() {
    let mut game = Game::new();
    for (from, to) in [
        (Square::G1, Square::F3),
        (Square::G8, Square::F6),
        (Square::F3, Square::G1),
        (Square::F6, Square::G8),
        (Square::G1, Square::F3),
        (Square::G8, Square::F6),
        (Square::F3, Square::G1),
    ] {
        play(&mut game, from, to);
    }

    assert_eq!(game.draw_claims(), DrawClaims::NONE);
    let claims = game
        .draw_claims_after(ChessMove::new(Square::F6, Square::G8))
        .unwrap();
    assert!(claims.contains(DrawClaim::ThreefoldRepetition));
    assert_eq!(game.history().len().value(), 7, "the probe must be pure");

    let mut receiver = game.clone();
    game.claim_draw_after(
        ChessMove::new(Square::F6, Square::G8),
        DrawClaim::ThreefoldRepetition,
    )
    .unwrap();
    let expected = GameStatus::Draw {
        reason: DrawReason::Claimed(DrawClaim::ThreefoldRepetition),
    };
    assert_eq!(game.status(), expected);
    assert_eq!(game.history().len().value(), 8);
    assert_eq!(game.piece_at(Square::F6).unwrap().kind(), PieceKind::Knight);
    assert_eq!(game.verify(), Ok(()));

    receiver.accept(game.history().latest().unwrap()).unwrap();
    assert_eq!(receiver.status(), expected);
    assert_eq!(receiver.verify(), Ok(()));
    assert_eq!(receiver.board(), game.board());
}

#[test]
fn fifty_moves_are_claimable_and_seventy_five_are_automatic() {
    let mut claimable_board =
        kings_and(Some(Piece::new(Color::White, PieceKind::Rook, Square::B1)));
    claimable_board.set_halfmove_clock(HalfmoveClock::new(100));
    let claimable = Game::from_board(claimable_board);
    let claims = claimable.draw_claims();
    assert!(claims.contains(DrawClaim::FiftyMoveRule));
    assert_eq!(claimable.status(), GameStatus::DrawClaimAvailable(claims));

    let mut automatic_board = claimable_board;
    automatic_board.set_halfmove_clock(HalfmoveClock::new(150));
    let mut automatic = Game::from_board(automatic_board);
    let expected = GameStatus::Draw {
        reason: DrawReason::SeventyFiveMoveRule,
    };
    assert_eq!(automatic.status(), expected);
    assert!(matches!(
        ChessMove::new(Square::B1, Square::B2).play(&mut automatic),
        Err(MoveError::GameOver {
            final_state: chess::FinalState::Draw {
                reason: DrawReason::SeventyFiveMoveRule,
            },
        })
    ));
}

#[test]
fn the_fifty_move_rule_can_be_claimed_by_announcing_the_next_move() {
    let mut board = kings_and(Some(Piece::new(Color::White, PieceKind::Rook, Square::B1)));
    board.set_halfmove_clock(HalfmoveClock::new(99));
    let mut game = Game::from_board(board);

    assert_eq!(game.draw_claims(), DrawClaims::NONE);
    let chess_move = ChessMove::new(Square::B1, Square::B2);
    let claims = game.draw_claims_after(chess_move).unwrap();
    assert!(claims.contains(DrawClaim::FiftyMoveRule));
    assert_eq!(game.piece_at(Square::B1).unwrap().kind(), PieceKind::Rook);

    game.claim_draw_after(chess_move, DrawClaim::FiftyMoveRule)
        .unwrap();
    assert_eq!(game.verify(), Ok(()));
    assert_eq!(
        game.status(),
        GameStatus::Draw {
            reason: DrawReason::Claimed(DrawClaim::FiftyMoveRule),
        }
    );
    assert_eq!(game.piece_at(Square::B1).unwrap().kind(), PieceKind::Rook);
}

#[test]
fn checkmate_and_stalemate_take_precedence_over_move_count_draws() {
    let mut mate = board_with([
        Piece::new(Color::White, PieceKind::King, Square::E1),
        Piece::new(Color::White, PieceKind::Rook, Square::A8),
        Piece::new(Color::Black, PieceKind::King, Square::E8),
        Piece::new(Color::Black, PieceKind::Pawn, Square::D7),
        Piece::new(Color::Black, PieceKind::Pawn, Square::E7),
        Piece::new(Color::Black, PieceKind::Pawn, Square::F7),
    ]);
    mate.set_side_to_move(Color::Black);
    mate.set_halfmove_clock(HalfmoveClock::new(150));
    assert_eq!(
        Game::from_board(mate).status(),
        GameStatus::Checkmate {
            winner: Color::White,
        }
    );

    let mut stale = board_with([
        Piece::new(Color::White, PieceKind::King, Square::A6),
        Piece::new(Color::White, PieceKind::Queen, Square::C7),
        Piece::new(Color::Black, PieceKind::King, Square::A8),
    ]);
    stale.set_side_to_move(Color::Black);
    stale.set_halfmove_clock(HalfmoveClock::new(150));
    assert_eq!(Game::from_board(stale).status(), GameStatus::Stalemate);
}
