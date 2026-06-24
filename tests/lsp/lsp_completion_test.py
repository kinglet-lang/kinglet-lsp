#!/usr/bin/env python3
"""Drive textDocument/completion against kinglet-lsp.

Each case directory contains:
    request.json - {
        "target_file": str,    // relative path inside case-dir of the .kl
                               // file to didOpen (e.g. "lib/fmt/util.kl")
        "line": int,
        "character": int
    }
    expected.json - {"labels": [str, ...], "exclude": [str, ...]?}
                    `labels` is the required subset of result item labels
                    (order-independent); `exclude` is a list of labels that
                    MUST NOT appear in the result.
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
    request_spec = json.loads((case_dir / "request.json").read_text(encoding="utf-8"))
    expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))

    target_file = request_spec.get("target_file", "initial.kl")
    initial_path = (case_dir / target_file).resolve()
    if not initial_path.exists():
        print(f"FAIL: target file missing: {initial_path}", file=sys.stderr)
        return 2

    initial = initial_path.read_text(encoding="utf-8")
    uri = initial_path.as_uri()

    proc = subprocess.Popen(
        [str(lsp_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin and proc.stdout

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
                    "text": initial,
                }
            },
        )
        result = request(
            proc,
            2,
            "textDocument/completion",
            {
                "textDocument": {"uri": uri},
                "position": {
                    "line": request_spec["line"],
                    "character": request_spec["character"],
                },
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

    if isinstance(result, dict):
        items = result.get("items", [])
    else:
        items = result or []
    labels = {item.get("label") for item in items}

    failed = False
    for required in expected.get("labels", []):
        if required not in labels:
            print(f"FAIL: expected completion label {required!r} not in result", file=sys.stderr)
            failed = True
    for forbidden in expected.get("exclude", []):
        if forbidden in labels:
            print(f"FAIL: forbidden completion label {forbidden!r} appeared in result", file=sys.stderr)
            failed = True

    if failed:
        print("actual labels:", sorted(labels), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
