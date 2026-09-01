use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

use chess_core::{Percentage, Toggle};
use persistence::persistence_schema;

persistence_schema! {
    pub(crate) struct Settings {
        pub(crate) sound: Toggle = b"settings/sound",
        pub(crate) brightness: Percentage = b"settings/brightness",
        pub(crate) launches: u32 = b"statistics/launches",
        pub(crate) device_id: [u8; 8] = b"identity/device-id",
    }
}

static NEXT_DATABASE: AtomicU64 = AtomicU64::new(0);

pub(crate) struct DatabaseFile {
    path: PathBuf,
}

impl DatabaseFile {
    pub(crate) fn new(test_name: &str) -> Self {
        let sequence = NEXT_DATABASE.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "chess-persistence-{test_name}-{}-{sequence}.sqlite3",
            std::process::id()
        ));
        remove_sqlite_files(&path);
        Self { path }
    }

    pub(crate) fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for DatabaseFile {
    fn drop(&mut self) {
        remove_sqlite_files(&self.path);
    }
}

fn remove_sqlite_files(path: &Path) {
    let _ = fs::remove_file(path);
    let _ = fs::remove_file(format!("{}-wal", path.display()));
    let _ = fs::remove_file(format!("{}-shm", path.display()));
}
