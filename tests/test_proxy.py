import sys
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app


class ProxyTestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/video":
            body = b"proxy-test-bytes"
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def test_proxy_stream_serves_upstream_content():
    server = HTTPServer(("127.0.0.1", 0), ProxyTestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with TestClient(app) as client:
            response = client.get("/proxy/stream", params={"url": f"http://127.0.0.1:{port}/video"})

        assert response.status_code == 200
        assert response.content == b"proxy-test-bytes"
        assert response.headers["content-type"].startswith("video/mp4")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
