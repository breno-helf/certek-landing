#!/usr/bin/env bash
# Sobe a landing page num servidor estático local.
#
#   ./serve.sh          -> http://localhost:8080
#   ./serve.sh 3000     -> http://localhost:3000
#
# É preciso servir por HTTP (e não abrir o index.html com file://) porque os
# caminhos são absolutos a partir da raiz — /assets/..., /en/ — que é como o
# site vai funcionar em produção.

set -euo pipefail
cd "$(dirname "$0")"

PORT="${1:-8080}"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "A porta $PORT já está em uso. Rode ./serve.sh <outra-porta>." >&2
  exit 1
fi

echo "Certek — landing page"
echo "  PT  http://localhost:$PORT/"
echo "  EN  http://localhost:$PORT/en/"
echo
echo "Ctrl+C para parar."
echo

exec python3 -m http.server "$PORT" --bind 127.0.0.1
