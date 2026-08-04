#!/usr/bin/env python3
"""Reduz o peso das imagens sem mudar como a página parece.

Três problemas medidos no repositório:

1. Os 40 logos de cliente vieram de fatias de tiras JPEG, salvos em PNG RGBA de
   ~340px de largura. O alfa é totalmente opaco (25% de dados jogados fora), o
   ruído de JPEG não comprime bem em PNG truecolor, e a célula do mosaico exibe
   cerca de 100x47 CSS px.
2. As fotos de obra são servidas no tamanho original — goodman.jpg tem 1447px e
   350 KB para um card que renderiza a ~540 CSS px.
3. A foto do herói entra a opacity 0.28 sob um gradiente 86% opaco, ou seja,
   quase nada da qualidade original chega aos olhos.

Alvos: DPR2 do tamanho real de exibição. Nunca amplia.

Uso:  ../bin/python scripts/optimize-images.py [--dry-run]
Depois:  ../bin/python scripts/add-img-dims.py   (senão o CLS volta)
"""

import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "assets/img"

DRY = "--dry-run" in sys.argv


def kb(n: int) -> str:
    return f"{n / 1024:.0f} KB"


def processa(path: pathlib.Path, fn) -> tuple[int, int]:
    antes = path.stat().st_size
    if DRY:
        return antes, antes
    fn(path)
    return antes, path.stat().st_size


def logo(path: pathlib.Path) -> None:
    im = Image.open(path).convert("RGBA")
    # o alfa é opaco em todos: descartar o canal antes de quantizar
    if im.getchannel("A").getextrema() == (255, 255):
        im = im.convert("RGB")
    im.thumbnail((190, 190), Image.LANCZOS)
    im.convert("RGB").quantize(colors=128, method=Image.FASTOCTREE).save(
        path, "PNG", optimize=True
    )


def foto(largura_max: int, qualidade: int):
    def _fn(path: pathlib.Path) -> None:
        im = Image.open(path).convert("RGB")
        if im.width > largura_max:
            im.thumbnail((largura_max, largura_max * 4), Image.LANCZOS)
        im.save(path, "JPEG", quality=qualidade, optimize=True, progressive=True)
    return _fn


def main() -> int:
    if DRY:
        print("(dry-run — nada será gravado)\n")

    total_antes = total_depois = 0

    logos = sorted((IMG / "clientes/logos").glob("*.png"))
    print(f"==> {len(logos)} logos de cliente  (exibidos a ~100x47 CSS px)")
    a = d = 0
    for p in logos:
        x, y = processa(p, logo)
        a += x
        d += y
    print(f"    {kb(a)} -> {kb(d)}")
    total_antes += a
    total_depois += d

    # o card renderiza a ~540 CSS px; 1080 cobre DPR2
    print("\n==> fotos de obra  (card a ~540 CSS px, alvo 1080)")
    for nome in ("goodman.jpg", "klabin.jpg", "sca-1.jpg", "clara-resorts-2.jpg"):
        p = IMG / "obras" / nome
        if not p.is_file():
            print(f"    ausente: {nome}")
            continue
        x, y = processa(p, foto(1080, 72))
        print(f"    {nome:<24} {kb(x):>8} -> {kb(y):>8}")
        total_antes += x
        total_depois += y

    # herói: opacity .28 sob gradiente 86% opaco — q45 é indistinguível
    p = IMG / "obras/clara-resorts-1.jpg"
    if p.is_file():
        print("\n==> herói  (opacity .28 sob gradiente; q45)")
        x, y = processa(p, foto(1600, 45))
        print(f"    {p.name:<24} {kb(x):>8} -> {kb(y):>8}")
        total_antes += x
        total_depois += y

    # favicon grande: logotipo de poucas cores não precisa de 24 bits
    p = IMG / "favicon-512.png"
    if p.is_file():
        print("\n==> favicon 512")
        def _fav(path):
            im = Image.open(path).convert("RGBA")
            im.quantize(colors=64, method=Image.FASTOCTREE).save(path, "PNG", optimize=True)
        x, y = processa(p, _fav)
        print(f"    {p.name:<24} {kb(x):>8} -> {kb(y):>8}")
        total_antes += x
        total_depois += y

    print("\n" + "-" * 46)
    print(f"total  {kb(total_antes)} -> {kb(total_depois)}"
          f"   (-{kb(total_antes - total_depois)}, "
          f"-{100 * (total_antes - total_depois) / total_antes:.0f}%)")
    if not DRY:
        print("\nAgora rode:  ../bin/python scripts/add-img-dims.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
