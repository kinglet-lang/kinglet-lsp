# kinglet-lsp

C++ [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) implementation for [Kinglet](https://github.com/kinglet-lang/kinglet), plus the **Perch** VS Code extension (client only).

The server reuses the [bootstrap](https://github.com/kinglet-lang/bootstrap) compiler frontend (lexer, parser, checker, module loader). It does **not** live in the compiler repo.

## Layout

```
kinglet-lsp/
├── server/src/lsp/     # LSP protocol + analysis + completion
├── server/main.cc      # stdio entry point
├── client/             # VS Code extension (TypeScript)
├── third_party/bootstrap/  # git submodule (compiler frontend)
├── src/                # → third_party/bootstrap/src (symlink; GN deps //src/*)
├── build/              # GN config + bootstrap toolchain/config links
├── kinglet-lsp         # wrapper script → out/Default/kinglet-lsp
└── package.json        # VS Code extension manifest
```

## Build (server)

Requires [GN](https://gn.googlesource.com/gn/), ninja, and a C++20 toolchain (clang++).

```bash
# One-time: init bootstrap submodule + GN symlinks
bash scripts/setup-deps.sh   # macOS/Linux
# Windows PowerShell:
#   .\scripts\setup-deps.ps1

gn gen out/Default --args='is_debug=false'
ninja -C out/Default kinglet-lsp

./kinglet-lsp   # stdio LSP; VS Code / Perch spawn this
```

Windows (MSYS2 clang on PATH):

```powershell
gn gen out/Default --args='is_debug=false'
ninja -C out/Default kinglet-lsp
.\out\Default\kinglet-lsp.exe
```

## VS Code extension

```bash
npm install
npm run compile
```

### Option A — install from VSIX (recommended for daily use)

Build the LSP server, then package the extension. On Windows the VSIX bundles
`kinglet-lsp.exe` plus MinGW runtime DLLs (`libstdc++-6.dll`, `libgcc_s_seh-1.dll`)
so VS Code does not need MSYS2 on `PATH`.

```bash
ninja -C out/Default kinglet-lsp
npm run package
```

In VS Code: **Extensions** → `...` → **Install from VSIX…** → pick `kinglet-lsp-vscode-0.1.3.vsix`.

The client is **esbuild-bundled** into `out/extension.js` (includes `vscode-languageclient`).
Do not exclude `node_modules` from the VSIX without bundling — that leaves the extension stuck on **activating**.

No `kinglet.lspPath` setting is required when the VSIX includes the matching binary under `bin/`.

**Verify LSP is running**

1. Open a `.kl` file — bottom-right language mode should be **Kinglet** (not Plain Text).
2. Status bar (bottom-right) should show **Kinglet** with a checkmark when the server is up.
3. **Ctrl+Shift+P** → **Kinglet: Show Language Server Log** — opens the **Kinglet** output channel.
4. In **View → Output**, pick **Kinglet** from the dropdown (not “Perch”).
5. For RPC traces: `"kinglet.trace.server": "verbose"`.

### Option B — Extension Development Host (F5)

Press **F5** to launch the Extension Development Host. Set `kinglet.lspPath` to your built binary if it is not on `PATH`.

## LSP features

- Diagnostics (parser + type checker)
- Completion (parser-driven)
- Go to definition, hover, document symbols
- Signature help, semantic tokens

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `kinglet.lspPath` | `kinglet-lsp` | Language server binary |
| `kinglet.trace.server` | `off` | LSP trace level |

## License

MIT
