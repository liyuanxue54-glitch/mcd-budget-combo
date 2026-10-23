#!/usr/bin/env python3
"""Live smoke test for McDonald's China MCP (read-only).

Loads token from MCD_MCP_TOKEN env, or sibling/parent .secrets/mcd_mcp_token.txt.
Calls tools/list + list-nutrition-foods (no store required). Never prints the token.
Mutating tools (create-order, mall-create-order, cancel-order, auto-bind-coupons,
draw-lottery) are never called.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = os.environ.get("MCD_MCP_URL", "https://mcp.mcd.cn")
OUT_PREFIX = "/tmp/mcd-smoke"


def load_token() -> str:
    env = os.environ.get("MCD_MCP_TOKEN", "").strip()
    if env:
        return env
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / ".secrets" / "mcd_mcp_token.txt",  # contest root
        here.parents[1] / ".secrets" / "mcd_mcp_token.txt",  # project root
        Path.home() / ".secrets" / "mcd_mcp_token.txt",
    ]
    for p in candidates:
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    print("ERROR: no token (set MCD_MCP_TOKEN or place .secrets/mcd_mcp_token.txt)", file=sys.stderr)
    sys.exit(2)


def rpc(token: str, method: str, params: dict | None, req_id: int) -> dict:
    body = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {err_body[:500]}") from e
    # Handle SSE-ish payloads if any
    if raw.lstrip().startswith("event:") or "data:" in raw[:80]:
        chunks = []
        for line in raw.splitlines():
            if line.startswith("data:"):
                chunks.append(line[5:].strip())
        raw = chunks[-1] if chunks else raw
    return json.loads(raw)


def save(name: str, obj: dict) -> Path:
    path = Path(f"{OUT_PREFIX}-{name}.json")
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def sample_food_names(nutrition_result: dict, limit: int = 8) -> list[str]:
    """Prefer structuredContent.data; fall back to content text."""
    names: list[str] = []
    result = nutrition_result.get("result") or {}
    data = ""
    sc = result.get("structuredContent")
    if isinstance(sc, dict) and isinstance(sc.get("data"), str):
        data = sc["data"]
    if not data:
        for c in result.get("content") or []:
            if isinstance(c, dict) and c.get("type") == "text":
                data += c.get("text") or ""
    for line in data.splitlines():
        line = line.strip()
        if not line or "productName" in line:
            continue
        if "," not in line:
            continue
        name = line.split(",", 1)[0].strip()
        if not name or name in ("productName", "code", "data", "message"):
            continue
        if not any(chr(0x4E00) <= ch <= chr(0x9FFF) for ch in name):
            continue
        if name not in names:
            names.append(name)
        if len(names) >= limit:
            break
    return names


def main() -> int:
    token = load_token()
    # 1) initialize (optional but polite)
    init = rpc(
        token,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "live-smoke", "version": "0.1.0"},
        },
        1,
    )
    save("init", init)
    if "error" in init:
        print("ERROR: initialize failed", file=sys.stderr)
        return 1

    # 2) tools/list
    listed = rpc(token, "tools/list", {}, 2)
    save("tools-list", listed)
    tools = (listed.get("result") or {}).get("tools") or []
    if not tools:
        print("ERROR: tools/list empty", file=sys.stderr)
        return 1
    names = sorted(t.get("name", "") for t in tools)

    # 3) list-nutrition-foods (no store needed; safe read-only)
    nutrition = rpc(
        token,
        "tools/call",
        {"name": "list-nutrition-foods", "arguments": {}},
        3,
    )
    save("nutrition", nutrition)
    if "error" in nutrition or (nutrition.get("result") or {}).get("isError"):
        print("ERROR: list-nutrition-foods failed", file=sys.stderr)
        return 1

    foods = sample_food_names(nutrition)
    summary = {
        "ok": True,
        "endpoint": ENDPOINT,
        "tool_count": len(tools),
        "tool_names_sample": names[:12],
        "sample_foods": foods,
        "saved": [
            f"{OUT_PREFIX}-init.json",
            f"{OUT_PREFIX}-tools-list.json",
            f"{OUT_PREFIX}-nutrition.json",
        ],
        "ts": int(time.time()),
    }
    save("summary", summary)
    # Print summary only — never the token
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

