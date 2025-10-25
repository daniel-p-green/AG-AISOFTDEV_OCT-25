#!/usr/bin/env python3
"""
Start a lightweight local web server and open the unified homepage.

Usage:
  python3 start_local.py            # serves on port 8000 by default
  python3 start_local.py --port 0   # chooses a free port automatically

This serves the repository root so the homepage and markdown overlay work
with same-origin requests.
"""
from __future__ import annotations

import argparse
import contextlib
import http.server
import os
import socket
import threading
import webbrowser


class NoCacheRequestHandler(http.server.SimpleHTTPRequestHandler):
    # Add simple no-cache headers to reduce confusion during iteration
    def end_headers(self) -> None:  # type: ignore[override]
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # quieter output
        print("[HTTP]", self.address_string(), "-", format % args)


def find_free_port(preferred: int) -> int:
    if preferred == 0:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]
    # try preferred, then scan a small range
    for p in [preferred] + list(range(8001, 8011)):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return 0


def serve(port: int) -> tuple[http.server.ThreadingHTTPServer, str]:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), NoCacheRequestHandler)
    url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
    return server, url


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the repo and open the homepage.")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on (0 chooses a free port)")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = find_free_port(args.port)
    httpd, url = serve(port)

    print(f"Serving at: http://127.0.0.1:{port}")
    print(f"Homepage:   {url}")

    # Start server in a background thread
    thread = threading.Thread(target=httpd.serve_forever, name="http-server", daemon=True)
    thread.start()

    try:
        # Open browser to the homepage
        webbrowser.open(url, new=2)
        # Block main thread while the server runs
        thread.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        httpd.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

