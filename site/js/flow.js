// Animated JSON-RPC packets moving between Host, Client and Server.
(function () {
  const svg = document.getElementById("flowSvg");
  if (!svg) return;
  const packets = document.getElementById("packets");
  const ticker = document.getElementById("tickerText");
  const nodes = { host: nHost, client: nClient, server: nServer };
  const paths = { HC: pHC, CH: pCH, CS: pCS, SC: pSC };

  // A scripted conversation. Each step: path, kind, label, which node lights up at the end.
  const script = [
    ["HC", "req", '{ "method": "initialize", "params": { "protocolVersion": "2025-06-18" } }', "client"],
    ["CS", "req", '{ "id": 1, "method": "initialize" }', "server"],
    ["SC", "res", '{ "id": 1, "result": { "capabilities": { "tools": {} } } }', "client"],
    ["CS", "ntf", '{ "method": "notifications/initialized" }', "server"],
    ["CS", "req", '{ "id": 2, "method": "tools/list" }', "server"],
    ["SC", "res", '{ "id": 2, "result": { "tools": [ { "name": "add" } ] } }', "client"],
    ["CH", "res", "tools: [add]  →  shown to the model", "host"],
    ["HC", "req", 'model picks: add({ "a": 2, "b": 3 })', "client"],
    ["CS", "req", '{ "id": 3, "method": "tools/call", "params": { "name": "add", "arguments": { "a": 2, "b": 3 } } }', "server"],
    ["SC", "ntf", '{ "method": "notifications/progress", "params": { "progress": 50 } }', "client"],
    ["SC", "res", '{ "id": 3, "result": { "content": [ { "type": "text", "text": "5" } ] } }', "client"],
    ["CH", "res", "result → appended to conversation", "host"],
  ];

  let i = 0, running = true, raf = null;

  function light(name) {
    Object.values(nodes).forEach(n => n.classList.remove("active"));
    if (nodes[name]) nodes[name].classList.add("active");
  }

  function fly(step, done) {
    const [pid, kind, label, target] = step;
    const path = paths[pid];
    const len = path.getTotalLength();
    const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    dot.setAttribute("r", kind === "ntf" ? 5 : 7);
    dot.setAttribute("class", "packet " + kind);
    packets.appendChild(dot);
    ticker.textContent = label.length > 92 ? label.slice(0, 89) + "..." : label;
    const dur = 900;
    const t0 = performance.now();
    function frame(t) {
      const p = Math.min(1, (t - t0) / dur);
      const e = p < .5 ? 2 * p * p : -1 + (4 - 2 * p) * p; // easeInOut
      const pt = path.getPointAtLength(e * len);
      dot.setAttribute("cx", pt.x);
      dot.setAttribute("cy", pt.y);
      if (p < 1) raf = requestAnimationFrame(frame);
      else { dot.remove(); light(target); done(); }
    }
    raf = requestAnimationFrame(frame);
  }

  function next() {
    if (!running) return;
    fly(script[i], () => {
      i = (i + 1) % script.length;
      setTimeout(next, i === 0 ? 1400 : 450);
    });
  }

  const toggle = document.getElementById("flowToggle");
  toggle.addEventListener("click", () => {
    running = !running;
    toggle.textContent = running ? "Pause" : "Play";
    if (running) next(); else if (raf) cancelAnimationFrame(raf);
  });

  // Start when visible.
  const io = new IntersectionObserver((ents) => {
    if (ents[0].isIntersecting) { io.disconnect(); light("host"); setTimeout(next, 500); }
  }, { threshold: .3 });
  io.observe(svg);
})();
