/**
 * Minimal MCP server in TypeScript.
 *
 * Build: npm install && npm run build
 * Run:   node dist/index.js            (stdio)
 * Test:  npx @modelcontextprotocol/inspector node dist/index.js
 * Add:   claude mcp add mcp-god-ts -- node <abs path>/dist/index.js
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "mcp-god-typescript", version: "0.1.0" });

const notes = new Map<string, string>();

server.registerTool(
  "now",
  {
    title: "Current time",
    description: "Current UTC time in ISO 8601. Use when the user asks the time or date.",
    inputSchema: {},
    annotations: { readOnlyHint: true },
  },
  async () => ({ content: [{ type: "text", text: new Date().toISOString() }] })
);

server.registerTool(
  "add",
  {
    title: "Add",
    description: "Add two numbers exactly. Use instead of mental arithmetic.",
    inputSchema: { a: z.number(), b: z.number() },
  },
  async ({ a, b }) => ({ content: [{ type: "text", text: String(a + b) }] })
);

server.registerTool(
  "save_note",
  {
    title: "Save note",
    description: "Save a short note under a key. Overwrites if the key exists.",
    inputSchema: { key: z.string().min(1), text: z.string() },
    annotations: { idempotentHint: true },
  },
  async ({ key, text }) => {
    notes.set(key, text);
    return { content: [{ type: "text", text: `saved "${key}" (${text.length} chars)` }] };
  }
);

server.registerTool(
  "list_notes",
  {
    title: "List notes",
    description: "List saved note keys.",
    inputSchema: {},
    annotations: { readOnlyHint: true },
  },
  async () => ({
    content: [{ type: "text", text: [...notes.keys()].sort().join("\n") || "(no notes)" }],
  })
);

server.registerResource(
  "note",
  "note://{key}",
  { title: "Note", description: "Read one note by key" },
  async (uri) => {
    const key = uri.host;
    return { contents: [{ uri: uri.href, text: notes.get(key) ?? `no note named "${key}"` }] };
  }
);

server.registerPrompt(
  "summarize_notes",
  { title: "Summarise notes", description: "Ask the model to summarise all saved notes" },
  () => {
    const body = [...notes.entries()]
      .sort()
      .map(([k, v]) => `## ${k}\n${v}`)
      .join("\n\n");
    return {
      messages: [
        {
          role: "user",
          content: { type: "text", text: `Summarise these notes in three bullets:\n\n${body || "(empty)"}` },
        },
      ],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("mcp-god-typescript ready on stdio");
