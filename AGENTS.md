# AGENTS.md

Instruções para agentes de código que forem trabalhar neste repositório.
Humanos: veja o `README.md`, que explica o porquê de cada decisão.

## O que é

Landing page institucional bilíngue (pt-BR / en) da **Certek Construtora**,
construtora brasileira sediada em São Paulo. HTML, CSS e JavaScript puros.

## Regra número um: não existe build step

Sem npm, sem bundler, sem framework, sem pré-processador. O que está no
repositório é exatamente o que o navegador recebe. Isso é deliberado, não
provisório:

- a página é servida como HTML estático já renderizado, sem hidratação — é o que
  garante que rastreadores que não executam JavaScript de forma confiável
  (incluindo vários rastreadores de IA) enxerguem a página inteira;
- o próximo a mexer aqui pode ser a agência de marketing da Certek, não um
  engenheiro de front-end.

**Não introduza** React, Vue, Tailwind, Sass, Vite, PostCSS, npm scripts, nem
dependência de CDN. Se uma tarefa parecer exigir isso, o caminho certo quase
sempre é um script utilitário em `scripts/` (Python com a stdlib, ou Pillow via
o venv do diretório pai) que roda uma vez e grava o resultado no repositório.

## Regra número dois: nunca invente fatos sobre a empresa

Esta página fala em nome de uma empresa real, para clientes reais. É proibido
acrescentar: ano de fundação diferente de 2012, número de funcionários, m²
construídos, faturamento, percentual de prazo cumprido, tempo de resposta
prometido, certificações ISO, apólices de seguro, ou qualquer cliente que já
não esteja na página.

Dois números foram fornecidos pela própria Certek (feedback de 05/08/2026) e
podem permanecer exatamente como estão: **+240 projetos entregues** e **+4
obras certificadas LEED**. Não os recalcule, não os arredonde e não os
"atualize" sem nova confirmação da Certek.

Se uma mudança ficaria melhor com um dado desses, **deixe um TODO e diga o que
precisa ser perguntado à Certek** — não estime, não arredonde, não infira a
partir de outro número. A seção "Pendências" do `README.md` é onde esses pedidos
ficam registrados.

Também não use dados do diretório irmão `../certek-streamlit/`: são números
financeiros internos, extraídos do ERP, e são confidenciais.

## Estrutura

```
index.html        página em português (canônica)
en/index.html     página em inglês
assets/css/site.css    folha única — tokens em :root, componentes por seção
assets/css/fonts.css   GERADO por scripts/fetch-fonts.py — não editar à mão
assets/js/site.js      menu mobile, reveal, fallback do formulário
assets/img/            logo, favicons, og:image, fotos de obra, 40 logos de cliente
scripts/               utilitários (ver README)
llms.txt               resumo legível por agente (padrão llmstxt.org)
```

## O HTML é duplicado de propósito

PT e EN são dois arquivos completos. Não há template, não há include.

Toda mudança de conteúdo tem de ser feita **nos dois arquivos**, e cada nó
traduzível carrega `data-i18n="chave"`. Antes de terminar qualquer tarefa:

```bash
python3 scripts/check-i18n.py
```

Ele exige que os dois arquivos tenham exatamente o mesmo conjunto de chaves, que
nenhuma esteja duplicada, que nenhum texto tenha ficado idêntico nos dois idiomas
(sinal de tradução esquecida), que a contagem de logos e de cards de obra bata, e
que todo arquivo referenciado exista no disco. Saída diferente de zero significa
que a tarefa não está pronta.

**O que o checador NÃO vigia** — cuide você:
- o conteúdo dos blocos JSON-LD (podem divergir entre PT e EN sem reclamação);
- os atributos `alt`, que também são conteúdo bilíngue;
- o texto dentro de `<noscript>`.

## Caminhos são relativos, sempre

`index.html` usa `assets/...`; `en/index.html` usa `../assets/...`. Nada de
caminho absoluto começando com `/`: o site é publicado numa subpasta do GitHub
Pages, e caminho absoluto quebra tudo lá. As únicas URLs absolutas legítimas são
`canonical`, `hreflang`, `og:` e o JSON-LD.

## Verificação antes de dar a tarefa por encerrada

```bash
python3 scripts/check-i18n.py     # sincronia PT/EN, obrigatório
node --check assets/js/site.js    # se mexeu no JS
./serve.sh                        # http://localhost:8080  e  /en/
```

Se mexeu em layout, confira em 375, 414 e 768px de largura — não pelo tamanho da
janela do Chrome (ele não desce abaixo de ~500px), e sim com a página dentro de
um `<iframe>` daquela largura, servido da mesma origem. Não pode haver rolagem
horizontal em nenhuma delas.

Se trocou imagem, rode `../bin/python scripts/add-img-dims.py` — sem
`width`/`height` corretos o layout salta enquanto a imagem carrega.

## Coisas que já foram decididas (não desfaça sem motivo novo)

- **Fontes self-hosted, com `unicode-range`.** Não voltar para o CDN do Google.
  E os `@font-face` de Inter usam faixa de peso (`400 700`) porque é uma fonte
  variável: pedir pesos soltos ao Google Fonts baixava o mesmo arquivo quatro
  vezes.
- **Sem minificar CSS.** O GitHub Pages já serve com gzip (31 KB → ~7 KB);
  minificar economizaria menos de 2 KB e criaria um passo de build.
- **Sem analytics de terceiro.** Quebra a política de não depender de CDN e
  implica tratamento de dado pessoal. Medição via Search Console apenas.
- **O formulário não finge.** Enquanto o `action` for `TODO_FORM_ENDPOINT`, o
  `site.js` abre um e-mail pré-preenchido e diz isso ao usuário. Nunca exibir
  mensagem de sucesso sem envio confirmado.
- **`.work__status--live`** parece CSS morto, mas é o badge de "obra em
  andamento", à espera de autorização da Certek. Manter.
