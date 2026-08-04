#!/usr/bin/env python3
"""Preenche width/height nas <img> dos logos de cliente, nos dois HTMLs.

Sem esses atributos a imagem ocupa 0x0 até carregar. Isso tem dois efeitos
ruins: o navegador não reserva espaço (layout shift quando o logo aparece) e
um elemento de área zero é um caso de borda ruim para o loading="lazy".

Lê a dimensão real de cada PNG e escreve no HTML. Idempotente: rodar de novo
apenas atualiza os valores.

Uso:  ../bin/python scripts/add-img-dims.py
"""

import pathlib
import re
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGINAS = [ROOT / "index.html", ROOT / "en/index.html"]

# só mexemos nos logos de cliente; as fotos de obra já têm width/height à mão
ALVO = re.compile(r'<img src="(/assets/img/clientes/logos/[^"]+)"([^>]*?)>')
DIM = re.compile(r'\s(?:width|height)="\d+"')


def main() -> int:
    total = 0
    for pagina in PAGINAS:
        if not pagina.is_file():
            print(f"não encontrei {pagina}", file=sys.stderr)
            return 1

        html = pagina.read_text(encoding="utf-8")
        faltando: list[str] = []

        def troca(m: re.Match) -> str:
            src, resto = m.group(1), m.group(2)
            arquivo = ROOT / src.lstrip("/")
            if not arquivo.is_file():
                faltando.append(src)
                return m.group(0)
            w, h = Image.open(arquivo).size
            resto = DIM.sub("", resto).rstrip()
            return f'<img src="{src}"{resto} width="{w}" height="{h}">'

        novo, n = ALVO.subn(troca, html)
        if faltando:
            for f in faltando:
                print(f"  arquivo ausente: {f}", file=sys.stderr)
            return 1

        pagina.write_text(novo, encoding="utf-8")
        print(f"{pagina.relative_to(ROOT)}: {n} imagens dimensionadas")
        total += n

    print(f"{total} no total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
