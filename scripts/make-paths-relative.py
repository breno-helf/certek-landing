#!/usr/bin/env python3
"""Converte os caminhos absolutos dos HTMLs em caminhos relativos.

Motivo: caminhos absolutos (/assets/..., /en/) só funcionam quando o site está
na raiz do domínio. No GitHub Pages de um repositório de projeto o site fica em
usuario.github.io/certek-landing/, e todo /assets/... apontaria para
usuario.github.io/assets/... — ou seja, 404 em tudo.

Com caminhos relativos a página funciona na raiz, em subpasta, e até aberta
direto do disco.

  index.html      /assets/x  ->  assets/x     |  href="/"     -> "./"    |  "/en/" -> "en/"
  en/index.html   /assets/x  ->  ../assets/x  |  href="/en/"  -> "./"    |  "/"    -> "../"

As URLs absolutas de canonical, hreflang e og: continuam apontando para
https://certek.com.br — é lá que o site vai morar de verdade, e manter o
canonical evita que a cópia no GitHub Pages concorra no índice do Google.

Idempotente. Uso:  python3 scripts/make-paths-relative.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (arquivo, prefixo para assets, destino do link PT, destino do link EN)
PAGINAS = [
    (ROOT / "index.html", "", "./", "en/"),
    (ROOT / "en/index.html", "../", "../", "./"),
]


def converter(html: str, prefixo: str, alvo_pt: str, alvo_en: str) -> str:
    # 1. assets: src="/assets/..." e href="/assets/..."
    html = re.sub(r'((?:src|href)=")/(assets/)', rf'\1{prefixo}\2', html)

    # 2. links de navegação entre idiomas e marca.
    #    Só os href que são exatamente "/" ou "/en/" — não tocar em URLs absolutas.
    html = re.sub(r'href="/en/"', f'href="{alvo_en}"', html)
    html = re.sub(r'href="/"', f'href="{alvo_pt}"', html)

    return html


def main() -> int:
    for pagina, prefixo, alvo_pt, alvo_en in PAGINAS:
        if not pagina.is_file():
            print(f"não encontrei {pagina}", file=sys.stderr)
            return 1

        original = pagina.read_text(encoding="utf-8")
        novo = converter(original, prefixo, alvo_pt, alvo_en)
        pagina.write_text(novo, encoding="utf-8")

        restantes = re.findall(r'(?:src|href)="(/[^"]*)"', novo)
        estado = "sem caminhos absolutos" if not restantes else f"AINDA ABSOLUTOS: {restantes}"
        print(f"{pagina.relative_to(ROOT)}: {estado}")
        if restantes:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
