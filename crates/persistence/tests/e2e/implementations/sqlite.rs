mod failures;
mod journeys;
mod support;

use persistence::implementations::SqliteStore;

use crate::common::backend_contract_tests;

fn fresh_store() -> SqliteStore {
    SqliteStore::in_memory().expect("in-memory SQLite backend opens")
}

backend_contract_tests!(fresh_store);
