#!/usr/bin/env bash
# Gera assets/img/og-certek.jpg (1200x630) — a imagem que aparece quando o link
# do site é colado no WhatsApp, LinkedIn ou Slack.
#
# O site antigo tinha <meta property="og:image" content="https://cdn.cmsfly.com/">
# — uma URL vazia — então todo compartilhamento saía sem imagem.
#
# Renderiza scripts/og-image.html com o Chrome headless e converte para JPEG.
# Uso:  ./scripts/make-og-image.sh

set -euo pipefail
cd "$(dirname "$0")/.."

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ ! -x "$CHROME" ]; then
  for alt in \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "$(command -v chromium || true)" \
    "$(command -v google-chrome || true)"; do
    if [ -n "$alt" ] && [ -x "$alt" ]; then CHROME="$alt"; break; fi
  done
fi

if [ ! -x "$CHROME" ]; then
  echo "Chrome headless não encontrado — pulei a geração do og:image." >&2
  echo "Instale o Chrome ou gere assets/img/og-certek.jpg à mão (1200x630)." >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

"$CHROME" \
  --headless \
  --disable-gpu \
  --hide-scrollbars \
  --force-device-scale-factor=1 \
  --window-size=1200,630 \
  --screenshot="$TMP/og.png" \
  --user-data-dir="$TMP/profile" \
  --virtual-time-budget=4000 \
  "file://$(pwd)/scripts/og-image.html" >/dev/null 2>&1

if [ ! -s "$TMP/og.png" ]; then
  echo "o Chrome não produziu a imagem" >&2
  exit 1
fi

# PNG -> JPEG: og:image não precisa de transparência e o JPEG fica bem menor.
../bin/python - "$TMP/og.png" assets/img/og-certek.jpg <<'PY'
import sys
from PIL import Image
src, dest = sys.argv[1], sys.argv[2]
img = Image.open(src).convert("RGB").resize((1200, 630), Image.LANCZOS)
img.save(dest, "JPEG", quality=88, optimize=True, progressive=True)
print(f"{dest}  {img.size[0]}x{img.size[1]}")
PY

echo "og:image gerado — $(du -h assets/img/og-certek.jpg | cut -f1)"
