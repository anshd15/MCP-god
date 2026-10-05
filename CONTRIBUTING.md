# Contributing

This is a personal study repo, but it follows real-project hygiene so the habits stick.

## Commit rules

- One topic per commit. A commit that touches docs and code for different reasons gets split.
- Prefix: `docs:`, `site:`, `agent:`, `examples:`, `chore:`, `ci:`.
- Subject line under 72 characters, imperative mood ("add", not "added").
- Line endings are LF. `.gitattributes` enforces it; on Windows write files with `newline="\n"`.

## Docs

- Guides live in `docs/` and are numbered. New guides take the next number.
- Every guide has numbered subsections (`## 3.2`) so they can be cited from elsewhere.
- Prefer tables for comparisons and fenced blocks for anything the reader would copy.

## Code

- `examples/` targets the current `mcp` 2.x Python SDK and the `@modelcontextprotocol/sdk` TypeScript SDK.
- `agent/` has its own tests. Run them before committing:

```bash
cd agent && uv run pytest -q
```

## Site

- `site/` is static. No build step. Keep it that way.
- Colors come from tokens on `:root`; never hard-code a hex in a component.
- Every animation must respect `prefers-reduced-motion`.

## Deploy

```bash
npx vercel --prod
```
