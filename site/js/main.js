// Scroll reveal + theme toggle.
(function () {
  const io = new IntersectionObserver((ents) => {
    ents.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { threshold: .12 });
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));

  const root = document.documentElement;
  const btn = document.getElementById("theme");
  let saved = null;
  try { saved = localStorage.getItem("mcp-god-theme"); } catch (_) {}
  if (saved) root.setAttribute("data-theme", saved);
  btn?.addEventListener("click", () => {
    const sysDark = matchMedia("(prefers-color-scheme: dark)").matches;
    const cur = root.getAttribute("data-theme") || (sysDark ? "dark" : "light");
    const nxt = cur === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", nxt);
    try { localStorage.setItem("mcp-god-theme", nxt); } catch (_) {}
  });
})();
