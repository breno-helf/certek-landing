# Certek — landing page

Landing page institucional da **Certek Construtora**, em português e inglês.
HTML, CSS e JavaScript puros: **sem build step, sem npm, sem framework.**

```bash
./serve.sh          # http://localhost:8080  (PT)  ·  /en/  (EN)
```

---

## Por que existe

O site em `certek.com.br` é montado num construtor no-code (cmsfly) e tem três
problemas concretos:

1. **A dobra inicial fica em branco.** O herói é um vídeo de 15 MB; até ele
   carregar não há nada na tela.
2. **A prova social está enterrada.** A lista de clientes — Klabin, Johnson &
   Johnson, L'Oréal, Albert Einstein, Sírio-Libanês, Hines, adidas, Bayer — vive
   numa subpágina de slug ilegível (`/zu6tiD`) em vez de estar na home.
3. **Não existe versão em inglês**, apesar de boa parte da carteira ser
   multinacional.

Somando: `og:image` vazio (todo link compartilhado saía sem imagem), sem
favicon, sem dados estruturados, e todo o conteúdo preso a um CMS de terceiros.

---

## Estrutura

```
index.html              página em português (canônica em /)
en/index.html           página em inglês (/en/)
assets/
  css/site.css          folha única — tokens, componentes, responsivo
  css/fonts.css         @font-face gerado (não editar à mão)
  fonts/*.woff2         Gentium Book Plus + Inter, self-hosted
  js/site.js            menu mobile, reveal, fallback do formulário
  img/                  logo, favicons, og:image
  img/obras/            fotos das obras
  img/clientes/logos/   42 logos de clientes, recortados das tiras originais
scripts/                utilitários (ver abaixo)
reference/              material de origem — não é servido
robots.txt · sitemap.xml
```

## Scripts

| Script | O que faz |
|---|---|
| `./serve.sh [porta]` | Sobe o servidor local (padrão 8080) |
| `python3 scripts/check-i18n.py` | Confere se PT e EN estão sincronizados |
| `./scripts/fetch-assets.sh` | Rebaixa imagens do CDN do site antigo |
| `python3 scripts/fetch-fonts.py` | Rebaixa as fontes e regenera `fonts.css` |
| `../bin/python scripts/slice-logos.py` | Fatia as tiras de logos em imagens individuais |
| `../bin/python scripts/name-logos.py` | Dá nome aos recortes |
| `../bin/python scripts/prep-logo.py` | Limpa o logo e gera a versão branca |
| `./scripts/make-og-image.sh` | Regenera o `og:image` 1200×630 |

Os scripts com `../bin/python` usam o venv do diretório pai, que já tem Pillow.
`make-og-image.sh` abre o Chrome headless e pode levar 1–2 minutos na primeira
execução.

---

## Como as duas línguas se mantêm em pé

Não há build step, então **o HTML é duplicado** — PT em `index.html`, EN em
`en/index.html`. O risco disso é a divergência: alguém edita uma seção em
português e esquece o inglês.

A mitigação é `scripts/check-i18n.py`. Cada nó traduzível carrega um atributo
`data-i18n="chave"`, e o script confere que:

- os dois arquivos têm exatamente o mesmo conjunto de chaves;
- nenhuma chave está duplicada dentro do mesmo arquivo;
- nenhum texto ficou literalmente igual nos dois idiomas (tradução esquecida);
- os dois têm o mesmo número de logos de cliente e de cards de obra;
- todo arquivo referenciado em `src`/`href` existe no disco.

**Rode antes de cada commit.** Se um dia a página virar várias, aí vale migrar
para algo com componentes (Astro resolve bem); para uma página só, um checador
de 150 linhas custa menos que um toolchain.

---

## Pendências antes de publicar

- [ ] **Endpoint do formulário.** O `action` está como `TODO_FORM_ENDPOINT`.
      Enquanto estiver assim, o `site.js` intercepta o envio e abre um e-mail já
      preenchido — nunca finge que enviou. Para ativar: crie um formulário no
      Formspree (ou use Netlify Forms) e troque o `action` **nos dois arquivos**.
- [ ] **Foto do Hines — 740 Anastácio.** É a obra premiada em 2014, e a imagem
      não é mais recuperável do CDN (o bucket `688fe0a0…` responde 403). Se a
      Certek tiver o original, a seção de reconhecimento ganha muito.
- [ ] **Domínio.** As tags canônicas assumem `https://certek.com.br`. Se o
      primeiro deploy for em outro domínio, é um find-and-replace.

Resolvidos: LinkedIn (`linkedin.com/company/certek-construtora`, no header, no
rodapé e no `sameAs` do JSON-LD) e ano de fundação (2012, no tile de "Números",
no texto de "Quem somos" e no `foundingDate` do JSON-LD).

---

## Regras que a página segue

- **Nada inventado.** Não há headcount, m² construídos nem faturamento. Os
  quatro números da seção "Números" ou são contáveis a partir do material
  público — 42 logos exibidos → "40+ clientes"; 6 segmentos; 3 obras em
  andamento (Clara Resorts, Hines, Yamaha) — ou foram informados pela Certek
  (fundação em 2012).
- **Zero dado financeiro.** Os números do ERP Sienge que existem em
  `../certek-streamlit/` são internos e não aparecem aqui.
- **Só clientes já públicos.** Todos os 42 logos vêm das tiras que a própria
  Certek já publica em `certek.com.br`. Nomes que aparecem apenas no ERP interno
  não foram adicionados.
- **Marcas de terceiros** são exibidas apenas como registro de obras
  executadas, com nota explícita na seção de clientes.

## Acessibilidade e desempenho

- Contraste: `#600a0a` sobre branco = 13,6:1 (AAA). `#ba3a3a` sobre branco =
  5,6:1 (AA para texto normal) — por isso só é usado em acentos e títulos.
- Landmarks semânticos, skip link, foco sempre visível, `prefers-reduced-motion`
  respeitado.
- Com JavaScript desativado a página fica inteira e navegável; só o menu mobile
  degrada (o `nav` continua visível).
- Fontes self-hosted com `unicode-range` correto, logo o navegador baixa só o
  subset que precisa. Imagens com `loading="lazy"` e `width`/`height` para não
  causar deslocamento de layout.
