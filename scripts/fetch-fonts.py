#!/usr/bin/env python3
"""Baixa Gentium Book Plus (títulos) e Inter (corpo) do Google Fonts como .woff2
e gera assets/css/fonts.css com @font-face apontando para os arquivos locais.

Por que self-hosted em vez do CDN do Google:
  - a página fica autocontida (abre offline, não quebra se o CDN sair do ar)
  - tira um terceiro do caminho crítico de renderização
  - evita a requisição ao Google em toda visita (privacidade / LGPD)

Só os subsets latin e latin-ext — é o que o português precisa (ã, ç, ê, õ).
O `unicode-range` de cada bloco é preservado: sem ele o navegador não saberia
qual dos dois arquivos usar para cada caractere e baixaria os dois sempre.

Uso:  python3 scripts/fetch-fonts.py
"""

import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTDIR = ROOT / "assets/fonts"
CSSOUT = ROOT / "assets/css/fonts.css"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SUBSETS = ("latin", "latin-ext")

FAMILIES = [
    ("Gentium+Book+Plus:wght@400;700", "Gentium Book Plus", "gentium"),
    ("Inter:wght@400;500;600;700", "Inter", "inter"),
]

BLOCK_RE = re.compile(r"/\*\s*(?P<subset>[\w-]+)\s*\*/\s*@font-face\s*\{(?P<body>[^}]*)\}")


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def field(body: str, name: str) -> str:
    m = re.search(rf"{name}\s*:\s*([^;]+);", body)
    return m.group(1).strip() if m else ""


def main() -> int:
    FONTDIR.mkdir(parents=True, exist_ok=True)
    faces: list[str] = []
    count = 0

    for query, family, slug in FAMILIES:
        print(f"==> {family}")
        css = get(f"https://fonts.googleapis.com/css2?family={query}&display=swap").decode()

        for m in BLOCK_RE.finditer(css):
            subset = m.group("subset")
            if subset not in SUBSETS:
                continue
            body = m.group("body")
            weight = field(body, "font-weight") or "400"
            style = field(body, "font-style") or "normal"
            urange = field(body, "unicode-range")
            src = re.search(r"url\(([^)]+)\)", field(body, "src"))
            if not src:
                continue

            name = f"{slug}-{weight}-{subset}.woff2"
            (FONTDIR / name).write_bytes(get(src.group(1)))
            size = (FONTDIR / name).stat().st_size
            print(f"   {name:<34} {size // 1024:>3} KB")

            face = [
                "@font-face {",
                f"  font-family: '{family}';",
                f"  font-style: {style};",
                f"  font-weight: {weight};",
                "  font-display: swap;",
                f"  src: url('../fonts/{name}') format('woff2');",
            ]
            if urange:
                face.append(f"  unicode-range: {urange};")
            face.append("}")
            faces.append("\n".join(face))
            count += 1

    if not faces:
        print("nenhuma face baixada", file=sys.stderr)
        return 1

    CSSOUT.write_text(
        "/* Gerado por scripts/fetch-fonts.py — não editar à mão. */\n\n"
        + "\n\n".join(faces)
        + "\n"
    )
    total = sum(p.stat().st_size for p in FONTDIR.glob("*.woff2"))
    print(f"\n{count} faces · {total // 1024} KB em {FONTDIR.relative_to(ROOT)}")
    print(f"CSS gerado em {CSSOUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
