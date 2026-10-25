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
        atomic::{AtomicBool, Ordering},
    };

    struct SlowBus(Arc<AtomicBool>);
    impl ErrorType for SlowBus {
        type Error = std::convert::Infallible;
    }
    impl I2c for SlowBus {
        fn transaction(&mut self, _: u8, _: &mut [Operation<'_>]) -> Result<(), Self::Error> {
            if !self.0.swap(true, Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(200));
            }
            Ok(())
        }
    }
    let entered = Arc::new(AtomicBool::new(false));
    let mut firmware = Firmware::start().unwrap();
    let start = std::time::Instant::now();
    let sensors = HallSensors::start(
        SlowBus(entered.clone()),
        &firmware.events(),
        HallTuning::DEFAULT,
    )
    .unwrap();
    while !entered.load(Ordering::SeqCst) {
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
}
