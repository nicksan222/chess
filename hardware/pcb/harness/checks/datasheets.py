"""Check recorded datasheet URLs without mistaking HTTP errors for documents.

A live link does not establish that the document is correct for the selected
part. Missing URLs are reported separately from dead or inaccessible links.
"""

from __future__ import annotations

import http.client
import re
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit


@dataclass(frozen=True, slots=True)
class DatasheetResult:
    components: tuple[str, ...]
    reference: str
    status: str
    detail: str


def validate_response(
    status: int, content_type: str, body: bytes, *, pdf: bool
) -> None:
    """Reject error statuses, empty responses, false PDFs and soft-404 titles."""
    if status not in (200, 206):
        raise ValueError(f"HTTP {status}")
    if not body.strip():
        raise ValueError("empty document response")
    if pdf or "application/pdf" in content_type:
        if not body.lstrip().startswith(b"%PDF-"):
            raise ValueError("expected a PDF document, received another response")
        return
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise ValueError(f"unexpected document content type: {content_type}")
    html = body.decode("utf-8", errors="replace")
    if not re.search(r"<(?:html|!doctype|head|body)\b", html, re.IGNORECASE):
        raise ValueError("response is not an HTML document")
    if re.search(
        r"_Incapsula_Resource|Request unsuccessful|cf-chl-|challenge-platform",
        html,
        re.IGNORECASE,
    ):
        raise ValueError("document page returned an access challenge")
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title and re.search(
        r"404|not found|access denied|just a moment|attention required",
        title[1],
        re.IGNORECASE,
    ):
        raise ValueError(f"document page unavailable: {title[1].strip()}")


def check_url(url: str, *, timeout_seconds: float = 8) -> str:
    """GET at most 64 KiB, follow up to four redirects, and return the final URL."""
    current = url
    for _ in range(5):
        parsed = urlsplit(current)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("datasheet needs an HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("datasheet URL must not contain credentials")
        connection_type = (
            http.client.HTTPSConnection
            if parsed.scheme == "https"
            else http.client.HTTPConnection
        )
        connection = connection_type(
            parsed.hostname, parsed.port, timeout=timeout_seconds
        )
        try:
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            connection.request(
                "GET",
                path,
                headers={
                    "User-Agent": "Chess-Datasheet-Check/1.0",
                    "Accept": "application/pdf,text/html,application/xhtml+xml",
                },
            )
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not location:
                    raise ValueError("redirect has no Location")
                current = urljoin(current, location)
                continue
            validate_response(
                response.status,
                response.getheader("Content-Type") or "",
                response.read(65536),
                pdf=parsed.path.lower().endswith(".pdf")
                or urlsplit(url).path.lower().endswith(".pdf"),
            )
            return current
        finally:
            connection.close()
    raise ValueError("too many datasheet redirects")


def check_all(references: Iterable[tuple[str, str]]) -> tuple[DatasheetResult, ...]:
    """Check each unique URL once and identify every component using it."""
    urls: dict[str, list[str]] = {}
    missing: list[DatasheetResult] = []
    for component, reference in references:
        parsed = urlsplit(reference)
        if parsed.scheme in ("http", "https") and parsed.hostname:
            keys = urls.setdefault(reference, [])
            if component not in keys:
                keys.append(component)
        else:
            missing.append(
                DatasheetResult(
                    (component,), reference, "missing", "no datasheet URL recorded"
                )
            )

    def check(reference: str) -> DatasheetResult:
        components = tuple(urls[reference])
        try:
            final_url = check_url(reference)
        except (OSError, ValueError, http.client.HTTPException) as error:
            return DatasheetResult(components, reference, "failed", str(error))
        return DatasheetResult(components, reference, "valid", final_url)

    with ThreadPoolExecutor(max_workers=8) as executor:
        checked = tuple(executor.map(check, sorted(urls)))
    return checked + tuple(missing)


def main() -> int:
    """Print an audit; missing or unverified references cause a nonzero exit."""
    from .catalog import datasheet_references

    report = check_all(datasheet_references())
    for row in report:
        print(f"{row.status}: {', '.join(row.components)}: {row.detail}")
    print(
        f"Datasheets: {sum(row.status == 'valid' for row in report)} valid URLs; {sum(row.status == 'failed' for row in report)} failed URLs; {sum(row.status == 'missing' for row in report)} components missing URLs"
    )
    return int(any(row.status != "valid" for row in report))


if __name__ == "__main__":
    raise SystemExit(main())
