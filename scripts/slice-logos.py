#!/usr/bin/env python3
"""Fatia as sete tiras de logos de clientes em imagens individuais.

As tiras vieram do CDN do site atual como PNGs de 1842x196 com 5-6 logos cada,
espaçados de forma irregular. Em vez de cortar em fatias iguais (que corta
logo no meio), este script detecta as colunas que têm conteúdo e corta nos
intervalos vazios entre os logos.

Uso:  ../bin/python scripts/slice-logos.py
Saída: assets/img/clientes/raw/<tira>-<n>.png
"""

import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/img/_inspecionar"
OUT = ROOT / "assets/img/clientes/raw"

# Uma coluna conta como "com conteúdo" se tiver pelo menos este tanto de pixels
# visíveis e escuros o bastante para não ser fundo branco.
ALPHA_MIN = 24
LUMA_MAX = 242
MIN_INK_PIXELS = 2
# Intervalo horizontal vazio que separa dois logos (em px).
MIN_GAP = 28
# Largura mínima para um recorte ser considerado um logo e não ruído.
MIN_WIDTH = 40
PAD = 6


def ink_columns(img: Image.Image) -> list[bool]:
    w, h = img.size
    px = img.load()
    cols = []
    for x in range(w):
        n = 0
        for y in range(h):
            r, g, b, a = px[x, y]
            if a < ALPHA_MIN:
                continue
            # luminância aproximada
            if (r * 299 + g * 587 + b * 114) // 1000 <= LUMA_MAX:
                n += 1
                if n >= MIN_INK_PIXELS:
                    break
        cols.append(n >= MIN_INK_PIXELS)
    return cols


def runs(cols: list[bool]) -> list[tuple[int, int]]:
    """Blocos contíguos de conteúdo, unindo os separados por menos de MIN_GAP."""
    spans, start = [], None
    for i, c in enumerate(cols):
        if c and start is None:
            start = i
        elif not c and start is not None:
            spans.append((start, i))
            start = None
    if start is not None:
        spans.append((start, len(cols)))

    merged: list[list[int]] = []
    for a, b in spans:
        if merged and a - merged[-1][1] < MIN_GAP:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged if b - a >= MIN_WIDTH]


def trim_vertically(img: Image.Image) -> Image.Image:
    w, h = img.size
    px = img.load()
    top, bottom = None, None
    for y in range(h):
        row = False
        for x in range(w):
            r, g, b, a = px[x, y]
            if a >= ALPHA_MIN and (r * 299 + g * 587 + b * 114) // 1000 <= LUMA_MAX:
                row = True
                break
        if row:
            if top is None:
                top = y
            bottom = y
    if top is None:
        return img
    return img.crop((0, max(0, top - PAD), w, min(h, bottom + 1 + PAD)))


def main() -> int:
    if not SRC.is_dir():
        print(f"não encontrei {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    total = 0
    for path in sorted(SRC.glob("*.png"), key=lambda p: int(p.stem)):
        img = Image.open(path).convert("RGBA")
        spans = runs(ink_columns(img))
        print(f"{path.name:>8}  {img.size[0]}x{img.size[1]}  -> {len(spans)} logos")
        for i, (a, b) in enumerate(spans, 1):
            crop = img.crop((max(0, a - PAD), 0, min(img.size[0], b + PAD), img.size[1]))
            crop = trim_vertically(crop)
            dest = OUT / f"{path.stem}-{i}.png"
            crop.save(dest)
            print(f"           {dest.name:<12} {crop.size[0]}x{crop.size[1]}")
            total += 1

    print(f"\n{total} logos gravados em {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
