#!/usr/bin/env python3
"""Exercise textDocument/didChange (Incremental sync) followed by formatting.

Each case directory contains:
    initial.kl   - the document text sent via didOpen
    edits.json   - a list of LSP TextDocumentContentChangeEvent dicts (with
                   `range` for ranged edits, or without it for a full replace).
                   Edits are applied in order via a single didChange.
    expected.kl  - the formatted output we require after the edits.
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


def path_to_uri(path: Path) -> str:
    return path.resolve().as_uri()


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <kinglet-lsp> <case-dir>", file=sys.stderr)
        return 2

    lsp_path = Path(sys.argv[1])
    case_dir = Path(sys.argv[2])
    initial_path = case_dir / "initial.kl"
    edits_path = case_dir / "edits.json"
    expected_path = case_dir / "expected.kl"

    initial = initial_path.read_text(encoding="utf-8")
    edits = json.loads(edits_path.read_text(encoding="utf-8"))
    expected = expected_path.read_text(encoding="utf-8")
    uri = path_to_uri(initial_path)

    proc = subprocess.Popen(
        [str(lsp_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin and proc.stdout

    try:
        caps = request(
            proc,
            1,
            "initialize",
            {"processId": None, "rootUri": None, "capabilities": {}},
        )
        capabilities = caps.get("capabilities", {})
        sync = capabilities.get("textDocumentSync", {})
        if isinstance(sync, dict):
            change_mode = sync.get("change")
        else:
            change_mode = sync
        if change_mode != 2:
            raise RuntimeError(
                f"expected Incremental sync (2), got textDocumentSync.change={change_mode!r}"
            )

        notify(proc, "initialized", {})
        notify(
            proc,
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "kinglet",
                    "version": 1,
                    "text": initial,
                }
            },
        )
        notify(
            proc,
            "textDocument/didChange",
            {
                "textDocument": {"uri": uri, "version": 2},
                "contentChanges": edits,
            },
        )
        result = request(
            proc,
            2,
            "textDocument/formatting",
            {
                "textDocument": {"uri": uri},
                "options": {"tabSize": 2, "insertSpaces": True},
            },
        )
    finally:
        try:
            request(proc, 99, "shutdown", None)
        except Exception:
            pass
        notify(proc, "exit", {})
        proc.terminate()
        proc.wait(timeout=5)

    if not isinstance(result, list) or len(result) != 1:
        raise RuntimeError(f"expected one TextEdit, got: {result!r}")
    formatted = result[0]["newText"]

    if formatted != expected:
        print("formatted output mismatch:", file=sys.stderr)
        print("--- expected ---", file=sys.stderr)
        print(expected, file=sys.stderr, end="")
        print("--- actual ---", file=sys.stderr)
        print(formatted, file=sys.stderr, end="")
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
