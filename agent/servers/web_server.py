"""Web fetch MCP server with a domain allowlist and SSRF protection.

Only hosts in MCP_WEB_ALLOW (comma-separated; subdomains included) can be
fetched. Every hop, redirects included, must be http(s) on an allowed host
that resolves to a public IP, so the agent cannot be steered into
localhost or cloud metadata endpoints.

Run: uv run servers/web_server.py
"""

import html
import ipaddress
import os
import re
import socket
from urllib.parse import urljoin, urlsplit

import httpx2
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

ALLOW = [d.strip().lower() for d in os.environ.get(
    "MCP_WEB_ALLOW", "modelcontextprotocol.io,docs.python.org,example.com").split(",") if d.strip()]
MAX_CHARS = 30_000
MAX_REDIRECTS = 5

mcp = MCPServer("web", instructions=f"Fetch pages from: {', '.join(ALLOW)}.")


def check_url(url: str, resolve: bool = True) -> str:
    """Return the host if the URL may be fetched, else raise ToolError."""
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        raise ToolError(f"scheme {parts.scheme!r} not allowed")
    host = (parts.hostname or "").lower()
    if not any(host == d or host.endswith("." + d) for d in ALLOW):
        raise ToolError(f"host {host!r} is not on the allowlist ({', '.join(ALLOW)})")
    if resolve:
        try:
            infos = socket.getaddrinfo(host, parts.port or 443)
        except socket.gaierror as e:
            raise ToolError(f"cannot resolve {host!r}") from e
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_global:
                raise ToolError(f"{host!r} resolves to non-public address {ip}")
    return host


def html_to_text(body: str) -> str:
    body = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", body)
    body = re.sub(r"(?i)<br\s*/?>|</(p|div|h[1-6]|li|tr)>", "\n", body)
    body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", body)).strip()


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True))
async def fetch_url(url: str) -> str:
    """Fetch a web page on an allowlisted domain and return its readable text."""
    async with httpx2.AsyncClient(timeout=15, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            check_url(url)
            resp = await client.get(url, headers={"User-Agent": "mcp-god-agent/0.1"})
            if resp.is_redirect and "location" in resp.headers:
                url = urljoin(url, resp.headers["location"])
                continue
            if resp.status_code >= 400:
                raise ToolError(f"HTTP {resp.status_code} for {url}")
            ctype = resp.headers.get("content-type", "")
            text = html_to_text(resp.text) if "html" in ctype else resp.text
            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS] + f"\n[truncated at {MAX_CHARS} chars]"
            return f"URL: {url}\n\n{text}"
    raise ToolError(f"more than {MAX_REDIRECTS} redirects")


if __name__ == "__main__":
    mcp.run()
