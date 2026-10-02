// "Build it" section: five steps, two languages, typewriter code reveal with light syntax tint.
(function () {
  const list = document.getElementById("buildSteps");
  if (!list) return;
  const out = document.getElementById("codeOut");
  const fileEl = document.getElementById("codeFile");
  const tabs = document.querySelectorAll(".tab");

  const steps = [
    { title: "Install the SDK", sub: "One dependency. The SDK handles JSON-RPC, transports, schemas.",
      py: { file: "terminal", code: `uv init my-server && cd my-server\nuv add "mcp[cli]"` },
      ts: { file: "terminal", code: `npm init -y\nnpm i @modelcontextprotocol/sdk zod\nnpm i -D typescript @types/node` } },
    { title: "Create the server", sub: "Name it. This shows up in the host as serverInfo.",
      py: { file: "server.py", code: `from mcp.server.fastmcp import FastMCP\n\nmcp = FastMCP("my-server")` },
      ts: { file: "src/index.ts", code: `import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";\nimport { z } from "zod";\n\nconst server = new McpServer({ name: "my-server", version: "0.1.0" });` } },
    { title: "Add a tool", sub: "Typed params become the JSON Schema. The docstring is what the model reads.",
      py: { file: "server.py", code: `@mcp.tool(annotations={"readOnlyHint": True})\ndef add(a: int, b: int) -> int:\n    """Add two integers. Use for exact arithmetic."""\n    return a + b` },
      ts: { file: "src/index.ts", code: `server.registerTool(\n  "add",\n  {\n    description: "Add two integers. Use for exact arithmetic.",\n    inputSchema: { a: z.number(), b: z.number() },\n    annotations: { readOnlyHint: true },\n  },\n  async ({ a, b }) => ({ content: [{ type: "text", text: String(a + b) }] })\n);` } },
    { title: "Add a resource and a prompt", sub: "Resources are GET-like data at a URI. Prompts are reusable templates.",
      py: { file: "server.py", code: `@mcp.resource("note://{key}")\ndef note(key: str) -> str:\n    """Read one note."""\n    return NOTES.get(key, "none")\n\n@mcp.prompt()\ndef review(code: str) -> str:\n    return f"Review this code, bugs first:\\n{code}"` },
      ts: { file: "src/index.ts", code: `server.registerResource(\n  "note", "note://{key}", { title: "Note" },\n  async (uri) => ({ contents: [{ uri: uri.href, text: notes.get(uri.host) ?? "none" }] })\n);\n\nserver.registerPrompt("review", { argsSchema: { code: z.string() } },\n  ({ code }) => ({ messages: [{ role: "user",\n    content: { type: "text", text: \`Review this code, bugs first:\\n\${code}\` } }] }));` } },
    { title: "Run and register", sub: "stdio by default. Inspect it, then add it to your host.",
      py: { file: "terminal", code: `# run on stdio\nuv run server.py\n\n# debug in a browser UI\nnpx @modelcontextprotocol/inspector uv run server.py\n\n# register with Claude Code\nclaude mcp add my-server -- uv run --directory /abs/path server.py` },
      ts: { file: "terminal", code: `# compile + run on stdio\nnpx tsc && node dist/index.js\n\n# debug in a browser UI\nnpx @modelcontextprotocol/inspector node dist/index.js\n\n# register with Claude Code\nclaude mcp add my-server -- node /abs/path/dist/index.js` } },
  ];

  let lang = "py", cur = 0, typing = null;

  function tint(src) {
    return src
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/(#.*|\/\/.*)$/gm, '<span class="c">$1</span>')
      .replace(/("[^"]*"|'[^']*'|`[^`]*`)/g, '<span class="s">$1</span>')
      .replace(/\b(from|import|def|return|const|async|await|export|new|server|mcp|uv|npm|npx|claude)\b/g, '<span class="k">$1</span>')
      .replace(/\b(FastMCP|McpServer|registerTool|registerResource|registerPrompt|tool|resource|prompt)\b/g, '<span class="f">$1</span>');
  }

  function render(idx) {
    cur = idx;
    [...list.children].forEach((li, j) => li.classList.toggle("active", j === idx));
    const s = steps[idx][lang];
    fileEl.textContent = s.file;
    clearInterval(typing);
    let n = 0;
    const src = s.code;
    typing = setInterval(() => {
      n = Math.min(src.length, n + 3);
      out.innerHTML = tint(src.slice(0, n)) + '<span class="caret"></span>';
      if (n >= src.length) clearInterval(typing);
    }, 12);
  }

  steps.forEach((s, idx) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="n">${idx + 1}</span><div><b>${s.title}</b><small>${s.sub}</small></div>`;
    li.addEventListener("click", () => render(idx));
    list.appendChild(li);
  });

  tabs.forEach(t => t.addEventListener("click", () => {
    tabs.forEach(x => { x.classList.remove("active"); x.setAttribute("aria-selected", "false"); });
    t.classList.add("active"); t.setAttribute("aria-selected", "true");
    lang = t.dataset.lang; render(cur);
  }));

  const io = new IntersectionObserver((ents) => {
    if (ents[0].isIntersecting) { io.disconnect(); render(0); }
  }, { threshold: .25 });
  io.observe(list);
})();
