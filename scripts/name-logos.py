#!/usr/bin/env python3
"""Dá nome aos logos fatiados por slice-logos.py.

O mapeamento vem da leitura visual de cada tira original: os logos aparecem da
esquerda para a direita, e slice-logos.py numera na mesma ordem.

Uso:  ../bin/python scripts/name-logos.py
"""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "assets/img/clientes/raw"
OUT = ROOT / "assets/img/clientes/logos"

NOMES = {
    # tira 2 — diagnósticos e saúde
    "2-1": "cdb",
    "2-2": "ibcc",
    "2-3": "dasa",
    "2-4": "alliar",
    "2-5": "salomao-zoppi",
    "2-6": "general-electric",
    # tira 3 — varejo, hotelaria e incorporação
    "3-1": "ecm5",
    "3-2": "pylos-yoo2",
    "3-3": "cultura-inglesa",
    "3-4": "embracon",
    "3-5": "copart",
    "3-6": "decathlon",
    # tira 4 — farmacêutico
    "4-1": "allergan",
    "4-2": "johnson-johnson",
    "4-3": "ache",
    "4-4": "janssen-cilag",
    "4-5": "eurofarma",
    "4-6": "chiesi",
    # tira 5 — indústria e bens de consumo
    "5-1": "essity",
    "5-2": "sca",
    "5-3": "ype",
    "5-4": "ceva",
    "5-5": "cba",
    "5-6": "votorantim",
    # tira 12 — indústria e cosméticos
    "12-1": "klabin",
    "12-2": "bayer",
    "12-3": "loreal",
    "12-4": "ashland",
    "12-5": "beiersdorf",
    "12-6": "nivea",
    # tira 62 — logística, imobiliário e varejo
    "62-1": "hines",
    "62-2": "adidas",
    "62-3": "goodman",
    "62-4": "abb",
    "62-5": "barzel",
    "62-6": "glp",
    # tira 72 — hospitais
    "72-1": "sao-camilo",
    "72-2": "sirio-libanes",
    "72-3": "albert-einstein",
    "72-4": "ac-camargo",
    "72-5": "afip",
}


def main() -> int:
    if not RAW.is_dir():
        print(f"rode slice-logos.py antes: {RAW} não existe", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    faltando = [k for k in NOMES if not (RAW / f"{k}.png").is_file()]
    if faltando:
        print(f"recortes ausentes: {', '.join(sorted(faltando))}", file=sys.stderr)
        return 1

    for origem, nome in NOMES.items():
        shutil.copyfile(RAW / f"{origem}.png", OUT / f"{nome}.png")

    sobrando = sorted(p.stem for p in RAW.glob("*.png") if p.stem not in NOMES)
    if sobrando:
        print(f"recortes sem nome (ignorados): {', '.join(sobrando)}")

    print(f"{len(NOMES)} logos nomeados em {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
