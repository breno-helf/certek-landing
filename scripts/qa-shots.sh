#!/usr/bin/env bash
# Tira screenshots da página em várias larguras, para conferir o responsivo.
# Precisa do servidor local rodando (./serve.sh).
#
# Uso:  ./scripts/qa-shots.sh [diretorio-de-saida] [porta]

set -uo pipefail
cd "$(dirname "$0")/.."

OUT="${1:-/tmp/certek-qa}"
PORT="${2:-8080}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

mkdir -p "$OUT"

shot() {  # shot <url> <largura> <altura> <nome>
  local url="$1" w="$2" h="$3" nome="$4"
  local profile
  profile="$(mktemp -d)"
  "$CHROME" \
    --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=1 \
    --window-size="$w,$h" \
    --user-data-dir="$profile" \
    --virtual-time-budget=6000 \
    --screenshot="$OUT/$nome.png" \
    "$url" >/dev/null 2>&1
  rm -rf "$profile"
  if [ -s "$OUT/$nome.png" ]; then
    echo "  OK  $nome.png  (${w}x${h})"
  else
    echo "  FALHOU  $nome  (${w}x${h})"
  fi
}

echo "Screenshots em $OUT"
shot "http://localhost:$PORT/"     390  1400 "pt-mobile"
shot "http://localhost:$PORT/"     768  1400 "pt-tablet"
shot "http://localhost:$PORT/"     1280 1500 "pt-desktop"
shot "http://localhost:$PORT/en/"  1280 1500 "en-desktop"
shot "http://localhost:$PORT/en/"  390  1400 "en-mobile"
echo "pronto"
