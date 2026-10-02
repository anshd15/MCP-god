// Session lifecycle: clickable steps + auto-play with an animated arrow between Client and Server lanes.
(function () {
  const list = document.getElementById("lifeSteps");
  if (!list) return;
  const msg = document.querySelector("#lifeMsg code");
  const arrow = document.getElementById("lifeArrow");

  const steps = [
    { dir: "cs", title: "initialize", sub: "Client proposes a protocol version and its capabilities.",
      code: '→ initialize\n{ "protocolVersion": "2025-06-18",\n  "capabilities": { "roots": {}, "sampling": {} },\n  "clientInfo": { "name": "claude-code" } }' },
    { dir: "sc", title: "initialize result", sub: "Server picks a version and declares what it offers.",
      code: '← result\n{ "protocolVersion": "2025-06-18",\n  "capabilities": { "tools": { "listChanged": true },\n                    "resources": {}, "prompts": {} },\n  "serverInfo": { "name": "my-server" } }' },
    { dir: "cs", title: "notifications/initialized", sub: "Handshake complete. No response expected.",
      code: '→ notifications/initialized\n(no id, no reply)' },
    { dir: "cs", title: "tools/list", sub: "Client asks for the tool catalogue.",
      code: '→ tools/list  { "id": 2 }' },
    { dir: "sc", title: "tools", sub: "Server returns names, descriptions, JSON Schemas.",
      code: '← result\n{ "tools": [ { "name": "add",\n    "description": "Add two integers.",\n    "inputSchema": { "type": "object",\n      "properties": { "a": {"type":"integer"}, "b": {"type":"integer"} } } } ] }' },
    { dir: "cs", title: "tools/call", sub: "The model chose a tool. Client forwards the call.",
      code: '→ tools/call  { "id": 3,\n  "params": { "name": "add", "arguments": { "a": 2, "b": 3 } } }' },
    { dir: "sc", title: "notifications/progress", sub: "Optional. Long tasks report progress.",
      code: '← notifications/progress\n{ "progressToken": "t3", "progress": 1, "total": 2 }' },
    { dir: "sc", title: "result", sub: "Content blocks the model can read. isError marks tool failures.",
      code: '← result  { "id": 3,\n  "content": [ { "type": "text", "text": "5" } ],\n  "isError": false }' },
    { dir: "sc", title: "notifications/tools/list_changed", sub: "Server added a tool. Client re-fetches the list.",
      code: '← notifications/tools/list_changed' },
    { dir: "cs", title: "close", sub: "Transport closes. stdio: process exits. HTTP: DELETE with Mcp-Session-Id.",
      code: '→ DELETE /mcp\nMcp-Session-Id: 9f1c...' },
  ];

  steps.forEach((s, idx) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="n">${String(idx + 1).padStart(2, "0")}</span><div><b>${s.title}</b><small>${s.sub}</small></div>`;
    li.addEventListener("click", () => { show(idx); restartTimer(); });
    list.appendChild(li);
  });

  let cur = -1, timer = null;
  function show(idx) {
    cur = idx;
    [...list.children].forEach((li, j) => li.classList.toggle("active", j === idx));
    const s = steps[idx];
    arrow.classList.remove("go", "flip");
    void arrow.offsetWidth; // restart animation
    if (s.dir === "sc") arrow.classList.add("flip");
    arrow.classList.add("go");
    msg.style.animation = "none"; void msg.offsetWidth; msg.style.animation = "";
    msg.textContent = s.code;
  }
  function tick() { show((cur + 1) % steps.length); }
  function restartTimer() { clearInterval(timer); timer = setInterval(tick, 3200); }

  const io = new IntersectionObserver((ents) => {
    if (ents[0].isIntersecting) { io.disconnect(); tick(); restartTimer(); }
  }, { threshold: .25 });
  io.observe(list);
})();
