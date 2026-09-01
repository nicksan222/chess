use std::sync::Mutex;

use chess::{ChessMove, Game, MoveError, Square};
use logger::{Level, Logger, Record, register};

#[derive(Debug, Eq, PartialEq)]
struct Message {
    level: Level,
    target: String,
    text: String,
}

struct CaptureLogger {
    messages: Mutex<Vec<Message>>,
}

impl CaptureLogger {
    const fn new() -> Self {
        Self {
            messages: Mutex::new(Vec::new()),
        }
    }

    fn take(&self) -> Vec<Message> {
        std::mem::take(&mut *self.messages.lock().unwrap())
    }
}

impl Logger for CaptureLogger {
    fn log(&self, record: Record<'_>) {
        self.messages.lock().unwrap().push(Message {
            level: record.level(),
            target: record.target().to_owned(),
            text: record.arguments().to_string(),
        });
    }
}

static LOGGER: CaptureLogger = CaptureLogger::new();

#[test]
fn registered_logger_observes_the_complete_game_lifecycle() {
    assert!(logger::get().is_none());
    register(&LOGGER).unwrap();

    let mut game = Game::new();
    assert_eq!(LOGGER.take()[0].level, Level::Debug);

    let error = game
        .play(ChessMove::new(Square::E7, Square::E5))
        .unwrap_err();
    assert!(matches!(error, MoveError::WrongSide { .. }));

    let invalid = LOGGER.take();
    assert_eq!(invalid.len(), 1);
    assert_eq!(invalid[0].level, Level::Warn);
    assert_eq!(invalid[0].target, "chess::game");
    assert!(invalid[0].text.contains("WrongSide"));

    game.resolve_latest_invalid().unwrap();
    assert!(LOGGER.take()[0].text.contains("resolved invalid state"));

    game.play(ChessMove::new(Square::E2, Square::E4)).unwrap();
    assert_eq!(
        LOGGER.take(),
        [Message {
            level: Level::Info,
            target: "chess::game".to_owned(),
            text: "recorded move e2e4 at ply 1".to_owned(),
        }]
    );
}
