"""Link availability checks and regressions for HTTP/PDF response validation."""

import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from pcb.harness.checks.datasheets import check_all, check_url, validate_response


class DatasheetsTest(unittest.TestCase):
    def test_access_challenge_without_a_title_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "access challenge"):
            validate_response(
                200,
                "text/html",
                b'<html><body><iframe src="/_Incapsula_Resource"></iframe></body></html>',
                pdf=False,
            )

    def test_missing_page_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTP 404"):
            validate_response(404, "text/html", b"Not found", pdf=False)

    def test_soft_not_found_page_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not found"):
            validate_response(
                200,
                "text/html",
                b"<html><title>Page not found</title></html>",
                pdf=False,
            )

    def test_pdf_endpoint_cannot_return_an_html_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "PDF"):
            validate_response(200, "text/html", b"<html>Access denied</html>", pdf=True)

    def test_pdf_signature_and_html_pages_are_accepted(self) -> None:
        validate_response(200, "application/pdf", b"%PDF-1.7\n", pdf=True)
        validate_response(
            200,
            "text/html",
            b"<html><title>Product datasheet</title></html>",
            pdf=False,
        )

    def test_empty_or_non_document_response_is_rejected(self) -> None:
        for body, content_type in ((b"", "application/pdf"), (b"random", "image/png")):
            with self.subTest(content_type=content_type), self.assertRaises(ValueError):
                validate_response(200, content_type, body, pdf=False)

    def test_invalid_or_credentialed_url_is_rejected(self) -> None:
        for url in (
            "",
            "file:///tmp/sheet.pdf",
            "https:///sheet.pdf",
            "http://user:secret@localhost/sheet.pdf",
        ):
            with (
                self.subTest(url=url),
                self.assertRaisesRegex(ValueError, "HTTP\\(S\\)|credentials"),
            ):
                check_url(url)

    def test_error_status_cannot_be_hidden_by_valid_pdf_content(self) -> None:
        for status in (403, 429, 500, 503):
            with (
                self.subTest(status=status),
                self.assertRaisesRegex(ValueError, f"HTTP {status}"),
            ):
                validate_response(status, "application/pdf", b"%PDF-1.7\n", pdf=True)

    def test_partial_pdf_response_is_accepted(self) -> None:
        validate_response(206, "application/pdf", b"%PDF-1.7\n", pdf=True)

    def test_html_content_type_without_html_content_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not an HTML document"):
            validate_response(200, "text/html", b"upstream error", pdf=False)

    def test_real_http_redirect_and_missing_response(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/sheet.pdf")
                    self.end_headers()
                elif self.path in (
                    "/loop",
                    "/no-location",
                    "/bad-scheme",
                    "/pdf-to-html.pdf",
                ):
                    self.send_response(302)
                    locations = {
                        "/loop": "/loop",
                        "/bad-scheme": "file:///tmp/sheet.pdf",
                        "/pdf-to-html.pdf": "/html",
                    }
                    if self.path in locations:
                        self.send_header("Location", locations[self.path])
                    self.end_headers()
                elif self.path == "/html":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><title>Product page</title></html>")
                elif self.path == "/sheet.pdf":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.end_headers()
                    self.wfile.write(b"%PDF-1.7\n")
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format: str, *args: object) -> None:
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            self.assertEqual(check_url(base + "/redirect"), base + "/sheet.pdf")
            with self.assertRaisesRegex(ValueError, "HTTP 404"):
                check_url(base + "/missing")
            for path, message in (
                ("/loop", "too many.*redirects"),
                ("/no-location", "no Location"),
                ("/bad-scheme", "HTTP\\(S\\)"),
                ("/pdf-to-html.pdf", "expected a PDF"),
            ):
                with (
                    self.subTest(path=path),
                    self.assertRaisesRegex(ValueError, message),
                ):
                    check_url(base + path)
            report = check_all(
                (
                    ("A", base + "/sheet.pdf"),
                    ("B", base + "/sheet.pdf"),
                    ("A", base + "/sheet.pdf"),
                    ("C", ""),
                    ("D", base + "/missing"),
                )
            )
            valid = [row for row in report if row.status == "valid"]
            self.assertEqual(len(valid), 1)
            self.assertEqual(valid[0].components, ("A", "B"))
            self.assertEqual(
                [row.components for row in report if row.status == "missing"], [("C",)]
            )
            self.assertEqual(
                [row.components for row in report if row.status == "failed"], [("D",)]
            )
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
