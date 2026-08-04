#!/usr/bin/env bash
# Baixa os assets da Certek do CDN do CMS atual para assets/img/.
#
# Contexto importante: o cdn.cmsfly.com serve DOIS buckets e um deles morreu.
#   68c3fec4ed3b7600500f003a  -> ativo, responde 200
#   688fe0a050e5450020582667  -> morto, responde 403 com um XML de erro
# Por isso usamos `curl -f`: sem ele o curl gravaria o XML de erro num arquivo
# .jpg e a página ficaria com imagem quebrada sem ninguém perceber.
#
# Uso:  ./scripts/fetch-assets.sh [--with-video]
#       --with-video  baixa também os dois MP4 (22,7 MB). Eles NÃO são usados
#                     na dobra inicial; ficam disponíveis caso se queira um
#                     vídeo mais abaixo na página, depois de comprimir.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

CDN="https://cdn.cmsfly.com/68c3fec4ed3b7600500f003a"
LOGO_CDN="https://cdn.cmsfly.com/6534e3e885f4bd0012ee789d"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"

ok=0; fail=0; failed_list=()

get() {  # get <url> <destino>
  local url="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if curl -fsSL --retry 2 --max-time 60 -A "$UA" "$url" -o "$dest"; then
    printf '  OK      %-42s %s\n' "$(basename "$dest")" "$(du -h "$dest" | cut -f1)"
    ok=$((ok + 1))
  else
    printf '  FALHOU  %-42s %s\n' "$(basename "$dest")" "$url"
    rm -f "$dest"
    fail=$((fail + 1))
    failed_list+=("$dest")
  fi
}

echo "==> Identidade"
get "$LOGO_CDN/logo3-PKdLvZ.png"            assets/img/logo-certek.png
get "$CDN/images/favicon-qiSC7.png"         assets/img/favicon.png

echo "==> Obras"
get "$CDN/images/clararesorts1-pcm1a.jpg"   assets/img/obras/clara-resorts-1.jpg
get "$CDN/images/clararesorts2-nViDT.jpg"   assets/img/obras/clara-resorts-2.jpg
get "$CDN/images/clararesorts3-zi8PI.jpg"   assets/img/obras/clara-resorts-3.jpg
get "$CDN/images/clararesorts5-Z6q2o.jpg"   assets/img/obras/clara-resorts-4.jpg
get "$CDN/images/Klabin1-Br6pA.jpg"         assets/img/obras/klabin.jpg
get "$CDN/images/sca-1-xtvfd.jpg"           assets/img/obras/sca-1.jpg
get "$CDN/images/sca-21-Jd63-.jpg"          assets/img/obras/sca-2.jpg
get "$CDN/images/good1-9yi1t.jpg"           assets/img/obras/goodman.jpg

echo "==> Logos de clientes (só existem estes três em imagem)"
get "$CDN/images/eurofarma-hsMt2.jpeg"      assets/img/clientes/eurofarma.jpg
get "$CDN/images/hinespng-NRN4d.png"        assets/img/clientes/hines.png
get "$CDN/images/klabinpng-VWBjK.png"       assets/img/clientes/klabin.png

echo "==> Imagens não identificadas (possíveis certificados/prêmios)"
for n in 2-NGKAy 3-nQtjQ 4-PtkfG 5-elvio 12-M6ke9 62-Zj9X5 72-w7OsE; do
  get "$CDN/images/$n.png" "assets/img/_inspecionar/${n%%-*}.png"
done

if [[ "${1:-}" == "--with-video" ]]; then
  echo "==> Vídeos (grandes — não usados na dobra inicial)"
  get "$CDN/videos/Upto138-xkoQa.mp4"       assets/video/hero-long.mp4
  get "$CDN/videos/Upto1317-BuSvI.mp4"      assets/video/hero-short.mp4
fi

# Indisponíveis: estes ficam registrados aqui para não se perder o rastro.
# O bucket 688fe0a050e5450020582667 responde 403 — as imagens abaixo não são
# mais recuperáveis do CDN e precisam vir do arquivo original da Certek:
#   Barzel1-S-EOh.jpg          -> foto da obra Barzel Properties
#   hines-anastacio-1-Z4JGF.jpg-> foto do Hines 740 Anastácio (obra premiada em 2014)
#   hinesp2-7oJvv.jpg          -> idem

echo
echo "-------------------------------------------"
printf 'Baixados: %d   Falharam: %d\n' "$ok" "$fail"
if (( fail > 0 )); then
  echo "Falhas:"
  printf '  - %s\n' "${failed_list[@]}"
fi
echo "Total em disco: $(du -sh assets/img 2>/dev/null | cut -f1)"
