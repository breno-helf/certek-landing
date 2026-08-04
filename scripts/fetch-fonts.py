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

# Peça FAIXAS de peso (wght@400..700), não pesos soltos (wght@400;500;600;700).
#
# O Google Fonts serve Inter como fonte VARIÁVEL: pedindo pesos soltos ele
# devolve a MESMA URL de arquivo em cada bloco @font-face. Salvando um arquivo
# por peso, gravamos quatro cópias byte-idênticas (md5 igual) e o navegador
# baixava 47 KB quatro vezes — 145 KB desperdiçados em toda visita fria.
#
# Com faixa, emitimos um @font-face por família+subset com `font-weight: 400 700`,
# e o navegador baixa um arquivo que cobre todos os pesos.
#
# Gentium Book Plus NÃO é variável: ali os pesos são arquivos de verdade, e o
# deduplicador abaixo não encontra repetição. Por isso a lógica é por hash, não
# por suposição sobre a família.
FAMILIES = [
    ("Gentium+Book+Plus:wght@400;700", "Gentium Book Plus", "gentium"),
    ("Inter:wght@400..700", "Inter", "inter"),
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
    for antigo in FONTDIR.glob("*.woff2"):
        antigo.unlink()  # o nome dos arquivos mudou; não deixar órfão para trás

    faces: list[str] = []
    count = 0

    for query, family, slug in FAMILIES:
        print(f"==> {family}")
        css = get(f"https://fonts.googleapis.com/css2?family={query}&display=swap").decode()

        # Junta os blocos por (subset, estilo, ARQUIVO). Se dois pesos apontam
        # para o mesmo binário, viram uma face só com faixa de peso.
        grupos: dict[tuple[str, str, str], dict] = {}
        for m in BLOCK_RE.finditer(css):
            subset = m.group("subset")
            if subset not in SUBSETS:
                continue
            body = m.group("body")
            src = re.search(r"url\(([^)]+)\)", field(body, "src"))
            if not src:
                continue
            url = src.group(1)
            style = field(body, "font-style") or "normal"
            peso = field(body, "font-weight") or "400"

            chave = (subset, style, url)
            g = grupos.setdefault(
                chave,
                {"url": url, "subset": subset, "style": style,
                 "urange": field(body, "unicode-range"), "pesos": []},
            )
            g["pesos"].append(peso)

        for g in grupos.values():
            # "400 700" (faixa variável) ou "600" (peso único)
            numeros = []
            for p in g["pesos"]:
                numeros.extend(int(n) for n in re.findall(r"\d+", p))
            peso_css = str(min(numeros)) if min(numeros) == max(numeros) \
                else f"{min(numeros)} {max(numeros)}"
            sufixo = "" if len(grupos) <= len(SUBSETS) else f"-{min(numeros)}"

            name = f"{slug}{sufixo}-{g['subset']}.woff2"
            (FONTDIR / name).write_bytes(get(g["url"]))
            size = (FONTDIR / name).stat().st_size
            print(f"   {name:<32} peso {peso_css:<9} {size // 1024:>3} KB")

            face = [
                "@font-face {",
                f"  font-family: '{family}';",
                f"  font-style: {g['style']};",
                f"  font-weight: {peso_css};",
                "  font-display: swap;",
                f"  src: url('../fonts/{name}') format('woff2');",
            ]
            if g["urange"]:
                face.append(f"  unicode-range: {g['urange']};")
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
