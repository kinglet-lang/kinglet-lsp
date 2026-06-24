#!/usr/bin/env python3
"""Open a .kl file two levels below its kinglet.nest and assert the LSP
resolves logical-name imports through nest walk-up.

Case directory layout:
    kinglet.nest
    <relative_path_to_target>.kl

The case is parameterized by:
    target_file  - relative path of the source file to didOpen (default
                   "lib/fmt/util.kl"). Required to be at least one
                   directory deep so this exercises the walk-up.

The test fails if publishDiagnostics for the opened file contains
"no kinglet.nest found".
"""
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


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <kinglet-lsp> <case-dir>", file=sys.stderr)
        return 2

    lsp_path = Path(sys.argv[1])
    case_dir = Path(sys.argv[2])

    # Discover target file: prefer explicit "target.txt" override, otherwise
    # default to lib/fmt/util.kl (mirrors the user's real bug report).
    target_marker = case_dir / "target.txt"
    if target_marker.exists():
        rel_target = target_marker.read_text(encoding="utf-8").strip()
    else:
        rel_target = "lib/fmt/util.kl"
    target = (case_dir / rel_target).resolve()
    if not target.exists():
        print(f"FAIL: target file missing: {target}", file=sys.stderr)
        return 2

    source = target.read_text(encoding="utf-8")
    uri = target.as_uri()

    proc = subprocess.Popen(
        [str(lsp_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin and proc.stdout
    diagnostics: list[dict] = []
    try:
        request(proc, 1, "initialize", {"processId": None, "rootUri": None, "capabilities": {}})
        notify(proc, "initialized", {})
        notify(
            proc,
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "kinglet",
                    "version": 1,
                    "text": source,
                }
            },
        )
        # Drain until we receive the diagnostics for our URI (or hit a hard
        # cap to avoid hanging if the server changes its protocol surface).
        for _ in range(50):
            message = read_message(proc.stdout)
            if message.get("method") == "textDocument/publishDiagnostics":
                params = message.get("params", {})
                if params.get("uri") == uri:
                    diagnostics = params.get("diagnostics", [])
                    break
    finally:
        try:
            request(proc, 99, "shutdown", None)
        except Exception:
            pass
        notify(proc, "exit", {})
        proc.terminate()
        proc.wait(timeout=5)

    nest_error = [
        d for d in diagnostics if "no kinglet.nest found" in d.get("message", "")
    ]
    if nest_error:
        print("FAIL: LSP did not discover kinglet.nest via walk-up.", file=sys.stderr)
        print(f"target file: {target}", file=sys.stderr)
        for d in nest_error:
            print(f"  diagnostic: {d.get('message')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
