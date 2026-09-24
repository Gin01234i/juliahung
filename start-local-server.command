#!/usr/bin/env bash

set -euo pipefail

# Always serve the website folder, even when this script is launched by
# double-clicking it from Finder or called from another directory.
cd "$(dirname "$0")"

port="${1:-8000}"
if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
  echo "Usage: ./start-local-server.command [port]"
  echo "Example: ./start-local-server.command 8001"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required to preview this website."
  exit 1
fi

url="http://localhost:${port}"

echo
echo "Julia Hung website preview"
echo "Opening ${url}"
echo "Press Control-C here to stop the server."
echo

# Open the preview after the server has had a moment to start. NO_OPEN=1 is
# useful for automated checks and remote shells.
if [[ "${NO_OPEN:-}" != "1" ]] && command -v open >/dev/null 2>&1; then
  (sleep 1; open "$url") &
elif [[ "${NO_OPEN:-}" != "1" ]] && command -v xdg-open >/dev/null 2>&1; then
  (sleep 1; xdg-open "$url") &
fi

exec python3 -m http.server "$port" --bind 127.0.0.1
