# 03 - Primitives (the six things MCP can express)

Server-side primitives: **Tools**, **Resources**, **Prompts**.
Client-side primitives: **Sampling**, **Roots**, **Elicitation**.

A useful lens: *who controls it*.

| Primitive | Controlled by | Analogy |
|---|---|---|
| Tools | Model | POST endpoints, functions |
| Resources | Application (host) | GET endpoints, files |
| Prompts | User | Slash commands, templates |
| Sampling | Server asks, host decides | Server borrows the LLM |
| Roots | Host tells server | Allowed directories |
| Elicitation | Server asks user | A form popup |

---

## 3.1 Tools

### What
Executable functions the model can call. The server returns a JSON Schema for inputs; the host converts that into the model's native tool-calling format.

### Definition shape
```json
{
  "name": "get_weather",
  "title": "Get Weather",
  "description": "Current weather for a city. Use when the user asks about conditions right now.",
  "inputSchema": {
    "type": "object",
    "properties": { "city": { "type": "string" } },
    "required": ["city"]
  },
  "outputSchema": { "type": "object", "properties": { "tempC": { "type": "number" } } },
  "annotations": { "readOnlyHint": true, "destructiveHint": false, "idempotentHint": true, "openWorldHint": true }
}
```

### Call and result
- Request: `tools/call` with `name` and `arguments`.
- Result: `content[]` of `text`, `image`, `audio`, `resource_link`, or embedded `resource`; optional `structuredContent` (must match `outputSchema`); `isError: true` for tool-level failures (distinct from protocol errors).

### Annotations (hints, not guarantees)
- `readOnlyHint`: does not modify state.
- `destructiveHint`: may delete or overwrite.
- `idempotentHint`: repeat calls are safe.
- `openWorldHint`: touches external systems (web, APIs).
Hosts use these to decide whether to ask the user for confirmation.

### Writing good tools
1. Description says *when* to use it, not just what it does.
2. Keep argument count small; prefer one object over many scalars.
3. Return text the model can reason over. Avoid dumping raw JSON blobs of 10k tokens.
4. Fail with `isError` and an actionable message, not a stack trace.
5. Mark side effects honestly in annotations.

---

## 3.2 Resources

### What
Read-only data identified by a URI. The host (not the model) usually decides which resources to attach to context, e.g. "@file" pickers in IDEs.

### Two flavours
- **Direct resources**: `resources/list` returns concrete URIs like `file:///repo/README.md`.
- **Resource templates**: `resources/templates/list` returns RFC 6570 URI templates like `db://users/{id}`; the client fills in the blanks.

### Reading
`resources/read` returns `contents[]`, each with `uri`, `mimeType`, and either `text` or base64 `blob`.

### Subscriptions
If server declares `resources: { subscribe: true }`, the client can `resources/subscribe` to a URI and receive `notifications/resources/updated` when it changes.

### When to use a resource vs a tool
- Resource: the data exists already and just needs to be surfaced (logs, docs, schemas).
- Tool: the model must decide to fetch or compute something with parameters.

---

## 3.3 Prompts

### What
Reusable, parameterised message templates. Surfaced to users as slash commands or menu items.

### Shape
```json
{
  "name": "review_pr",
  "title": "Review a pull request",
  "description": "Structured code review",
  "arguments": [ { "name": "pr_url", "description": "Link to the PR", "required": true } ]
}
```
`prompts/get` returns `messages[]` of `{ role, content }` that the host injects into the conversation. Content can embed resources.

### Use cases
- Onboarding workflows ("/setup-project").
- Enforcing a house style for a recurring task.
- Bundling a resource plus instructions in one shot.

---

## 3.4 Sampling (server asks host to run the LLM)

### What
Server sends `sampling/createMessage` with `messages`, optional `systemPrompt`, `modelPreferences` (hints, cost/speed/intelligence priorities), `maxTokens`. Host may show the user a review dialog, runs the model, returns the completion.

### Why it exists
Lets a server do agentic sub-steps (summarise, classify, extract) **without holding its own API key**. The user keeps control and pays through the host.

### Cautions
- Not all hosts support it (Claude Desktop historically did not; Claude Code and several SDK-based hosts do).
- Never assume a specific model. Use `modelPreferences.hints` as suggestions only.

---

## 3.5 Roots

### What
Client declares `roots` capability and answers `roots/list` with `file://` URIs. Tells the server which directories or projects are in scope. `notifications/roots/list_changed` fires when the user switches project.

### Use
Filesystem, git, and build servers should respect roots as their sandbox boundary. Treat any path outside the roots as forbidden.

---

## 3.6 Elicitation

### What
Server sends `elicitation/create` with a `message` and a flat JSON Schema (strings, numbers, booleans, enums). Host renders a form; user fills it or declines. Result carries `action: accept | decline | cancel` and `content`.

### Use
- Ask for a missing parameter mid-tool-call instead of failing.
- Confirm a destructive step with a human.

### Rule
Never elicit secrets (passwords, tokens). Use proper OAuth instead.

---

## 3.7 Cross-cutting utilities

| Utility | Purpose |
|---|---|
| `completion/complete` | Autocomplete values for prompt args or resource template vars |
| `logging/setLevel` + `notifications/message` | Server logs surfaced in host UI |
| `notifications/progress` | Percent or step updates on long calls |
| `notifications/cancelled` | Abort a request |
| `ping` | Keep-alive and liveness |
| `_meta` | Free-form metadata bag on any message |

## 3.8 Cheat sheet

```
Model wants to DO something        -> Tool
App wants to SHOW something        -> Resource
User wants to TRIGGER a workflow   -> Prompt
Server needs the LLM               -> Sampling
Server needs to know the workspace -> Roots
Server needs user input            -> Elicitation
```
