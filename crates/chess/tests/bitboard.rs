use std::mem::size_of;

use chess::{BitBoard, BoardDirection, BoardEdge, File, Rank, Square, SquareIndex, SquareOffset};

#[test]
fn square_coordinates_and_indices_round_trip_exhaustively() {
    let squares = Square::all().collect::<Vec<_>>();

    assert_eq!(squares.len(), 64);
    assert_eq!(squares.first(), Some(&Square::A1));
    assert_eq!(squares.last(), Some(&Square::H8));

    for value in 0_u8..64 {
        let index = SquareIndex::new(value).expect("index is valid");
        let square = Square::from_index(index);
        assert_eq!(square.index(), index);
        assert_eq!(Square::new(square.file(), square.rank()), square);
        assert_eq!(index.value(), value);
    }
}

#[test]
fn square_rejects_invalid_coordinates_and_formats_algebraically() {
    assert_eq!(Square::new(File::E, Rank::Four), Square::E4);
    let index_error = SquareIndex::new(64).expect_err("index is invalid");
    assert_eq!(index_error.index(), 64);

    let error = Square::try_from(255).expect_err("index is invalid");
    assert_eq!(error.index(), 255);
    assert_eq!(error.to_string(), "square index 255 is outside 0..64");
    assert_eq!(Square::E4.to_string(), "e4");
    assert_eq!(format!("{:?}", Square::H8), "h8");
}

#[test]
fn square_offsets_respect_board_edges() {
    assert_eq!(Square::E4.offset(SquareOffset::new(1, 2)), Some(Square::F6));
    assert_eq!(Square::A1.offset(SquareOffset::new(-1, 0)), None);
    assert_eq!(Square::A1.offset(SquareOffset::new(0, -1)), None);
    assert_eq!(Square::H8.offset(SquareOffset::new(1, 0)), None);
    assert_eq!(Square::H8.offset(SquareOffset::new(0, 1)), None);
}

#[test]
fn square_steps_and_rays_use_objective_coordinates() {
    assert_eq!(
        Square::D4.step(BoardDirection::TowardRank8),
        Some(Square::D5)
    );
    assert_eq!(
        Square::D4.step(BoardDirection::TowardRank1FileA),
        Some(Square::C3)
    );
    assert_eq!(Square::A1.step(BoardDirection::TowardFileA), None);
    assert_eq!(Square::H8.step(BoardDirection::TowardRank8FileH), None);
    assert_eq!(
        Square::D4
            .ray(BoardDirection::TowardRank8FileH)
            .collect::<Vec<_>>(),
        [Square::E5, Square::F6, Square::G7, Square::H8]
    );
    assert_eq!(
        Square::H4
            .ray(BoardDirection::TowardFileA)
            .collect::<Vec<_>>(),
        [
            Square::G4,
            Square::F4,
            Square::E4,
            Square::D4,
            Square::C4,
            Square::B4,
            Square::A4,
        ]
    );
}

#[test]
fn board_edges_are_objective_and_corners_belong_to_two_edges() {
    assert!(BoardEdge::FileA.contains(Square::A4));
    assert!(BoardEdge::Rank8.contains(Square::E8));
    assert!(!BoardEdge::FileH.contains(Square::G8));
    assert_eq!(
        Square::A1.edges().collect::<Vec<_>>(),
        [BoardEdge::FileA, BoardEdge::Rank1]
    );
    assert_eq!(
        Square::H8.edges().collect::<Vec<_>>(),
        [BoardEdge::FileH, BoardEdge::Rank8]
    );
    assert!(Square::A1.is_edge());
    assert!(Square::A1.is_corner());
    assert!(Square::A4.is_edge());
    assert!(!Square::A4.is_corner());
    assert!(!Square::D4.is_edge());
    assert!(!Square::D4.is_corner());

    for edge in BoardEdge::ALL {
        assert_eq!(
            Square::all()
                .filter(|square| edge.contains(*square))
                .count(),
            8
        );
    }
    assert_eq!(Square::all().filter(|square| square.is_edge()).count(), 28);
    assert_eq!(Square::all().filter(|square| square.is_corner()).count(), 4);
    for square in Square::all() {
        let edge_count = square.edges().count();
        assert_eq!(square.is_edge(), edge_count != 0);
        assert_eq!(square.is_corner(), edge_count == 2);
    }
}

#[test]
fn square_iterator_is_exact_sized_and_double_ended() {
    let mut squares = Square::all();

    assert_eq!(squares.len(), 64);
    assert_eq!(squares.next(), Some(Square::A1));
    assert_eq!(squares.next_back(), Some(Square::H8));
    assert_eq!(squares.len(), 62);
    assert_eq!(squares.count(), 62);
}

#[test]
fn bitboard_has_compact_representation_and_set_semantics() {
    assert_eq!(size_of::<BitBoard>(), size_of::<u64>());

    let mut board = BitBoard::EMPTY;
    assert!(board.is_empty());
    assert!(!board.is_full());
    assert!(board.insert(Square::A1));
    assert!(!board.insert(Square::A1));
    assert!(board.insert(Square::E4));
    assert_eq!(board.len(), 2);
    assert!(board.contains(Square::A1));
    assert!(board.remove(Square::A1));
    assert!(!board.remove(Square::A1));
    assert!(board.toggle(Square::H8));
    assert!(!board.toggle(Square::H8));
    assert_eq!(board, BitBoard::from(Square::E4));

    board.clear();
    assert_eq!(board, BitBoard::EMPTY);
    assert!(BitBoard::FULL.is_full());
}

#[test]
fn iteration_is_ordered_exact_sized_and_double_ended() {
    let board: BitBoard = [Square::H8, Square::E4, Square::A1].into_iter().collect();
    let mut squares = board.iter();

    assert_eq!(squares.len(), 3);
    assert_eq!(squares.next(), Some(Square::A1));
    assert_eq!(squares.next_back(), Some(Square::H8));
    assert_eq!(squares.next(), Some(Square::E4));
    assert_eq!(squares.next(), None);
    assert_eq!(board.first(), Some(Square::A1));
    assert_eq!(board.last(), Some(Square::H8));
    assert_eq!(format!("{board:?}"), "{a1, e4, h8}");
}

#[test]
fn set_operators_match_raw_bit_operations() {
    let first: BitBoard = [Square::A1, Square::B2, Square::C3].into_iter().collect();
    let second: BitBoard = [Square::B2, Square::D4].into_iter().collect();

    assert_eq!(
        (first | second).iter().collect::<Vec<_>>(),
        [Square::A1, Square::B2, Square::C3, Square::D4]
    );
    assert_eq!((first & second).iter().collect::<Vec<_>>(), [Square::B2]);
    assert_eq!(
        (first ^ second).iter().collect::<Vec<_>>(),
        [Square::A1, Square::C3, Square::D4]
    );
    assert_eq!(
        (first - second).iter().collect::<Vec<_>>(),
        [Square::A1, Square::C3]
    );
    assert!(first.intersects(second));
    assert!(!first.is_disjoint(second));
    assert_eq!((!BitBoard::EMPTY), BitBoard::FULL);

    let mut assigned = first;
    assigned |= second;
    assigned &= !BitBoard::from(Square::A1);
    assigned ^= BitBoard::from(Square::H8);
    assigned -= BitBoard::from(Square::B2);
    assert_eq!(
        assigned.iter().collect::<Vec<_>>(),
        [Square::C3, Square::D4, Square::H8]
    );
}

#[test]
fn directional_shifts_never_wrap_across_files() {
    assert_eq!(
        BitBoard::from(Square::E4).north(),
        BitBoard::from(Square::E5)
    );
    assert_eq!(
        BitBoard::from(Square::E4).south(),
        BitBoard::from(Square::E3)
    );
    assert_eq!(
        BitBoard::from(Square::E4).east(),
        BitBoard::from(Square::F4)
    );
    assert_eq!(
        BitBoard::from(Square::E4).west(),
        BitBoard::from(Square::D4)
    );
    assert_eq!(
        BitBoard::from(Square::E4).north_east(),
        BitBoard::from(Square::F5)
    );
    assert_eq!(
        BitBoard::from(Square::E4).north_west(),
        BitBoard::from(Square::D5)
    );
    assert_eq!(
        BitBoard::from(Square::E4).south_east(),
        BitBoard::from(Square::F3)
    );
    assert_eq!(
        BitBoard::from(Square::E4).south_west(),
        BitBoard::from(Square::D3)
    );

    assert!(BitBoard::from(Square::H4).east().is_empty());
    assert!(BitBoard::from(Square::A4).west().is_empty());
    assert!(BitBoard::from(Square::A8).north().is_empty());
    assert!(BitBoard::from(Square::A1).south().is_empty());
}

#[test]
fn raw_shifts_are_total_for_every_shift_amount() {
    let board = BitBoard::from(Square::A1);

    assert_eq!(board << 63, BitBoard::from(Square::H8));
    assert_eq!(board << 64, BitBoard::EMPTY);
    assert_eq!(BitBoard::from(Square::H8) >> 63, board);
    assert_eq!(BitBoard::from(Square::H8) >> 64, BitBoard::EMPTY);

    let mut shifted = board;
    shifted <<= 8;
    assert_eq!(shifted, BitBoard::from(Square::A2));
    shifted >>= 8;
    assert_eq!(shifted, board);
}

#[test]
fn bitboard_round_trips_every_raw_value_in_deterministic_sample() {
    let mut state = 0x0123_4567_89AB_CDEF_u64;

    for _ in 0..10_000 {
        state = state
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        let board = BitBoard::from_bits(state);
        let reconstructed: BitBoard = board.iter().collect();

        assert_eq!(board.bits(), state);
        assert_eq!(board.len(), state.count_ones());
        assert_eq!(reconstructed, board);
    }
}
