//! A local stand-in for the release feed, shared by the firmware module's tests.

use std::{
    io::{Read, Write},
    net::TcpListener,
    sync::{Arc, Mutex},
    thread,
};

/// Serves one canned HTTP response on a local port and records each request.
pub(super) struct FakeFeed {
    pub(super) url: String,
    requests: Arc<Mutex<Vec<String>>>,
    // Keeps a silent feed's port open; answering feeds move theirs to a thread.
    _listener: Option<TcpListener>,
}

impl FakeFeed {
    /// Answers every request with `response`.
    pub(super) fn answering(response: String) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let url = format!("http://{}/releases/latest", listener.local_addr().unwrap());
        let requests = Arc::new(Mutex::new(Vec::new()));
        let recorded = requests.clone();
        thread::spawn(move || {
            for mut stream in listener.incoming().flatten() {
                let mut buffer = [0; 4096];
                // Preflight probes connect without sending a request.
                let read = stream.read(&mut buffer).unwrap_or(0);
                if read > 0 {
                    let request = String::from_utf8_lossy(&buffer[..read]).into_owned();
                    recorded.lock().unwrap().push(request);
                    let _ = stream.write_all(response.as_bytes());
                }
            }
        });
        Self {
            url,
            requests,
            _listener: None,
        }
    }

    /// Accepts connections but never answers, so a check stays in flight.
    pub(super) fn silent() -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        Self {
            url: format!("http://{}/releases/latest", listener.local_addr().unwrap()),
            requests: Arc::default(),
            _listener: Some(listener),
        }
    }

    /// The raw HTTP requests received so far.
    pub(super) fn requests(&self) -> Vec<String> {
        self.requests.lock().unwrap().clone()
    }
}

/// An HTTP response with `status` such as `"404 Not Found"`.
pub(super) fn answer(status: &str, body: &str) -> String {
    format!(
        "HTTP/1.1 {status}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
        body.len()
    )
}

/// A GitHub "latest release" answer for `tag`.
pub(super) fn release(tag: &str) -> String {
    answer(
        "200 OK",
        &format!(r#"{{"tag_name": "{tag}", "html_url": "https://example.invalid/{tag}"}}"#),
    )
}
