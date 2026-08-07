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
carreiras/              página de carreiras em português
trabalhe-conosco/       stub de redirect para /carreiras/ (rota antiga)
en/careers/             página de carreiras em inglês
assets/
  css/site.css          folha única — tokens, componentes, responsivo
  css/fonts.css         @font-face gerado (não editar à mão)
  fonts/*.woff2         Gentium Book Plus + Inter, self-hosted
  js/site.js            menu mobile, reveal, fallback do formulário
  img/                  logo, favicons, og:image
  img/obras/            fotos das obras
  img/clientes/logos/   47 logos de clientes, recortados das tiras originais
scripts/                utilitários (ver abaixo)
reference/              material de origem — não é servido
llms.txt                resumo legível por agente (padrão llmstxt.org)
AGENTS.md               instruções para agentes de código que editarem o repo
robots.txt · sitemap.xml
```

O material que a Certek enviou em 07/08/2026 (os decks `.pptx` de obras, o deck
`Experiencia Certek Leed.pptx` e o documento com a ficha técnica) **não está no
repositório** — fica no Drive, junto com o resto do material do cliente. Do que
veio, só os arquivos de logo foram commitados, em
`reference/cassiano-2026-08/`, porque são a origem de imagens que o site serve.

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
| `../bin/python scripts/optimize-images.py` | Recomprime logos e fotos (`--dry-run` para simular) |
| `../bin/python scripts/add-img-dims.py` | Escreve `width`/`height` reais em toda `<img>` |
| `./scripts/qa-shots.sh` | Screenshots em várias larguras via Chrome headless |

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
- todo arquivo referenciado em `src`/`href` existe no disco;
- os blocos JSON-LD são válidos e a organização tem o **mesmo `@id`** dos dois
  lados — é isso que diz aos buscadores que `/` e `/en/` falam da mesma empresa.

O que ele ainda **não** vigia, e você precisa conferir à mão: o conteúdo dos
`alt` (também é texto bilíngue) e o que está dentro de `<noscript>`.

Ele cobre **todos os pares de página** listados em `PARES`, no topo do script.
Ao criar uma página nova, acrescente o par ali — é a única coisa que ele precisa
saber para passar a vigiá-la.

**Rode antes de cada commit.** Se um dia a página virar várias, aí vale migrar
para algo com componentes (Astro resolve bem); para uma página só, um checador
de 150 linhas custa menos que um toolchain.

---

## Pendências antes de publicar

- [ ] **Endpoint do formulário.** O `action` está como `TODO_FORM_ENDPOINT`.
      Enquanto estiver assim, o `site.js` intercepta o envio e abre um e-mail já
      preenchido — nunca finge que enviou. Para ativar: crie um formulário no
      Formspree (ou use Netlify Forms) e troque o `action` **nos dois arquivos**.
- [ ] **Domínio.** As URLs absolutas apontam para
      `https://breno-helf.github.io/certek-landing`, que é onde o site está
      publicado hoje. Quando `certek.com.br` passar a servir esta página, é um
      find-and-replace nos dois HTMLs, no `robots.txt`, no `sitemap.xml` e no
      `llms.txt`.
- [ ] **Registros profissionais.** Faltam o registro da PJ no CREA-SP, o nome e
      o número CREA do responsável técnico, e a inscrição municipal (CCM-SP).
      O CNPJ já está publicado — ver abaixo.
- [ ] **Ficha técnica das obras: falta o ano e o tipo de contrato.** Cidade/UF e
      área construída vieram no material de 07/08/2026 e já estão publicadas na
      linha de dados de cada card. Ano de conclusão e regime de contratação
      continuam sem fonte — sem eles o `ItemList` do JSON-LD fica sem data.
- [ ] **Cidade do Galpão G1 (Hines, LEED).** O documento dá a área
      (36.862,88 m²) e o Distribution Park I, mas não a cidade; o cliente lista
      três endereços para a Hines (São Paulo, Cajamar e Embu das Artes). Enquanto
      não confirmar, o card cita a obra sem cidade.
- [ ] **Divergência na área de reforma da Nivea/Beiersdorf.** O documento diz
      "reformar = 6.850 m²"; o deck `Experiencia Certek Leed.pptx` diz
      "Reforma: 11.675,00 m²". A página usa o número do deck (11.675 m², o mais
      recente). Confirmar com a Certek qual vale.
- [ ] **Automação de resposta do WhatsApp.** Antes de divulgar mais o canal
      (botão flutuante, campanhas), validar com o Mauro se a resposta automática
      está funcionando — hoje o número aparece no contato e no rodapé.
- [ ] **Migração de hosting para a LocalWeb, via FTP.** O site está hoje no
      GitHub Pages; o find-and-replace de domínio descrito acima acontece nesse
      momento, junto com a subida por FTP.
- [ ] **Logo e nome do IBCC.** O arquivo enviado em 07/08/2026 é de outra
      identidade ("ibcc oncologia", branco sobre azul sólido — viraria um bloco
      cinza no mosaico em grayscale), então o logo antigo foi mantido. As fontes
      também divergem no nome por extenso ("Combate" no deck, "Controle" no logo
      atual). Confirmar com a Certek qual identidade e grafia valem.
- [ ] **Facebook e Compliance.** O feedback pede link do Facebook e link de
      Compliance na seção de contato. Faltam a URL da página no Facebook e a
      página (ou documento) de Compliance. O LinkedIn já está no contato.
- [ ] **Recorrência.** Quais clientes contrataram mais de uma vez. É o sinal
      mais forte do setor e hoje nenhum logo prova.

Resolvidos no material de 07/08/2026:

- **Foto do Hines — 740 Anastácio.** O deck `Experiencia Certek Leed.pptx`
  trazia uma foto do átrio (699 px, máximo disponível no deck); ela está na
  seção de reconhecimento, sob os três prêmios que citam a obra.

- **Logos que faltavam no mural.** Bosch, Yamaha Motor, Farmarin, ECM5, CMPC e
  Grupo São Joaquim entraram — o mural foi de 41 para 47 logos.
- **Logo da GLP.** O cliente confirmou que a GLP mantém a marca clássica depois
  da aquisição pela Marq Logistics e enviou o arquivo em 07/08/2026; o logo
  exibido está correto.
- **Obra farmacêutica divulgável.** A Eurofarma (Edifício de Inovação e
  Biotecnologia, Itapevi/SP) fecha a lacuna que existia num shortlist de farma.
- **Obras para os demais filtros de segmento.** Farmacêutico, automotivo,
  hospitalar e celulose passaram a ter card próprio (Eurofarma, Yamaha Motor,
  IBCC e Klabin, respectivamente).
- **LEED nomeado.** As quatro obras LEED estão citadas na seção de
  sustentabilidade: Nivea/Beiersdorf (Projeto Footprint fase 2, Itatiba/SP),
  Hines 740 Anastácio (São Paulo/SP, LEED Silver), Hines Galpão G9 (Embu das
  Artes/SP) e o retrofit do Galpão G1 (Distribution Park I).
- **Autorização de citação por cliente.** A Certek confirmou em 07/08/2026 que
  não há restrição para citar os clientes e as obras deste material.

Resolvidos antes: LinkedIn (`linkedin.com/company/certek-construtora`, no header, no
rodapé e no `sameAs` do JSON-LD), ano de fundação (2012, no tile de "Números",
no texto de "Quem somos" e no `foundingDate` do JSON-LD) e **CNPJ da matriz,
`15.815.166/0001-33`** — na linha legal do rodapé, no `taxID` e no `identifier`
do JSON-LD, e no `llms.txt`.

O CNPJ não veio do cliente: foi conferido em duas fontes públicas independentes
que batem com o que a página já afirma — mesmo endereço (Renato Paes de Barros,
618, conj. 37, Itaim Bibi, CEP 04530-000) e abertura em 18/05/2012, situação
ATIVA. Existe uma filial em Ortigueira (PR), `15.815.166/0002-14`, deliberadamente
não publicada: a página fala pela matriz.

---

## Regras que a página segue

- **Nada inventado.** Não há headcount, m² construídos nem faturamento. Os
  cinco tiles da seção "Números" são: **2012** (fundação, confirmada pela
  Certek e pelo registro público), **+240 projetos entregues** (número
  informado pela própria Certek no feedback de 05/08/2026 — não veio do ERP e
  não deve ser "atualizado" sem nova confirmação), **+40** (contável — são 47
  logos exibidos), **6** (contável — são 6 segmentos com card próprio) e
  **LEED, +4 obras certificadas** (o "+4" também veio do feedback da Certek de
  05/08/2026). O tile "obras em andamento" foi retirado por ser o único que
  envelhecia sozinho em dois arquivos sem data na página.
  O LinkedIn da Certek declara 51–200 funcionários; a regra de não publicar
  headcount vale mesmo assim, inclusive na página de carreiras.
- **Zero dado financeiro.** Os números do ERP Sienge que existem em
  `../certek-streamlit/` são internos e não aparecem aqui.
- **Só clientes já públicos.** Os 41 logos originais vêm das tiras que a própria
  Certek já publica em `certek.com.br`; os 6 acrescentados em 07/08/2026 (Bosch,
  Yamaha Motor, Farmarin, ECM5, CMPC e Grupo São Joaquim) vieram de arquivos
  enviados pela própria Certek, com autorização de citação confirmada na mesma
  data. Nomes que aparecem apenas no ERP interno não foram adicionados.
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
