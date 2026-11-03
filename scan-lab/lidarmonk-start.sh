#!/bin/bash
# lidarMONK Desktop Launcher
# Starts the lidarMONK server and opens the web interface

set -e

# Konfiguration
APP_DIR="$HOME/lidarMONK/scan-lab"
VENV_PYTHON="$HOME/.local/share/lidarmonk/venv/bin/python"
LOG_DIR="$HOME/.local/share/lidarmonk/logs"
SERVER_PORT="${LIDARMONK_PORT:-8765}"
LAUNCH_BROWSER="${LAUNCH_BROWSER:-true}"

# Farben für Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Prüft ob Venv existiert
check_venv() {
    if [[ ! -d "$HOME/.local/share/lidarmonk/venv" ]]; then
        log_info "Virtual Environment nicht gefunden - starte Installation..."
        bash "$APP_DIR/linux-deploy.sh" install
    fi
}

# Startet den Server
start_server() {
    mkdir -p "$LOG_DIR"
    
    cd "$APP_DIR"
    
    # Kill vorhandene Prozesse
    pkill -f "python.*server.py" 2>/dev/null || true
    sleep 1
    
    # Starte Server im Hintergrund
    log_info "Starte lidarMONK Server auf Port $SERVER_PORT..."
    $VENV_PYTHON backend/server.py --port $SERVER_PORT > "$LOG_DIR/server.log" 2>&1 &
    SERVER_PID=$!
    
    # Warte auf Server
    for i in {1..10}; do
        if curl -s http://localhost:$SERVER_PORT/ > /dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
    
    # Hole Token aus Log
    TOKEN=$(grep "Lokal:" "$LOG_DIR/server.log" 2>/dev/null | sed 's/.*http://127.0.0.1:[0-9]*\/#//' | head -1)
    
    if [[ -n "$TOKEN" ]]; then
        log_info "Server gestartet mit Token: ${TOKEN:0:8}..."
    else
        log_info "Server gestartet (Token nicht gelesen)"
    fi
    
    echo "$SERVER_PID" > "$LOG_DIR/server.pid"
}

# Öffnet Browser
open_browser() {
    if [[ "$LAUNCH_BROWSER" == "true" ]]; then
        TOKEN=$(grep "Lokal:" "$LOG_DIR/server.log" 2>/dev/null | sed 's/.*http://127.0.0.1:[0-9]*\/#//' | head -1)
        URL="http://localhost:$SERVER_PORT/#${TOKEN:-}"
        
        log_info "Öffne Browser: $URL"
        
        if command -v google-chrome &> /dev/null; then
            google-chrome "$URL" 2>/dev/null &
        elif command -v firefox &> /dev/null; then
            firefox "$URL" 2>/dev/null &
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$URL" 2>/dev/null &
        else
            log_warn "Kein Browser gefunden. Öffne manuell: $URL"
        fi
    fi
}

# Stoppt den Server
stop_server() {
    if [[ -f "$LOG_DIR/server.pid" ]]; then
        PID=$(cat "$LOG_DIR/server.pid")
        if kill -0 "$PID" 2>/dev/null; then
            log_info "Stoppe Server (PID: $PID)..."
            kill "$PID" 2>/dev/null || true
            rm -f "$LOG_DIR/server.pid"
        fi
    fi
    pkill -f "python.*server.py" 2>/dev/null || true
}

# Zeigt Status
show_status() {
    if curl -s http://localhost:$SERVER_PORT/ > /dev/null 2>&1; then
        TOKEN=$(grep "Lokal:" "$LOG_DIR/server.log" 2>/dev/null | sed 's/.*http://127.0.0.1:[0-9]*\/#//' | head -1)
        echo "lidarMONK läuft auf: http://localhost:$SERVER_PORT/#${TOKEN:-}"
    else
        echo "lidarMONK ist nicht aktiv"
    fi
}

# Hauptlogik
case "${1:-start}" in
    start)
        check_venv
        start_server
        open_browser
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        open_browser
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac