"""Serve the project root over HTTP for BrowserUse (file:// is blocked by browser_use security policy)."""

from __future__ import annotations

import socketserver
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

from src.utils.io import project_root


class _ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def _make_handler_class(root: Path) -> type[SimpleHTTPRequestHandler]:
    root_resolved = str(root.resolve())

    class _ProjectRootHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root_resolved, **kwargs)

        def log_message(self, _format: str, *_args) -> None:
            return

    return _ProjectRootHandler


@contextmanager
def serve_project_root(root: Path | None = None) -> Iterator[str]:
    """Bind 127.0.0.1 on a free port; serve ``root`` (default: repo root). Yields base URL ``http://127.0.0.1:<port>``."""
    root = root or project_root()
    handler = _make_handler_class(root)
    httpd = _ReuseAddrTCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=15)
