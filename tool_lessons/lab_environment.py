"""Loopback services and synthetic captures for tool starter lessons."""

import base64
import hashlib
import http.server
from pathlib import Path
import socket
import socketserver
import sqlite3
import struct
import sys
import threading
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lessons"))
from lesson_support import Resources, write


PASSWORD = "LabPassword42"


class ToolResources(Resources):
    def __init__(self):
        super().__init__()
        self.requests = []
        self.auth_successes = 0
        self.database = None

    def web(self, token):
        resource = self
        self.database = sqlite3.connect(":memory:", check_same_thread=False)
        self.database.executescript("CREATE TABLE products(id INTEGER, name TEXT); INSERT INTO products VALUES(1,'Notebook'),(2,'Pencil'),(3,'Eraser');")
        lock = threading.Lock()
        class Handler(http.server.BaseHTTPRequestHandler):
            server_version = "TerminalToolLab/1.0"
            sys_version = ""

            def respond(self, status, body, extras=None):
                body = body.encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("X-Tool-Lab", token)
                for key, value in (extras or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                if self.command != "HEAD":
                    try:
                        self.wfile.write(body)
                    except (BrokenPipeError, ConnectionResetError):
                        pass

            def do_HEAD(self):
                self.do_GET()

            def do_GET(self):
                resource.requests.append(self.path)
                parsed = urlsplit(self.path)
                query = parse_qs(parsed.query)
                if parsed.path == "/protected":
                    expected = "Basic " + base64.b64encode(("trainee:" + PASSWORD).encode()).decode()
                    if self.headers.get("Authorization") != expected:
                        return self.respond(401, "Authentication required\n", {"WWW-Authenticate": 'Basic realm="Terminal lesson"'})
                    resource.auth_successes += 1
                    return self.respond(200, "Training login accepted\n")
                if parsed.path in ("/item", "/safe-item"):
                    value = query.get("id", ["1"])[0]
                    try:
                        with lock:
                            if parsed.path == "/item":
                                # Deliberately injectable, in-memory, fictional data.
                                result = resource.database.execute("SELECT name FROM products WHERE id=" + value).fetchall()
                            else:
                                result = resource.database.execute("SELECT name FROM products WHERE id=?", (value,)).fetchall()
                        return self.respond(200, "\n".join(row[0] for row in result) + "\n")
                    except sqlite3.Error:
                        return self.respond(400, "Training SQL error\n")
                if parsed.path == "/hello":
                    return self.respond(200, "Hello " + query.get("name", ["reader"])[0] + "\n")
                if parsed.path == "/robots.txt":
                    return self.respond(200, "User-agent: *\nDisallow: /training-admin/\n")
                if parsed.path in ("/", "/training-admin/"):
                    return self.respond(200, "Tool practice server\nCase code: " + token + "\n")
                self.respond(404, "Not found\n")

            def log_message(self, *args):
                pass

        class LocalServer(http.server.ThreadingHTTPServer):
            def server_bind(self):
                socketserver.TCPServer.server_bind(self)
                self.server_name = "localhost"
                self.server_port = self.server_address[1]

        self.server = LocalServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.port

    def banner(self, token):
        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.sendall(("TRAINING " + token + "\n").encode())
        self.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.port

    def close(self):
        super().close()
        if self.database:
            self.database.close()
            self.database = None


def checksum(data):
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack("!{}H".format(len(data) // 2), data))
    while total >> 16:
        total = (total & 65535) + (total >> 16)
    return (~total) & 65535


def http_capture(path):
    """Write a real PCAP container with two synthetic Ethernet/IPv4/TCP frames."""
    client, server = socket.inet_aton("192.0.2.10"), socket.inet_aton("192.0.2.20")
    request = b"GET /hello?name=reader HTTP/1.1\r\nHost: lab.invalid\r\n\r\n"
    response = b"HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello reader\n"
    def packet(src, dst, sport, dport, seq, ack, payload):
        tcp = struct.pack("!HHIIBBHHH", sport, dport, seq, ack, 0x50, 0x18, 8192, 0, 0)
        pseudo = src + dst + struct.pack("!BBH", 0, 6, len(tcp) + len(payload))
        tcp = tcp[:16] + struct.pack("!H", checksum(pseudo + tcp + payload)) + tcp[18:]
        ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 40 + len(payload), 1, 0, 64, 6, 0, src, dst)
        ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
        return b"\x02\x00\x00\x00\x00\x02\x02\x00\x00\x00\x00\x01\x08\x00" + ip + tcp + payload
    frames = [packet(client, server, 45000, 80, 1, 1, request),
              packet(server, client, 80, 45000, 1, len(request) + 1, response)]
    data = struct.pack("<IHHIIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
    for index, frame in enumerate(frames):
        data += struct.pack("<IIII", 1700000000 + index, 0, len(frame), len(frame)) + frame
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def make_common(root, slug, token):
    (root / "fixtures").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    write(root / "fixtures/scope.txt", "Tool: {}\nCase code: {}\nScope: generated files and the loopback targets printed by this instructor\n".format(slug, token))
    write(root / "fixtures/words.txt", "wrong-one\n" + PASSWORD + "\nwrong-two\n")
    write(root / "fixtures/hash.txt", "trainee:" + hashlib.md5(PASSWORD.encode()).hexdigest() + "\n")
