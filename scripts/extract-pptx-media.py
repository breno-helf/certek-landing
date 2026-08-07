#!/usr/bin/env python3
"""Extrai as fotos de dentro de um .pptx e já as normaliza para o site.

Os slides institucionais da Certek são a única fonte de fotos de obra que
temos. Um .pptx é um zip: as imagens estão cruas em `ppt/media/`. Este script
abre o zip, joga fora o que não serve e grava o resto no padrão do
`optimize-images.py` (função `foto`): RGB, no máximo 1080px, JPEG q72
progressivo — o mesmo que as fotos de obra já versionadas.

O que é descartado, e por quê:

- `.wdp` — HD Photo/JPEG XR, um formato que o PowerPoint guarda junto de fotos
  com efeito aplicado. Pillow não lê e o navegador também não.
- o logotipo do template. Todo deck traz o mesmo `image1.png` de ~7,7 KB no
  rodapé de cada slide; ele já existe em `assets/img/` como marca do site.
  Reconhecido por tamanho pequeno + PNG, não por nome (o índice varia).
- qualquer imagem pequena demais para virar card (ícone, seta, marca-d'água).

Nada é gravado dentro de `assets/`: a saída é uma pasta de trabalho para
alguém olhar as fotos e escolher as boas à mão. A cópia final para
`assets/img/obras/` é decisão humana — foto com rosto visível, obra em
andamento ou render com caixa de texto não entra no site.

Uso:
    ../bin/python scripts/extract-pptx-media.py <arquivo.pptx> <pasta-saida>
    ../bin/python scripts/extract-pptx-media.py <arquivo.pptx> <saida> --map

`--map` não extrai nada: imprime, para cada slide, o texto e as mídias
referenciadas por ele. É como se descobre quais fotos pertencem a qual obra
num deck que cobre várias (Farmacêutica.pptx, Hospitalar e Saúde.pptx).
"""

import io
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageOps

LARGURA_MAX = 1080
QUALIDADE = 72

# o logo do template repete em todo slide; ~7,7 KB é o tamanho dele no zip
LIMITE_LOGO_BYTES = 12_000
# menor que isto não vira card de 16/10 nem com boa vontade
LADO_MINIMO = 500

NS_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def kb(n: int) -> str:
    return f"{n / 1024:.0f} KB"


def num(nome: str) -> int:
    """slide12.xml -> 12, para ordenar como o PowerPoint ordena."""
    m = re.search(r"(\d+)", pathlib.PurePath(nome).name)
    return int(m.group(1)) if m else 0


def texto_do_slide(zf: zipfile.ZipFile, slide: str) -> str:
    raiz = ET.fromstring(zf.read(slide))
    partes = [t.text.strip() for t in raiz.iter(f"{NS_A}t") if t.text and t.text.strip()]
    return " | ".join(partes)


def midias_do_slide(zf: zipfile.ZipFile, slide: str) -> list[str]:
    rels = f"ppt/slides/_rels/{pathlib.PurePath(slide).name}.rels"
    if rels not in zf.namelist():
        return []
    raiz = ET.fromstring(zf.read(rels))
    saida = []
    for rel in raiz.iter(f"{NS_REL}Relationship"):
        alvo = rel.get("Target", "")
        if "media/" in alvo:
            saida.append(pathlib.PurePath(alvo).name)
    return saida


def mapa(pptx: pathlib.Path) -> int:
    """Imprime slide a slide: texto + mídias, para casar foto com obra."""
    with zipfile.ZipFile(pptx) as zf:
        slides = sorted(
            (n for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
            key=num,
        )
        for s in slides:
            print(f"\n--- {pathlib.PurePath(s).name} ---")
            print(f"texto : {texto_do_slide(zf, s)[:900]}")
            print(f"midias: {', '.join(midias_do_slide(zf, s)) or '(nenhuma)'}")
    return 0


def extrai(pptx: pathlib.Path, destino: pathlib.Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    gravados = pulados = 0

    with zipfile.ZipFile(pptx) as zf:
        midias = sorted(
            (i for i in zf.infolist() if i.filename.startswith("ppt/media/")),
            key=lambda i: num(i.filename),
        )
        print(f"==> {pptx.name}  ({len(midias)} mídias)")

        for info in midias:
            nome = pathlib.PurePath(info.filename).name
            sufixo = pathlib.PurePath(nome).suffix.lower()

            if sufixo in (".wdp", ".emf", ".wmf"):
                print(f"    - {nome:<18} formato que o navegador não lê")
                pulados += 1
                continue
            if sufixo == ".png" and info.file_size <= LIMITE_LOGO_BYTES:
                print(f"    - {nome:<18} logo do template ({kb(info.file_size)})")
                pulados += 1
                continue

            try:
                im = Image.open(io.BytesIO(zf.read(info.filename)))
                # foto de celular guarda a rotação no EXIF; ao salvar de novo o
                # JPEG perde a tag e a foto sai deitada no navegador
                im = ImageOps.exif_transpose(im).convert("RGB")
            except Exception as e:  # noqa: BLE001 — mídia exótica, só reportar
                print(f"    - {nome:<18} Pillow não abriu ({e})")
                pulados += 1
                continue

            if max(im.size) < LADO_MINIMO:
                print(f"    - {nome:<18} pequena demais ({im.width}x{im.height})")
                pulados += 1
                continue

            largura_orig = im.width
            if im.width > LARGURA_MAX:
                im.thumbnail((LARGURA_MAX, LARGURA_MAX * 4), Image.LANCZOS)

            saida = destino / (pathlib.PurePath(nome).stem + ".jpg")
            im.save(saida, "JPEG", quality=QUALIDADE, optimize=True, progressive=True)
            print(f"      {saida.name:<18} {largura_orig}px -> {im.width}x{im.height}"
                  f"  {kb(info.file_size)} -> {kb(saida.stat().st_size)}")
            gravados += 1

    print(f"    {gravados} gravadas, {pulados} descartadas -> {destino}")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 1:
        print(__doc__)
        return 2

    pptx = pathlib.Path(args[0]).expanduser()
    if not pptx.is_file():
        print(f"não achei: {pptx}", file=sys.stderr)
        return 1

    if "--map" in sys.argv:
        return mapa(pptx)

    if len(args) < 2:
        print("falta a pasta de saída", file=sys.stderr)
        return 2
    return extrai(pptx, pathlib.Path(args[1]).expanduser())


if __name__ == "__main__":
    raise SystemExit(main())
