#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/out/Default/kinglet-lsp" ]]; then
  LSP="$ROOT/out/Default/kinglet-lsp"
elif [[ -x "$ROOT/out/Debug/kinglet-lsp" ]]; then
  LSP="$ROOT/out/Debug/kinglet-lsp"
else
  echo "kinglet-lsp not built; run: gn gen out/Default && ninja -C out/Default kinglet-lsp formatting_test" >&2
  exit 1
fi

if [[ ! -x "$ROOT/out/Default/formatting_test" && ! -x "$ROOT/out/Debug/formatting_test" ]]; then
  echo "formatting_test not built; run: ninja -C out/Default formatting_test" >&2
  exit 1
fi

if [[ -x "$ROOT/out/Default/formatting_test" ]]; then
  TEST_BIN="$ROOT/out/Default/formatting_test"
else
  TEST_BIN="$ROOT/out/Debug/formatting_test"
fi

echo "==> unit: formatting_test"
"$TEST_BIN" "$ROOT"

echo "==> integration: lsp formatting"
python3 "$ROOT/tests/lsp/lsp_formatting_test.py" "$LSP" "$ROOT/tests/lsp/cases/basic_spacing"
python3 "$ROOT/tests/lsp/lsp_formatting_test.py" "$LSP" "$ROOT/tests/lsp/cases/project_config"
python3 "$ROOT/tests/lsp/lsp_formatting_test.py" "$LSP" "$ROOT/tests/lsp/cases/preserve_blank_and_cast"

echo "==> integration: lsp incremental didChange"
python3 "$ROOT/tests/lsp/lsp_incremental_test.py" "$LSP" "$ROOT/tests/lsp/cases/incremental_ascii"
python3 "$ROOT/tests/lsp/lsp_incremental_test.py" "$LSP" "$ROOT/tests/lsp/cases/incremental_utf16"

echo "==> integration: lsp nest walk-up"
python3 "$ROOT/tests/lsp/lsp_nest_walkup_test.py" "$LSP" "$ROOT/tests/lsp/cases/nest_walkup"

echo "==> integration: lsp nest diagnostics"
python3 "$ROOT/tests/lsp/lsp_nest_diagnostic_test.py" "$LSP" "$ROOT/tests/lsp/cases/nest_diag_dirty"
python3 "$ROOT/tests/lsp/lsp_nest_diagnostic_test.py" "$LSP" "$ROOT/tests/lsp/cases/nest_diag_clean"

echo "==> integration: lsp import completion"
python3 "$ROOT/tests/lsp/lsp_completion_test.py" "$LSP" "$ROOT/tests/lsp/cases/completion_import_prefix"
python3 "$ROOT/tests/lsp/lsp_completion_test.py" "$LSP" "$ROOT/tests/lsp/cases/completion_import_mid_prefix"
python3 "$ROOT/tests/lsp/lsp_completion_test.py" "$LSP" "$ROOT/tests/lsp/cases/completion_import_empty"
python3 "$ROOT/tests/lsp/lsp_completion_test.py" "$LSP" "$ROOT/tests/lsp/cases/completion_namespace_access"

echo "==> integration: lsp nest completion"
python3 "$ROOT/tests/lsp/lsp_completion_test.py" "$LSP" "$ROOT/tests/lsp/cases/nest_complete_modules"
python3 "$ROOT/tests/lsp/lsp_completion_test.py" "$LSP" "$ROOT/tests/lsp/cases/nest_complete_targets"
python3 "$ROOT/tests/lsp/lsp_completion_test.py" "$LSP" "$ROOT/tests/lsp/cases/nest_complete_build_default"

echo "All LSP formatting tests passed."
