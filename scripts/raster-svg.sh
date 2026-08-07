#!/usr/bin/env bash
# Converte um logo em SVG para PNG, porque o Pillow não lê SVG.
#
# Alguns clientes só mandaram a marca em vetor. O mosaico de clientes é PNG
# (40 arquivos, todos gerados por scripts/optimize-images.py), e o site não
# carrega SVG de terceiro sem antes olhar o que tem dentro — SVG é XML, aceita
# script e referência externa. Rasterizar aqui resolve os dois pontos.
#
# Rasteriza com o Quick Look do próprio macOS (`qlmanage`), que usa o mesmo
# motor do Preview: nada de instalar Inkscape ou librsvg. O Quick Look devolve
# a miniatura sempre num quadrado, com o desenho centralizado e sobra
# transparente em volta — então o passo seguinte recorta essa sobra e achata o
# que restou sobre branco, que é o fundo dos outros 40 logos.
#
# Uso:  ./scripts/raster-svg.sh <entrada.svg> <saida.png> [largura]
# Depois:  aplicar logo() de scripts/optimize-images.py no arquivo gerado.
#
# Atenção: nem todo arquivo com extensão .svg é SVG. "Cmpc logo.svg", por
# exemplo, é um WebP renomeado — o Pillow abre direto e este script não é
# necessário. Confira com `file` antes.

set -euo pipefail

if [ $# -lt 2 ]; then
  sed -n '2,20p' "$0"
  exit 2
fi

ENTRADA="$1"
SAIDA="$2"
LARGURA="${3:-380}"

cd "$(dirname "$0")/.."

if [ ! -f "$ENTRADA" ]; then
  echo "não achei: $ENTRADA" >&2
  exit 1
fi

if ! command -v qlmanage >/dev/null 2>&1; then
  echo "qlmanage não existe fora do macOS — rasterize o SVG à mão." >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# -s é o lado do quadrado; pedimos com folga porque o desenho não o preenche
qlmanage -t -s "$((LARGURA * 2))" -o "$TMP" "$ENTRADA" >/dev/null 2>&1 || true

BRUTO="$(find "$TMP" -name '*.png' -print -quit)"
if [ -z "$BRUTO" ] || [ ! -s "$BRUTO" ]; then
  echo "o Quick Look não rasterizou '$ENTRADA' (arquivo corrompido ou não é SVG)" >&2
  exit 1
fi

../bin/python - "$BRUTO" "$SAIDA" "$LARGURA" <<'PY'
import sys
from PIL import Image, ImageChops

bruto, saida, largura = sys.argv[1], sys.argv[2], int(sys.argv[3])

im = Image.open(bruto).convert("RGBA")

# achata sobre branco: é o fundo dos outros logos do mosaico, e o PNG indexado
# de 128 cores que vem depois não guarda alfa
fundo = Image.new("RGBA", im.size, (255, 255, 255, 255))
im = Image.alpha_composite(fundo, im).convert("RGB")

# tira a moldura que o Quick Look acrescenta para fechar o quadrado. Ela pode
# vir transparente ou branca conforme a versão do macOS, então o corte é pela
# diferença contra a cor do canto — funciona nos dois casos.
canto = Image.new("RGB", im.size, im.getpixel((0, 0)))
caixa = ImageChops.difference(im, canto).getbbox()
if caixa:
    im = im.crop(caixa)

if im.width > largura:
    im.thumbnail((largura, largura * 4), Image.LANCZOS)

im.save(saida, "PNG", optimize=True)
print(f"{saida}  {im.width}x{im.height}")
PY
