<p align="center">
  <img src="https://raw.githubusercontent.com/kinglet-lang/kinglet-lsp/main/image/icons/icon.png" width="128" alt="Kinglet">
</p>

<h1 align="center">Kinglet for VS Code</h1>

<p align="center">Language support for <a href="https://github.com/kinglet-lang/kinglet">Kinglet</a> (<code>.kl</code>) — syntax highlighting and a fast, native language server.</p>

---

## Features

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

## Getting Started

1. Install the extension.
2. Open any `.kl` file — the language mode (bottom-right) switches to **Kinglet**.
3. The language server starts automatically; a **Kinglet** indicator appears in
   the status bar once it is up.

> The extension ships with a matching `kinglet-lsp` binary, so no extra setup is
> required on supported platforms. To use your own build, set `kinglet.lspPath`.

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `kinglet.lspPath` | `kinglet-lsp` | Path to the language server binary. |
| `kinglet.trace.server` | `off` | LSP trace verbosity (`off`, `messages`, `verbose`). |

## Commands

| Command | Description |
|---------|-------------|
| **Kinglet: Show Language Server Log** | Open the Kinglet output channel. |
| **Kinglet: Restart Language Server** | Restart the language server. |

## Troubleshooting

- **File opens as Plain Text** — set the language mode (bottom-right) to **Kinglet**,
  or ensure the file ends in `.kl`.
- **No diagnostics / completion** — run **Kinglet: Show Language Server Log** to
  check the server started. For detailed RPC traces, set
  `"kinglet.trace.server": "verbose"`.
- **Custom server** — point `kinglet.lspPath` at your own `kinglet-lsp` binary.

## Contributing

Building the language server from source, packaging the VSIX, and the repo
layout are documented in [CONTRIBUTING.md](https://github.com/kinglet-lang/kinglet-lsp/blob/main/CONTRIBUTING.md).

## License

[MIT](https://github.com/kinglet-lang/kinglet-lsp/blob/main/LICENSE)
