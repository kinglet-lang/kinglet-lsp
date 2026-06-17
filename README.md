<p align="center">
  <img src="image/icons/icon.svg" width="88" alt="Kinglet file icon (light themes)">
  &nbsp;&nbsp;
  <img src="image/icons/icon-dark.svg" width="88" alt="Kinglet file icon (dark themes)">
</p>

<p align="center">
  <a href="https://github.com/kinglet-lang/perch/blob/main/package.json">
    <img src="https://img.shields.io/github/package-json/v/kinglet-lang/perch?label=version&color=555" alt="version">
  </a>
  &nbsp;
  <a href="https://github.com/kinglet-lang/perch/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/kinglet-lang/perch" alt="license">
  </a>
</p>

<p align="center">Language support for <a href="https://github.com/kinglet-lang/kinglet">Kinglet</a> (<code>.kl</code>) — syntax highlighting and a fast, native language server.</p>

---

### Features

- **Diagnostics** — real-time parser and type-checker errors as you type
- **Completion** — context-aware, parser-driven suggestions
- **Go to Definition** — jump to where a symbol is declared
- **Hover** — types and documentation on hover
- **Document Symbols** — outline view and breadcrumbs
- **Signature Help** — parameter hints while you call functions
- **Semantic Tokens** — precise, type-aware highlighting
- **Syntax Highlighting** — TextMate grammar for `.kl` files

The language server is written in C++ and reuses the official Kinglet compiler
frontend, so diagnostics match the compiler exactly.

### Getting Started

1. Install the extension.
2. Open any `.kl` file — the language mode (bottom-right) switches to **Kinglet**.
3. The language server starts automatically; a **Perch** indicator appears in
   the status bar once it is up.

> Perch ships with a matching `kinglet-lsp` binary, so no extra setup is
> required on supported platforms. To use your own build, set `kinglet.lspPath`.

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `kinglet.lspPath` | `kinglet-lsp` | Path to the Kinglet language server binary. |
| `kinglet.trace.server` | `off` | LSP trace verbosity (`off`, `messages`, `verbose`). |

### Commands

| Command | Description |
|---------|-------------|
| **Perch: Show Language Server Log** | Open the Perch output channel. |
| **Perch: Restart Language Server** | Restart the Kinglet language server. |

### Troubleshooting

- **File opens as Plain Text** — set the language mode (bottom-right) to **Kinglet**,
  or ensure the file ends in `.kl`.
- **No diagnostics / completion** — run **Perch: Show Language Server Log** to
  check the server started. For detailed RPC traces, set
  `"kinglet.trace.server": "verbose"`.
- **Custom server** — point `kinglet.lspPath` at your own `kinglet-lsp` binary.

### Contributing

Building the language server from source, packaging the VSIX, and the repo
layout are documented in [CONTRIBUTING.md](https://github.com/kinglet-lang/perch/blob/main/CONTRIBUTING.md).
