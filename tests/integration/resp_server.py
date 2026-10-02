"""Minimal RESP server (stdlib only) for live integration: supports exactly what
the platform needs: PING, SELECT, CLIENT, RPUSH, BLPOP (blocking), LLEN,
COMMAND. Anything else -> +OK. One thread per connection."""
import socket
import threading
import time


class MiniRedis:
    def __init__(self, host="127.0.0.1", port=6399):
        self.store = {}
        self.lock = threading.Lock()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, port))
        self._sock.listen(64)
        self._sock.settimeout(0.5)
        self._run = True

    def serve_forever(self):
        while self._run:
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def shutdown(self):
        self._run = False
        try:
            self._sock.close()
        except OSError:
            pass

    # ---- protocol ----
    def _readline(self, f):
        line = f.readline()
        if not line:
            raise ConnectionError("eof")
        return line

    def _handle(self, conn):
        try:
            f = conn.makefile("rb")
            while True:
                try:
                    line = self._readline(f)
                except ConnectionError:
                    return
                if not line.startswith(b"*"):
                    continue
                n = int(line[1:-2] or 0)
                args = []
                for _ in range(n):
                    h = self._readline(f)
                    ln = int(h[1:-2])
                    data = b""
                    while len(data) < ln + 2:
                        chunk = f.read(ln + 2 - len(data))
                        if not chunk:
                            raise ConnectionError("eof")
                        data += chunk
                    args.append(data[:ln].decode(errors="replace"))
                if not args:
                    continue
                self._command(conn, [a for a in args])
        except (ConnectionError, OSError, ValueError):
            return
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _send(self, conn, payload: bytes):
        conn.sendall(payload)

    def _command(self, conn, args):
        cmd = args[0].upper()
        if cmd == "PING":
            self._send(conn, b"+PONG\r\n" if len(args) == 1
                       else b"$" + str(len(args[1])).encode() + b"\r\n" + args[1].encode() + b"\r\n")
        elif cmd in ("SELECT", "CLIENT", "COMMAND", "QUIT", "RESET"):
            self._send(conn, b"+OK\r\n")
        elif cmd == "HELLO":
            proto = args[1] if len(args) > 1 else "2"
            body = (b"$6\r\nserver\r\n$5\r\nredis\r\n"
                    b"$7\r\nversion\r\n$5\r\n7.0.0\r\n"
                    b"$5\r\nproto\r\n:" + proto.encode() + b"\r\n"
                    b"$4\r\nmode\r\n$10\r\nstandalone\r\n")
            self._send(conn, b"%4\r\n" + body)
        elif cmd == "RPUSH":
            with self.lock:
                lst = self.store.setdefault(args[1], [])
                lst.extend(args[2:])
                n = len(lst)
            self._send(conn, b":" + str(n).encode() + b"\r\n")
        elif cmd == "LLEN":
            with self.lock:
                n = len(self.store.get(args[1], []))
            self._send(conn, b":" + str(n).encode() + b"\r\n")
        elif cmd in ("BLPOP", "BRPOP"):
            key, timeout = args[1], int(float(args[2])) if len(args) > 2 else 0
            deadline = time.time() + timeout if timeout else None
            while True:
                with self.lock:
                    lst = self.store.get(key, [])
                    if lst:
                        val = lst.pop(0)
                        kb, vb = key.encode(), val.encode()
                        self._send(conn, b"*2\r\n$" + str(len(kb)).encode() + b"\r\n" + kb +
                                   b"\r\n$" + str(len(vb)).encode() + b"\r\n" + vb + b"\r\n")
                        return
                if deadline and time.time() >= deadline:
                    self._send(conn, b"*-1\r\n")
                    return
                time.sleep(0.05)
        else:
            self._send(conn, b"+OK\r\n")
