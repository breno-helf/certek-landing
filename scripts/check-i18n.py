#!/usr/bin/env python3
"""Compara index.html (PT) e en/index.html (EN) e aponta divergências.

O site é duas cópias de HTML, sem build step. O risco real disso é a
divergência: alguém edita uma seção em português e esquece o inglês. Cada nó
traduzível carrega um atributo data-i18n; este script confere que:

  1. os dois arquivos têm exatamente o mesmo conjunto de chaves
  2. nenhuma chave aparece duas vezes no mesmo arquivo
  3. nenhum texto ficou literalmente igual nos dois (sinal de tradução esquecida)
  4. as duas páginas têm o mesmo número de logos de cliente e de cards de obra
  5. os arquivos referenciados em src/href existem no disco

Saída: 0 se está tudo sincronizado, 1 se há divergência.

Uso:  python3 scripts/check-i18n.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Cada par é uma página em duas línguas. Acrescente aqui ao criar página nova —
# é a única coisa que o checador precisa saber para passar a vigiá-la.
PARES = [
    ("home", ROOT / "index.html", ROOT / "en/index.html"),
    ("trabalhe-conosco", ROOT / "trabalhe-conosco/index.html", ROOT / "en/careers/index.html"),
]

# Chaves cujo texto pode legitimamente ser idêntico nos dois idiomas
# (nomes próprios, siglas, termos que não se traduzem).
IGUAIS_OK = {
    "hero.eyebrow",
    "leed.seal",
    "contact.email",
    "form.emailLabel",
    "works.clara.title",
    "works.klabin.title",
    "works.sca.title",
    "works.goodman.title",
    "segment.industrial.title",
    "works.sca.sector",
    "awards.press",
    "careers.apply.emaillink",
    "careers.apply.linkedin",
}


class Coletor(HTMLParser):
    """Extrai o texto de cada elemento marcado com data-i18n."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.textos: list[tuple[str, str]] = []
        self.pilha: list[str | None] = []
        self.buffer: list[str] = []
        self.contagens = {"client": 0, "work": 0}

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        classes = (d.get("class") or "").split()
        if "client" in classes:
            self.contagens["client"] += 1
        if "work" in classes:
            self.contagens["work"] += 1

        chave = d.get("data-i18n")
        if tag in ("img", "br", "input", "meta", "link", "hr"):
            return  # void: não abre escopo
        self.pilha.append(chave)
        if chave:
            self.buffer.append("")

    def handle_endtag(self, tag):
        if tag in ("img", "br", "input", "meta", "link", "hr"):
            return
        if not self.pilha:
            return
        chave = self.pilha.pop()
        if chave:
            texto = " ".join(self.buffer.pop().split())
            self.textos.append((chave, texto))

    def handle_data(self, data):
        if self.buffer and any(k for k in self.pilha if k):
            self.buffer[-1] += data


def coletar(caminho: pathlib.Path) -> Coletor:
    c = Coletor()
    c.feed(caminho.read_text(encoding="utf-8"))
    return c


def recursos(caminho: pathlib.Path) -> set[pathlib.Path]:
    """Arquivos locais referenciados na página, já resolvidos no disco.

    Os caminhos são relativos à própria página (para o site funcionar tanto na
    raiz quanto numa subpasta do GitHub Pages), então a resolução parte do
    diretório do arquivo HTML.
    """
    html = caminho.read_text(encoding="utf-8")
    achados = re.findall(r'(?:src|href)="([^"#:]+)"', html)
    saida = set()
    for a in achados:
        if a.endswith("/") or a.startswith(("#", "mailto:", "tel:")):
            continue
        saida.add((caminho.parent / a).resolve())
    return saida


def confere(rotulo: str, PT: pathlib.Path, EN: pathlib.Path) -> tuple[list[str], int, dict]:
    problemas: list[str] = []

    for p in (PT, EN):
        if not p.is_file():
            return ([f"{rotulo}: não encontrei {p}"], 0, {"client": 0, "work": 0})

    pt, en = coletar(PT), coletar(EN)
    pt_map, en_map = dict(pt.textos), dict(en.textos)

    # 1. mesmo conjunto de chaves
    so_pt = sorted(set(pt_map) - set(en_map))
    so_en = sorted(set(en_map) - set(pt_map))
    for k in so_pt:
        problemas.append(f"chave só existe no PT: {k}")
    for k in so_en:
        problemas.append(f"chave só existe no EN: {k}")

    # 2. duplicadas — data-i18n repetido no mesmo arquivo é ambíguo.
    # nav.* aparece de propósito no header e no rodapé, então é tolerado.
    for nome, coletado in (("PT", pt), ("EN", en)):
        vistos: dict[str, int] = {}
        for chave, _ in coletado.textos:
            vistos[chave] = vistos.get(chave, 0) + 1
        for chave, n in sorted(vistos.items()):
            if n > 1 and not chave.startswith("nav.") and chave not in {
                "works.status.done",
                "works.status.live",
                "awards.press",
                "careers.cta2",
            }:
                problemas.append(f"{nome}: chave repetida {n}x: {chave}")

    # 3. tradução esquecida
    for chave in sorted(set(pt_map) & set(en_map)):
        if chave in IGUAIS_OK:
            continue
        a, b = pt_map[chave], en_map[chave]
        if a and a == b:
            problemas.append(f"texto idêntico nos dois idiomas: {chave} -> {a[:60]!r}")

    # 4. contagens estruturais
    for campo, nome_campo in (("client", "logos de cliente"), ("work", "cards de obra")):
        if pt.contagens[campo] != en.contagens[campo]:
            problemas.append(
                f"{nome_campo}: PT tem {pt.contagens[campo]}, EN tem {en.contagens[campo]}"
            )

    # 5. JSON-LD: válido nos dois, e a MESMA entidade dos dois lados.
    # O @id compartilhado é o que diz aos buscadores que /pt e /en falam da
    # mesma empresa; se divergir, viram duas organizações distintas — e nada
    # mais neste script olha para dentro do JSON-LD.
    ids = {}
    for nome, caminho in (("PT", PT), ("EN", EN)):
        blocos = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            caminho.read_text(encoding="utf-8"),
            re.S,
        )
        if not blocos:
            problemas.append(f"{nome}: nenhum bloco JSON-LD")
            continue
        for i, bruto in enumerate(blocos, 1):
            try:
                dado = json.loads(bruto)
            except json.JSONDecodeError as e:
                problemas.append(f"{nome}: JSON-LD #{i} inválido — {e}")
                continue
            for no in dado.get("@graph", []):
                tipos = no.get("@type", "")
                if "GeneralContractor" in tipos or "Organization" in tipos:
                    ids[nome] = no.get("@id")
    if len(ids) == 2 and len(set(ids.values())) != 1:
        problemas.append(f"@id da organização difere entre PT e EN: {ids}")

    # 6. arquivos referenciados existem
    for nome, caminho in (("PT", PT), ("EN", EN)):
        for ref in sorted(recursos(caminho)):
            if not ref.exists():
                try:
                    rotulo = ref.relative_to(ROOT)
                except ValueError:
                    rotulo = ref
                problemas.append(f"{nome}: arquivo não encontrado: {rotulo}")

    chaves = len(set(pt_map) | set(en_map))
    return ([f"{rotulo}: {p}" for p in problemas], chaves, pt.contagens)


def main() -> int:
    todos: list[str] = []
    linhas: list[str] = []
    for rotulo, pt_path, en_path in PARES:
        problemas, chaves, cont = confere(rotulo, pt_path, en_path)
        todos.extend(problemas)
        linhas.append(
            f"  {rotulo:<20} {chaves:>3} chaves"
            + (f", {cont['client']} logos, {cont['work']} obras" if cont["client"] else "")
        )

    if todos:
        print(f"{len(todos)} divergência(s):\n")
        for p in todos:
            print(f"  - {p}")
        return 1

    print(f"OK — {len(PARES)} páginas em PT/EN sincronizadas:")
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
