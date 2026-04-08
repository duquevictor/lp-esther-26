#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScanResult:
    referenced: set[Path]
    candidates: list[Path]
    missing: set[Path]


_RE_ATTR = re.compile(
    r"""(?:
        \b(?:src|href|poster)\s*=\s*["'](?P<attr>[^"']+)["']
      | \bstyle\s*=\s*["'][^"']*url\((?P<style_url>[^)]+)\)[^"']*["']
    )""",
    re.IGNORECASE | re.VERBOSE,
)

_RE_CSS_URL = re.compile(r"""url\((?P<url>[^)]+)\)""", re.IGNORECASE)


def _strip_url(u: str) -> str:
    u = u.strip()
    # Sometimes values come partially escaped, e.g. \"data:... or "data:...
    u = u.lstrip("\\")
    if (u.startswith('"') and u.endswith('"')) or (u.startswith("'") and u.endswith("'")):
        u = u[1:-1]
    return u.strip()


def _is_local_asset(ref: str) -> bool:
    ref = ref.strip()
    if not ref:
        return False
    ref2 = ref.lstrip("\\\"'").strip()
    if ref2.startswith(("http://", "https://", "data:", "mailto:", "tel:")):
        return False
    if ref.startswith("#"):
        return False
    if "${" in ref or "}" in ref:
        return False
    # Only treat things that look like file paths as assets
    allowed_ext = {
        ".webp",
        ".png",
        ".jpg",
        ".jpeg",
        ".svg",
        ".gif",
        ".css",
        ".js",
        ".mjs",
        ".json",
        ".woff2",
        ".woff",
        ".ttf",
        ".mp4",
        ".webm",
    }
    # Must have a slash OR a known extension
    if "/" not in ref2 and Path(ref2).suffix.lower() not in allowed_ext:
        return False
    return True


def _normalize_ref(root: Path, ref: str) -> Path | None:
    ref = _strip_url(ref)
    # drop query/hash
    ref = ref.split("#", 1)[0].split("?", 1)[0]
    if not _is_local_asset(ref):
        return None
    # keep only paths under project root
    p = (root / ref).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return None
    return p


def _extract_refs_from_text(root: Path, text: str) -> set[Path]:
    refs: set[Path] = set()

    for m in _RE_ATTR.finditer(text):
        for key in ("attr", "style_url"):
            val = m.group(key)
            if not val:
                continue
            p = _normalize_ref(root, val)
            if p is not None:
                refs.add(p)

    # Also parse raw CSS url() occurrences in inline <style> blocks etc.
    for m in _RE_CSS_URL.finditer(text):
        val = m.group("url")
        if not val:
            continue
        p = _normalize_ref(root, val)
        if p is not None:
            refs.add(p)

    return refs


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def scan(root: Path) -> ScanResult:
    root = root.resolve()
    index = root / "index.html"
    src_dir = root / "src"

    referenced: set[Path] = set()
    for p in [index]:
        if p.exists():
            referenced |= _extract_refs_from_text(root, _read_text(p))

    if src_dir.exists():
        for dirpath, _dirnames, filenames in os.walk(src_dir):
            for fn in filenames:
                if not fn.lower().endswith((".html", ".css", ".js", ".mjs", ".ts", ".tsx", ".json", ".svg")):
                    continue
                fp = Path(dirpath) / fn
                referenced |= _extract_refs_from_text(root, _read_text(fp))

    # Candidate assets we are willing to delete in this cleanup pass
    candidates: list[Path] = []
    for rel in ("imagens", "imagens-webp"):
        base = root / rel
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            # Never delete generated responsive assets (they are the new source of truth)
            if Path(dirpath).name == "responsive":
                dirnames[:] = []
                continue
            for fn in filenames:
                fp = (Path(dirpath) / fn).resolve()
                candidates.append(fp)

    missing: set[Path] = set()
    for ref in referenced:
        if not ref.exists():
            missing.add(ref)

    return ScanResult(referenced=referenced, candidates=sorted(set(candidates)), missing=missing)


def main() -> int:
    ap = argparse.ArgumentParser(description="Remove assets locais não referenciados.")
    ap.add_argument("--root", default=".", help="Raiz do projeto (default: .)")
    ap.add_argument(
        "--yes",
        action="store_true",
        help="Executa deleção. Sem isso, apenas imprime o plano (dry-run).",
    )
    ap.add_argument(
        "--report-json",
        action="store_true",
        help="Imprime um relatório JSON com detalhes (útil para auditoria).",
    )
    args = ap.parse_args()

    root = Path(args.root).resolve()
    res = scan(root)

    referenced_rel = sorted({str(p.relative_to(root)) for p in res.referenced})
    candidates_rel = [str(p.relative_to(root)) for p in res.candidates]
    deletable = [p for p in res.candidates if p not in res.referenced]
    deletable_rel = [str(p.relative_to(root)) for p in deletable]
    missing_rel = sorted({str(p.relative_to(root)) for p in res.missing})

    if args.report_json:
        print(
            json.dumps(
                {
                    "root": str(root),
                    "referenced_count": len(referenced_rel),
                    "referenced": referenced_rel,
                    "candidates_count": len(candidates_rel),
                    "candidates": candidates_rel,
                    "deletable_count": len(deletable_rel),
                    "deletable": deletable_rel,
                    "missing_count": len(missing_rel),
                    "missing": missing_rel,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"Referências locais encontradas: {len(referenced_rel)}")
        print(f"Candidatos avaliados (imagens/ + imagens-webp/, exceto responsive/): {len(candidates_rel)}")
        print(f"Arquivos seguros para remover (não referenciados): {len(deletable_rel)}")
        if missing_rel:
            print(f"ATENÇÃO: referências quebradas encontradas: {len(missing_rel)}")
            for x in missing_rel[:40]:
                print(f"  - {x}")
            if len(missing_rel) > 40:
                print("  - ...")

    if not args.yes:
        return 0

    # Safety: abort if there are missing references
    if res.missing:
        print("Abortando deleção porque existem referências quebradas (missing).")
        return 2

    removed = 0
    for p in deletable:
        try:
            p.unlink()
            removed += 1
        except FileNotFoundError:
            continue

    print(f"Removidos: {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

