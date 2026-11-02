#!/usr/bin/env bash
# Start the local lidarMONK backend on Linux; --lan opts into home-network access.
set -euo pipefail
umask 077

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
backend_dir="$project_dir/backend"
requirements="$backend_dir/requirements.txt"
data_dir="${XDG_DATA_HOME:-$HOME/.local/share}/lidarmonk"
venv_dir="$data_dir/venv"
state_dir="$data_dir/data"
mode=local
check_only=0
port=8765

usage() {
  cat <<'HELP'
Start:       bash scan-lab/start.sh --lan
Nur lokal:   bash scan-lab/start.sh
Installation prüfen: bash scan-lab/start.sh --check
Optionen: --lan, --check, --port PORT, --help

--lan macht den Server im lokalen Netz über unverschlüsseltes HTTP erreichbar.
Nur im eigenen vertrauenswürdigen WLAN verwenden, niemals Portfreigaben einrichten.
HELP
}
while (($#)); do
  case "$1" in
    --lan) mode=lan; shift ;;
    --check) check_only=1; shift ;;
    --port) if (($# < 2)) || [[ ! "$2" =~ ^[0-9]+$ ]] || ((10#$2 < 1 || 10#$2 > 65535)); then echo 'Ungültiger Port (1–65535).' >&2; exit 2; fi; port="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unbekannte Option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if ! command -v python3 >/dev/null || ! command -v ffmpeg >/dev/null; then
  echo 'Python 3 oder ffmpeg fehlt. Unter Linux Mint installieren mit:' >&2
  echo 'sudo apt install python3 python3-venv ffmpeg libgl1 libglib2.0-0' >&2
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(not ((3, 10) <= sys.version_info[:2] <= (3, 14)))'; then
  echo 'Benötigt Python 3.10 bis 3.14; auf Mint 22 sollte Python 3.12 vorhanden sein.' >&2
  exit 1
fi
mkdir -p -- "$data_dir" "$state_dir"
if [[ ! -x "$venv_dir/bin/python" ]]; then
  echo 'Erstelle einmalig eine Python-Umgebung …'
  if ! python3 -m venv "$venv_dir"; then
    echo 'Python-Umgebung konnte nicht erstellt werden. Unter Mint: sudo apt install python3-venv' >&2
    exit 1
  fi
fi
req_hash="$(sha256sum "$requirements" | cut -d ' ' -f 1)"
installed_hash="$(cat "$venv_dir/lidarmonk-requirements.sha256" 2>/dev/null || true)"
if [[ "$req_hash" != "$installed_hash" ]] || ! "$venv_dir/bin/python" -c 'import numpy, open3d, skimage, wurld' >/dev/null 2>&1; then
  echo 'Installiere oder aktualisiere die benötigten Python-Pakete. Das kann einige Minuten dauern …'
  "$venv_dir/bin/python" -m pip install -r "$requirements"
  "$venv_dir/bin/python" -c 'import numpy, open3d, skimage, wurld'
  printf '%s\n' "$req_hash" > "$venv_dir/lidarmonk-requirements.sha256"
fi
printf 'Datenordner: %s\n' "$state_dir"
if ((check_only)); then
  echo 'Abhängigkeiten sind geladen; Installation ist bereit.'
  exit 0
fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
args=(--data "$state_dir" --port "$port")
if [[ "$mode" == lan ]]; then args+=(--lan); fi
echo 'Mit Strg+C stoppen.'
exec "$venv_dir/bin/python" -u "$backend_dir/server.py" "${args[@]}"
