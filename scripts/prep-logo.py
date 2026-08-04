#!/usr/bin/env python3
"""Prepara o logo da Certek a partir do PNG original do CDN.

O arquivo original (Semnome120x50cm1) é 2399x1000, com o wordmark vinho sobre
fundo BRANCO opaco e muita margem em volta. Assim ele não serve nem para o
header claro (retângulo branco visível) nem para o rodapé escuro.

Este script:
  1. torna o branco transparente (o logo é chapado em duas cores, então um
     corte por luminância resolve sem franjas)
  2. recorta a margem em volta do conteúdo
  3. grava duas versões — a vinho para fundo claro e uma branca para fundo escuro

Uso:  ../bin/python scripts/prep-logo.py <origem.png>
"""

import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "assets/img"

# Acima disto o pixel é considerado fundo branco.
BRANCO_MIN = 235
# Abaixo disto é tinta cheia. Entre os dois, alpha proporcional (anti-aliasing).
TINTA_MAX = 170
MARGEM = 8


def main() -> int:
    origem = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else IMG / "logo-certek.png"
    if not origem.is_file():
        print(f"não encontrei {origem}", file=sys.stderr)
        return 1

    img = Image.open(origem).convert("RGBA")
    w, h = img.size
    px = img.load()

    # 1. branco -> transparente, preservando o anti-aliasing das bordas
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            luma = (r * 299 + g * 587 + b * 114) // 1000
            if luma >= BRANCO_MIN:
                px[x, y] = (r, g, b, 0)
            elif luma > TINTA_MAX:
                frac = (BRANCO_MIN - luma) / (BRANCO_MIN - TINTA_MAX)
                px[x, y] = (r, g, b, int(a * frac))

    # 2. recorta a margem
    caixa = img.getbbox()
    if caixa:
        l, t, r_, b_ = caixa
        img = img.crop(
            (max(0, l - MARGEM), max(0, t - MARGEM), min(w, r_ + MARGEM), min(h, b_ + MARGEM))
        )

    destino = IMG / "logo-certek.png"
    img.save(destino)
    print(f"{destino.relative_to(ROOT)}  {img.size[0]}x{img.size[1]}")

    # 3. versão branca para fundo escuro: mesma silhueta, tinta branca
    branco = Image.new("RGBA", img.size, (255, 255, 255, 0))
    bp, ip = branco.load(), img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            bp[x, y] = (255, 255, 255, ip[x, y][3])
    destino_b = IMG / "logo-certek-branco.png"
    branco.save(destino_b)
    print(f"{destino_b.relative_to(ROOT)}  {branco.size[0]}x{branco.size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
