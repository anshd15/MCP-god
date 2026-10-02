# site/

The animated companion page for MCP-god. Pure static HTML, CSS, and vanilla JS. No build step.

## Sections

| Section | What it animates |
|---|---|
| Data flow | JSON-RPC packets moving Host → Client → Server and back, with a live message ticker |
| Lifecycle | The ten-step session handshake, auto-playing with a direction arrow between Client and Server lanes |
| Build it | Five steps to a custom server, Python and TypeScript tabs, typewriter code reveal |
| Primitives | Six cards: tools, resources, prompts, sampling, roots, elicitation |
| Transports | stdio vs Streamable HTTP packet pipes |

## Run locally

Any static server works:

```bash
npx serve site
```

## Deploy

The repo root has a `vercel.json` that points `outputDirectory` at this folder.

```bash
vercel --prod
```

## Files

- `index.html` markup and inline SVG diagram
- `styles.css` tokens (dark and light), layout, keyframes
- `js/flow.js` packet animation along SVG paths
- `js/lifecycle.js` handshake stepper
- `js/steps.js` build-guide stepper with typewriter
- `js/main.js` scroll reveal and theme toggle
