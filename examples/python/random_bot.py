#!/usr/bin/env python3
"""A minimal bot for the WotR Bot Protocol (draft 0.1): it answers every decision with a random legal option.

A template for other authors: Python 3.8+, the standard library only, no other file needed.

Two ways to connect:

  Local, as the referee's child process (stdin and stdout carry the protocol, stderr is a log): a referee starts
      python3 random_bot.py

  Remote, dialling a referee's WebSocket with a token (in the URL, or with --token in the hello):
      python3 random_bot.py --connect wss://wotr.behindmedia.com/referee --token YOUR-TOKEN
      python3 random_bot.py --connect "ws://localhost:8765/referee?token=YOUR-TOKEN"

Options: --seed S (this bot's own generator; otherwise each game's seed_bot), --name NAME, --events (ask for the event
stream, printed to stderr with --verbose).

Every message is one JSON object; the referee asks, the bot answers with the same "id". The bot never needs the
rules: each "decide" carries the view of the position and the closed list of options, and the answer is an option's
"o". Option 0 is always legal. See SPEC.md for the messages and vocabulary/ for the names.
"""

import argparse
import base64
import json
import os
import random
import socket
import ssl
import struct
import sys
from urllib.parse import urlparse

PROTOCOL = "wotr-bot/0.1"


def log(*args):
    print(*args, file=sys.stderr, flush=True)


class Bot:
    """The bot's logic: everything a bot author would replace is in decide()."""

    def __init__(self, name, seed=None, events=False, verbose=False, token=None):
        self.name = name
        self.fixed_seed = seed
        self.events = events
        self.verbose = verbose
        self.token = token
        self.rng = random.Random(seed)
        self.side = None
        self.score = {"games": 0, "won": 0}

    def handle(self, message):
        """The answer to one message from the referee (a dict), or None. Raises SystemExit on quit."""
        kind = message.get("type")
        if kind == "hello":
            answer = {"type": "hello", "id": message.get("id"), "protocol": PROTOCOL, "name": self.name,
                      "version": "1.0", "author": "example", "events": self.events, "options": []}
            if self.token:
                answer["token"] = self.token
            return answer
        if kind == "new_game":
            self.side = message.get("side")
            log("game", self.score["games"] + 1, "started:", message.get("game"), "as", self.side)
            if self.fixed_seed is None:
                self.rng = random.Random(message.get("seed_bot"))
            return {"type": "ready", "id": message.get("id")}
        if kind == "decide":
            return self.decide(message)
        if kind == "event":
            if self.verbose:
                log("event", message.get("seq"), json.dumps(message.get("event")))
            return None
        if kind == "game_over":
            log("game over:", message.get("winner"), message.get("how"), "turn", message.get("turn"), "(I played", self.side + ")")
            self.score["games"] += 1
            self.score["won"] += message.get("winner") == self.side
            return None
        if kind == "quit":
            log("match over: won", self.score["won"], "of", self.score["games"])
            raise SystemExit(0)
        if kind in ("options", "timeout", "error"):
            if kind != "options":
                log("referee:", json.dumps(message))
            return None
        # Unknown messages with an id get an error; others are ignored (section 2).
        if "id" in message:
            return {"type": "error", "id": message["id"], "code": "unknown_type"}
        return None

    def decide(self, message):
        decision = message["decision"]
        options = decision["options"]
        # A real bot reads message["view"] (the position as this side knows it) and the options' fields here.
        choice = self.rng.choice(options)
        if self.verbose:
            log("decide", decision.get("kind"), "->", choice.get("text") or choice.get("kind"), "of", len(options))
        return {"type": "choice", "id": message["id"], "o": choice["o"], "fingerprint": decision.get("fingerprint"),
                "info": {"picked": choice.get("kind")}}


def run_stdio(bot):
    """The protocol over stdin and stdout: one JSON object per line."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            log("not JSON:", line[:200])
            continue
        answer = bot.handle(message)
        if answer is not None:
            sys.stdout.write(json.dumps(answer, separators=(",", ":")) + "\n")
            sys.stdout.flush()


class WebSocket:
    """A small WebSocket client (RFC 6455) on the standard library: text messages, ping/pong, close."""

    def __init__(self, url):
        parts = urlparse(url)
        secure = parts.scheme == "wss"
        port = parts.port or (443 if secure else 80)
        raw = socket.create_connection((parts.hostname, port))
        self.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=parts.hostname) if secure else raw
        key = base64.b64encode(os.urandom(16)).decode()
        path = (parts.path or "/") + ("?" + parts.query if parts.query else "")
        host = parts.hostname + ("" if parts.port is None else ":%d" % parts.port)
        request = ("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                   "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n") % (path, host, key)
        self.sock.sendall(request.encode())
        self.buffer = b""
        header = self._read_until(b"\r\n\r\n").decode("latin-1")
        if " 101 " not in header.split("\r\n")[0]:
            raise RuntimeError("the referee refused the connection: " + header.split("\r\n")[0])

    def _read(self, n):
        while len(self.buffer) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError("connection closed")
            self.buffer += chunk
        data, self.buffer = self.buffer[:n], self.buffer[n:]
        return data

    def _read_until(self, marker):
        while marker not in self.buffer:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError("connection closed")
            self.buffer += chunk
        index = self.buffer.index(marker) + len(marker)
        data, self.buffer = self.buffer[:index], self.buffer[index:]
        return data

    def _frame(self, opcode, payload):
        header = bytes([0x80 | opcode])
        n = len(payload)
        if n < 126:
            header += bytes([0x80 | n])
        elif n < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)  # A client masks every frame.
        self.sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def send(self, text):
        self._frame(0x1, text.encode("utf-8"))

    def receive(self):
        """The next text message, or None once the referee closed the connection."""
        message = b""
        while True:
            b0, b1 = self._read(2)
            opcode, n = b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            mask = self._read(4) if b1 & 0x80 else None
            payload = self._read(n)
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            if opcode == 0x8:
                return None
            if opcode == 0x9:
                self._frame(0xA, payload)
                continue
            if opcode in (0x0, 0x1):
                message += payload
                if b0 & 0x80:
                    return message.decode("utf-8")

    def close(self):
        try:
            self._frame(0x8, struct.pack(">H", 1000))
            self.sock.close()
        except OSError:
            pass


def run_websocket(bot, url):
    """The protocol over a WebSocket the bot dials: one JSON message per frame; the referee speaks first."""
    ws = WebSocket(url)
    try:
        while True:
            text = ws.receive()
            if text is None:
                log("the referee closed the connection")
                return
            for line in text.splitlines():
                if line.strip():
                    answer = bot.handle(json.loads(line))
                    if answer is not None:
                        ws.send(json.dumps(answer, separators=(",", ":")))
    except SystemExit:
        pass
    finally:
        ws.close()


def main():
    parser = argparse.ArgumentParser(description="A random bot for the WotR Bot Protocol (draft 0.1).")
    parser.add_argument("--connect", help="a referee's WebSocket URL (ws:// or wss://); default: stdin and stdout")
    parser.add_argument("--token", help="the token for a remote referee (also possible as ?token= in the URL)")
    parser.add_argument("--seed", type=int, help="this bot's own seed (default: each game's seed_bot)")
    parser.add_argument("--name", default="random-example")
    parser.add_argument("--events", action="store_true", help="ask for the event stream")
    parser.add_argument("--verbose", action="store_true", help="print each decision and the events to stderr (asks for events)")
    args = parser.parse_args()
    bot = Bot(args.name, args.seed, args.events or args.verbose, args.verbose, args.token)
    if args.connect:
        run_websocket(bot, args.connect)
    else:
        try:
            run_stdio(bot)
        except SystemExit:
            pass


if __name__ == "__main__":
    main()
