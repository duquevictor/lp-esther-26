#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResizeJob:
    input_path: Path
    widths: tuple[int, ...]
    crop_square: bool = False


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _probe_size(path: Path) -> tuple[int, int]:
    # Returns (width, height)
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            str(path),
        ],
        text=True,
    ).strip()
    w_str, h_str = out.split(",", 1)
    return int(w_str), int(h_str)


def _even(n: int) -> int:
    return n if n % 2 == 0 else n + 1


def _calc_height(src_w: int, src_h: int, target_w: int) -> int:
    if target_w >= src_w:
        return _even(src_h)
    return _even(max(2, round(src_h * (target_w / src_w))))


def _encode_webp(*, src: Path, dst: Path, w: int, h: int, quality: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "cwebp",
            "-preset",
            "photo",
            "-q",
            str(quality),
            "-m",
            "4",
            "-mt",
            "-metadata",
            "none",
            "-resize",
            str(w),
            str(h),
            str(src),
            "-o",
            str(dst),
        ]
    )


def _encode_webp_square_avatar(*, src: Path, dst: Path, size: int, quality: int) -> None:
    src_w, src_h = _probe_size(src)
    square = min(src_w, src_h)
    crop_x = max(0, (src_w - square) // 2)
    crop_y = max(0, (src_h - square) // 2)

    dst.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "cwebp",
            "-preset",
            "photo",
            "-q",
            str(quality),
            "-m",
            "4",
            "-mt",
            "-metadata",
            "none",
            "-crop",
            str(crop_x),
            str(crop_y),
            str(square),
            str(square),
            "-resize",
            str(size),
            str(size),
            str(src),
            "-o",
            str(dst),
        ]
    )


def _expand_glob(root: Path, pattern: str) -> list[Path]:
    return sorted(root.glob(pattern))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera versões WebP responsivas (por largura) usando cwebp."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Diretório raiz do projeto (default: .)",
    )
    parser.add_argument(
        "--input-dir",
        default="imagens-webp",
        help="Diretório de entrada com .webp (default: imagens-webp)",
    )
    parser.add_argument(
        "--output-dir",
        default="imagens-webp/responsive",
        help="Diretório de saída (default: imagens-webp/responsive)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=75,
        help="Qualidade do WebP (0-100). Default: 75",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    in_dir = (root / args.input_dir).resolve()
    out_dir = (root / args.output_dir).resolve()

    jobs: list[ResizeJob] = []

    # Marquee (receitas)
    for p in _expand_glob(in_dir, "recipe-[0-9][0-9]-*.webp"):
        if p.name.startswith("recipe-07-") or p.name.startswith("recipe-08-") or p.name.startswith("recipe-09-") or p.name.startswith("recipe-10-") or p.name.startswith("recipe-11-") or p.name.startswith("recipe-12-") or p.name.startswith("recipe-13-") or p.name.startswith("recipe-14-") or p.name.startswith("recipe-15-") or p.name.startswith("recipe-16-") or p.name.startswith("recipe-17-") or p.name.startswith("recipe-18-") or p.name.startswith("recipe-19-") or p.name.startswith("recipe-20-") or p.name.startswith("recipe-21-") or p.name.startswith("recipe-22-") or p.name.startswith("recipe-23-") or p.name.startswith("recipe-24-"):
            jobs.append(ResizeJob(p, (200, 400)))

    # Avatar
    avatar = in_dir / "foto-perfil-hero.webp"
    if avatar.exists():
        jobs.append(ResizeJob(avatar, (48, 96), crop_square=True))

    # Antes/depois (história)
    for p in [in_dir / "antes-esther.webp", in_dir / "depois-esther.webp"]:
        if p.exists():
            jobs.append(ResizeJob(p, (360, 720)))

    # Cards (grid) e mockups
    for p in [in_dir / "recipe-01-crumble-de-banana.webp", in_dir / "recipe-08-maionese-de-abacate.webp"]:
        if p.exists():
            jobs.append(ResizeJob(p, (400, 800)))

    mockups = in_dir / "mockups-corretos.webp"
    if mockups.exists():
        jobs.append(ResizeJob(mockups, (768, 1536)))

    if not in_dir.exists():
        raise SystemExit(f"Input dir not found: {in_dir}")

    total = 0
    for job in jobs:
        base = job.input_path.stem
        for w in job.widths:
            dst = out_dir / f"{base}-{w}w.webp"
            if job.crop_square:
                _encode_webp_square_avatar(
                    src=job.input_path, dst=dst, size=w, quality=args.quality
                )
            else:
                src_w, src_h = _probe_size(job.input_path)
                h = _calc_height(src_w, src_h, w)
                _encode_webp(
                    src=job.input_path, dst=dst, w=w, h=h, quality=args.quality
                )
            total += 1

    print(f"Generated {total} files into {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

