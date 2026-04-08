#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ICON_TAG_RE = re.compile(r"<iconify-icon\b([^>]*)></iconify-icon>", re.IGNORECASE)
ATTR_RE = re.compile(r"(\w[\w-]*)\s*=\s*\"([^\"]*)\"")


@dataclass(frozen=True)
class IconTag:
    attrs: dict[str, str]

    @property
    def icon(self) -> str:
        return self.attrs.get("icon", "").strip()

    @property
    def klass(self) -> str:
        return self.attrs.get("class", "").strip()

    @property
    def aria_hidden(self) -> str:
        return self.attrs.get("aria-hidden", "").strip()


def fetch_svg(icon: str) -> str:
    # Iconify API returns an <svg ...>...</svg>
    url = f"https://api.iconify.design/{icon}.svg"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) CursorAgent/1.0",
            "Accept": "image/svg+xml,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def fetch_svg_fallback(icon: str) -> str | None:
    # Some endpoints (like /search) are blocked; but most direct SVG fetches work.
    # If the icon doesn't exist (404), we return None so the tag is left as-is.
    try:
        return fetch_svg(icon)
    except Exception as e:
        # Keep it simple: only swallow 404s, rethrow others.
        msg = str(e)
        if "HTTP Error 404" in msg:
            return None
        raise


def normalize_svg(svg: str, *, klass: str, aria_hidden: str) -> str:
    # Ensure class passes through and icon inherits currentColor
    # Remove width/height to allow CSS sizing.
    svg = svg.strip()
    if not svg.lower().startswith("<svg"):
        raise ValueError("Unexpected SVG payload")

    # Extract opening tag and inner content
    m = re.match(r"<svg\b([^>]*)>([\s\S]*?)</svg>", svg, re.IGNORECASE)
    if not m:
        raise ValueError("Could not parse SVG")

    attrs_raw = m.group(1)
    inner = m.group(2)

    # Remove width/height/fill from the original opening attrs; keep viewBox
    cleaned_attrs = re.sub(r'\s(width|height)\s*=\s*"[^"]*"', "", attrs_raw, flags=re.IGNORECASE)
    cleaned_attrs = re.sub(r'\sfill\s*=\s*"[^"]*"', "", cleaned_attrs, flags=re.IGNORECASE)
    cleaned_attrs = cleaned_attrs.strip()

    extra = []
    if klass:
        extra.append(f'class=\"{klass}\"')
    # Accessibility: treat as decorative when aria-hidden is true, otherwise let it be announced as image.
    if aria_hidden == "true":
        extra.append('aria-hidden=\"true\"')
        extra.append('focusable=\"false\"')
    else:
        extra.append('role=\"img\"')

    # Force currentColor
    extra.append('fill=\"currentColor\"')

    final_attrs = (cleaned_attrs + " " + " ".join(extra)).strip()
    return f"<svg {final_attrs}>{inner}</svg>"


def parse_attrs(attr_blob: str) -> dict[str, str]:
    attrs = {}
    for k, v in ATTR_RE.findall(attr_blob):
        attrs[k.lower()] = v
    return attrs


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: inline_iconify.py path/to/index.html", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    html = path.read_text(encoding="utf-8", errors="ignore")

    cache: dict[str, str] = {}
    replaced = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal replaced
        tag = IconTag(parse_attrs(m.group(1)))
        if not tag.icon:
            return m.group(0)
        if tag.icon not in cache:
            fetched = fetch_svg_fallback(tag.icon)
            if fetched is None:
                return m.group(0)
            cache[tag.icon] = fetched
        svg = normalize_svg(cache[tag.icon], klass=tag.klass, aria_hidden=tag.aria_hidden)
        replaced += 1
        return svg

    new_html = ICON_TAG_RE.sub(repl, html)
    path.write_text(new_html, encoding="utf-8")
    print(f"Replaced {replaced} <iconify-icon> tags with inline <svg>.")
    print(f"Unique icons fetched: {len(cache)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

