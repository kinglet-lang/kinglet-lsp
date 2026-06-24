#!/usr/bin/env python3
"""Stress-test completion: probe many cursor positions across typical .kl
source shapes and assert the server never returns zero items (which would
indicate a missing set_completion() in the parser)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def read_message(stream) -> dict:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            raise EOFError("LSP server closed stdout")
        line = line.decode("utf-8").strip()
        if not line:
            break
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    length = int(headers["content-length"])
    body = stream.read(length)
    if not body:
        raise EOFError("empty LSP message body")
    return json.loads(body.decode("utf-8"))


def write_message(stream, payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    stream.write(header + body)
    stream.flush()


def request(proc, req_id: int, method: str, params) -> dict:
    write_message(
        proc.stdin,
        {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params},
    )
    while True:
        message = read_message(proc.stdout)
        if message.get("id") == req_id:
            if "error" in message:
                raise RuntimeError(f"{method} failed: {message['error']}")
            return message["result"]


def notify(proc, method: str, params: dict) -> None:
    write_message(proc.stdin, {"jsonrpc": "2.0", "method": method, "params": params})


# Probe points: (line, character) pairs across different code shapes.
# Each key names a shape; values are (src, [(line, char), ...]) tuples.
PROBES = [
    # ── top-level shapes ──
    ("top-level empty line",
     "using io;\nint x = 1;\n\n",
     [(2, 0)]),
    ("top-level after using",
     "using io;\nint x;\n\n",
     [(1, 0)]),
    ("top-level after fn decl",
     "int f() { return 0; }\n\n",
     [(1, 0)]),

    # ── inside function body ──
    ("fn body start",
     "int main() {\n  \n  return 0;\n}\n",
     [(1, 2)]),
    ("fn body after stmt",
     "int main() {\n  int x = 1;\n  \n  return 0;\n}\n",
     [(2, 2)]),
    ("fn body middle block",
     "int main() {\n  if (true) {\n    \n  }\n  return 0;\n}\n",
     [(2, 4)]),

    # ── after expression (before ';') ──
    ("match no semicolon",
     "int main() {\n  int x = 42;\n  x match { _ => 0 }\n  \n}\n",
     [(3, 2)]),

    # ── struct literal ──
    ("struct literal field",
     "struct S { int a; }\nint main() {\n  S s { \n  return 0;\n}\n",
     [(3, 9)]),

    # ── namespace access ──
    ("namespace access",
     "using io;\nint main() {\n  io::\n  return 0;\n}\n",
     [(2, 5)]),

    # ── return expression ──
    ("return expr",
     "int main() {\n  return \n}\n",
     [(1, 9)]),

    # ── type position (fn return) ──
    ("fn return type",
     "  int main() {\n    return 0;\n  }\n}\n",
     [(0, 2)]),

    # ── map literal key ──
    ("map literal",
     "int main() {\n  {string: int} m = { \n  return 0;\n}\n",
     [(2, 22)]),
]


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <kinglet-lsp>", file=sys.stderr)
        return 2

    lsp_path = Path(sys.argv[1])

    failed = 0
    for label, source, positions in PROBES:
        proc = subprocess.Popen(
            [str(lsp_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert proc.stdin and proc.stdout

        try:
            request(proc, 1, "initialize",
                    {"processId": None, "rootUri": None, "capabilities": {}})
            notify(proc, "initialized", {})
            notify(proc, "textDocument/didOpen",
                   {"textDocument": {"uri": "file:///st.kl",
                                     "languageId": "kinglet",
                                     "version": 1,
                                     "text": source}})

            for nid, (line, char) in enumerate(positions):
                result = request(
                    proc, 2 + nid, "textDocument/completion",
                    {"textDocument": {"uri": "file:///st.kl"},
                     "position": {"line": line, "character": char}},
                )
                if isinstance(result, dict):
                    items = result.get("items", [])
                else:
                    items = result or []
                if len(items) == 0:
                    print(f"FAIL [{label}] line={line} char={char}: 0 items",
                          file=sys.stderr)
                    failed += 1
        finally:
            try:
                request(proc, 99, "shutdown", None)
            except Exception:
                pass
            notify(proc, "exit", {})
            proc.terminate()
            proc.wait(timeout=5)

    if failed:
        print(f"\n{failed} stress probe(s) failed (returned no candidates).",
              file=sys.stderr)
        return 1
    print(f"All {sum(len(ps) for _, _, ps in PROBES)} probes passed across {len(PROBES)} shapes.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
