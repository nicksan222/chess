mod board;

use std::time::Duration;

use board::{Board, square};
use firmware::{
    hardware::{HardwareEvent, HardwareEventBus, PieceEvent, hall::HallSensors},
    runtime::Firmware,
    tuning::HallTuning,
};

async fn next_piece(firmware: &mut Firmware, after: u64) -> PieceEvent {
    let snapshot = tokio::time::timeout(Duration::from_secs(1), firmware.after(after))
        .await
        .expect("the poller should report a piece change")
        .unwrap();
    let Some(HardwareEvent::Piece(event)) = snapshot.last_event else {
        panic!("expected a piece event, got {:?}", snapshot.last_event);
    };
    event
}

#[tokio::test]
async fn hall_banks_drive_piece_events_into_the_runtime() {
    let board = Board::empty();
    board.place("E2");
    let mut firmware = Firmware::start().unwrap();
    let sensors =
        HallSensors::start(board.clone(), &firmware.events(), HallTuning::DEFAULT).unwrap();

    // The starting position arrives as placements.
    assert_eq!(
        next_piece(&mut firmware, 0).await,
        PieceEvent::Placed(square("E2"))
    );

    board.remove("E2");
    assert_eq!(
        next_piece(&mut firmware, 1).await,
        PieceEvent::Removed(square("E2"))
    );
    board.place("E4");
    assert_eq!(
        next_piece(&mut firmware, 2).await,
        PieceEvent::Placed(square("E4"))
    );

    drop(sensors);
    board.remove("E4");
    tokio::time::sleep(Duration::from_millis(200)).await;
    assert_eq!(firmware.snapshot().processed_events, 3);
    firmware.shutdown().await.unwrap();
}

#[test]
fn hall_sensors_need_a_runtime() {
    let error = HallSensors::start(
        Board::empty(),
        &HardwareEventBus::new(),
        HallTuning::DEFAULT,
    )
    .err()
    .unwrap();
    assert!(error.to_string().contains("active Tokio runtime"));
}

/// A slow kernel transfer must not stall the single-thread application loop.
#[tokio::test]
async fn a_slow_hall_bus_does_not_stall_the_runtime() {
    use embedded_hal::i2c::{ErrorType, I2c, Operation};
    use firmware::hardware::pins::{Button, ButtonEvent};
    use std::sync::{
        Arc,
        atomic::{AtomicUsize, Ordering},
    };

    struct SlowBus(Arc<AtomicUsize>);
    impl ErrorType for SlowBus {
        type Error = std::convert::Infallible;
    }
    impl I2c for SlowBus {
        fn transaction(&mut self, _: u8, _: &mut [Operation<'_>]) -> Result<(), Self::Error> {
            if self.0.fetch_add(1, Ordering::SeqCst) == 0 {
                std::thread::sleep(Duration::from_millis(200));
            }
            Ok(())
        }
    }
    let entered = Arc::new(AtomicUsize::new(0));
    let mut firmware = Firmware::start().unwrap();
    let start = std::time::Instant::now();
    let sensors = HallSensors::start(
        SlowBus(entered.clone()),
        &firmware.events(),
        HallTuning::DEFAULT,
    )
    .unwrap();
    while entered.load(Ordering::SeqCst) == 0 {
        tokio::task::yield_now().await;
    }
    firmware
        .events()
        .emit(ButtonEvent::Pressed(Button::Down).into())
        .unwrap();
    let snapshot = tokio::time::timeout(Duration::from_millis(100), firmware.after(0))
        .await
        .unwrap()
        .unwrap();
    assert_eq!(
        snapshot.last_event,
        Some(ButtonEvent::Pressed(Button::Down).into())
    );
    assert!(start.elapsed() < Duration::from_millis(100));
    drop(sensors);
    firmware.shutdown().await.unwrap();
    // The first bank may finish its in-flight configuration; no next bank
    // may be touched after cancellation.
    tokio::time::sleep(Duration::from_millis(250)).await;
    assert_eq!(entered.load(Ordering::SeqCst), 2);
}

#[tokio::test]
async fn invalid_hall_tuning_returns_an_error_before_starting_a_worker() {
    for tuning in [
        HallTuning {
            scan_interval: Duration::ZERO,
            ..HallTuning::DEFAULT
        },
        HallTuning {
            stable_scans: 0,
            ..HallTuning::DEFAULT
        },
    ] {
        let error =
            HallSensors::start(Board::empty(), &HardwareEventBus::new(), tuning).unwrap_err();
        assert_eq!(error.kind(), std::io::ErrorKind::InvalidInput);
    }
}

#[tokio::test]
async fn a_full_board_is_delivered_without_losing_square_events() {
    let board = Board::empty();
    for file in 'A'..='H' {
        for rank in 1..=8 {
            board.place(&format!("{file}{rank}"));
        }
    }
    let mut firmware = Firmware::start().unwrap();
    let _sensors =
        HallSensors::start(board.clone(), &firmware.events(), HallTuning::DEFAULT).unwrap();
    let full = tokio::time::timeout(Duration::from_secs(1), firmware.after(63))
        .await
        .unwrap()
        .unwrap();
    assert_eq!(full.modules.pieces.count(), 64);
    for file in 'A'..='H' {
        for rank in 1..=8 {
            board.remove(&format!("{file}{rank}"));
        }
    }
    let empty = tokio::time::timeout(Duration::from_secs(1), firmware.after(127))
        .await
        .unwrap()
        .unwrap();
    assert_eq!(empty.modules.pieces.count(), 0);
    firmware.shutdown().await.unwrap();
}
