use chess::{Square, SquareSet};

#[test]
fn square_set_has_collection_semantics() {
    let mut board = SquareSet::EMPTY;
    assert!(board.is_empty());
    assert!(!board.is_full());
    assert!(board.insert(Square::A1));
    assert!(!board.insert(Square::A1));
    assert!(board.insert(Square::E4));
    assert_eq!(board.len().value(), 2);
    assert!(board.contains(Square::A1));
    assert!(board.remove(Square::A1));
    assert!(!board.remove(Square::A1));
    assert!(board.toggle(Square::H8));
    assert!(!board.toggle(Square::H8));
    assert_eq!(board, SquareSet::from(Square::E4));

    board.clear();
    assert_eq!(board, SquareSet::EMPTY);
    assert!(SquareSet::FULL.is_full());
}

#[test]
fn iteration_is_ordered_exact_sized_and_double_ended() {
    let board: SquareSet = [Square::H8, Square::E4, Square::A1].into_iter().collect();
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
fn set_operators_match_union_intersection_and_difference() {
    let first: SquareSet = [Square::A1, Square::B2, Square::C3].into_iter().collect();
    let second: SquareSet = [Square::B2, Square::D4].into_iter().collect();

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
    assert_eq!((!SquareSet::EMPTY), SquareSet::FULL);

    let mut assigned = first;
    assigned |= second;
    assigned &= !SquareSet::from(Square::A1);
    assigned ^= SquareSet::from(Square::H8);
    assigned -= SquareSet::from(Square::B2);
    assert_eq!(
        assigned.iter().collect::<Vec<_>>(),
        [Square::C3, Square::D4, Square::H8]
    );
}
