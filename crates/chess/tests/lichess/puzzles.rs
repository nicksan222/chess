//! Typed, checked views of the published puzzles and independent oracle output.
use std::{collections::BTreeSet, fmt};

use chess::{Board, ChessMove, DrawReason, GameStatus};

use crate::fen;

pub struct Puzzle {
    pub positions: Vec<Position>,
}

pub struct Position {
    pub puzzle_id: &'static str,
    pub ply: usize,
    pub chess_move: Option<ChessMove>,
    pub board: Board,
    pub legal_moves: Vec<ChessMove>,
    pub in_check: bool,
    pub status: GameStatus,
}

impl Position {
    fn parse(row: &'static str) -> Self {
        let [puzzle_id, ply, uci, fen, legal, check, status]: [&str; 7] = row
            .split('\t')
            .collect::<Vec<_>>()
            .try_into()
            .expect("reference position must have seven columns");
        let board = fen::board(fen);
        let status = match status {
            "active" => GameStatus::InProgress,
            "checkmate" => GameStatus::Checkmate {
                winner: board.side_to_move().opposite(),
            },
            "stalemate" => GameStatus::Stalemate,
            "insufficient" => GameStatus::Draw {
                reason: DrawReason::InsufficientMaterial,
            },
            _ => panic!("unknown reference status: {status}"),
        };
        let mut legal_moves: Vec<ChessMove> = legal
            .split_whitespace()
            .map(|uci| uci.parse().expect("valid reference move"))
            .collect();
        legal_moves.sort_unstable();
        assert!(legal_moves.windows(2).all(|pair| pair[0] != pair[1]));
        Self {
            puzzle_id,
            ply: ply.parse().expect("valid reference ply"),
            chess_move: (uci != "-").then(|| uci.parse().expect("valid reference move")),
            board,
            legal_moves,
            in_check: match check {
                "0" => false,
                "1" => true,
                _ => panic!("unknown reference check flag: {check}"),
            },
            status,
        }
    }
}

impl fmt::Display for Position {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "puzzle {}, ply {}", self.puzzle_id, self.ply)?;
        if let Some(chess_move) = self.chess_move {
            write!(f, ", move {chess_move}")?;
        }
        Ok(())
    }
}

pub fn load() -> Vec<Puzzle> {
    let mut reference = include_str!("fixtures/expected_positions.tsv")
        .lines()
        .skip(1);
    let mut ids = BTreeSet::new();
    let mut move_count = 0;
    let puzzles: Vec<_> = include_str!("fixtures/puzzles.tsv")
        .lines()
        .skip(1)
        .map(|row| {
            let [id, fen, moves, _themes]: [&str; 4] = row
                .split('\t')
                .collect::<Vec<_>>()
                .try_into()
                .expect("published puzzle must have four columns");
            assert!(ids.insert(id), "duplicate puzzle: {id}");
            let moves = moves
                .split_whitespace()
                .map(|uci| Some(uci.parse::<ChessMove>().expect("valid published move")));
            let positions: Vec<_> = std::iter::once(None)
                .chain(moves)
                .enumerate()
                .map(|(ply, chess_move)| {
                    let position =
                        Position::parse(reference.next().expect("missing reference position"));
                    assert_eq!(position.puzzle_id, id, "{position}");
                    assert_eq!(position.ply, ply, "{position}");
                    assert_eq!(position.chess_move, chess_move, "published move {position}");
                    position
                })
                .collect();
            assert!(positions.len() > 1, "puzzle {id} has no moves");
            move_count += positions.len() - 1;
            assert_eq!(positions[0].board, fen::board(fen), "published FEN: {id}");
            Puzzle { positions }
        })
        .collect();
    assert!(reference.next().is_none(), "unexpected reference positions");
    assert_eq!(puzzles.len(), 157, "incomplete puzzle corpus");
    assert_eq!(move_count, 764, "incomplete move corpus");
    puzzles
}
