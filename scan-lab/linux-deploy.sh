#!/bin/bash
# lidarMONK Linux Deployment Script
# Version: 1.0.0
# Installiert und konfiguriert lidarMONK auf Linux-Systemen

set -e

# Konfiguration
APP_NAME="lidarMONK"
APP_DIR="${APP_DIR:-$HOME/.local/share/lidarmonk}"
SERVICE_PORT="${PORT:-8080}"
SYSTEMD_USER="lidarmonk"
PYDEPS="numpy open3d==0.20.0 wurld==1.4.0 pymcubes>=0.1.0 flask werkzeug"

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Prüft ob wir als root laufen
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "Bitte nicht als root ausführen. User-Kontext verwenden."
        exit 1
    fi
}

# Prüft Systemvoraussetzungen
check_requirements() {
    log_info "Prüfe Systemvoraussetzungen..."
    
    # Python 3.14+
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 nicht gefunden. Bitte installieren: sudo apt install python3 python3-pip"
        exit 1
    fi
    
    PYVER=$(python3 -c 'import sys; print(sys.version_info.major * 100 + sys.version_info.minor)')
    if [[ $PYVER -lt 314 ]]; then
        log_warn "Python 3.14+ empfohlen. Aktuelle Version: $(python3 --version)"
    fi
    
    # FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        log_warn "FFmpeg nicht gefunden. Stray-Konvertierung wird fehlschlagen."
        log_warn "Installieren mit: sudo apt install ffmpeg"
    fi
    
    # System-Bibliotheken
    if ! pkg-config --exists open3d 2>/dev/null; then
        log_info "Prüfe Open3D-Abhängigkeiten..."
        for lib in libgl1 libgomp1 libegl1 libglib2.0-0; do
            if ! ldconfig -p | grep -q "$lib"; then
                log_warn "Bibliothek $lib nicht gefunden (meist vorhanden)"
            else
                log_info "✓ $lib gefunden"
            fi
        done
    fi
}

# Erstellt User-Service für systemd
create_systemd_service() {
    log_info "Erstelle systemd-User-Service..."
    
    local SERVICE_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SERVICE_DIR"
    
    cat > "$SERVICE_DIR/lidarmonk.service" << 'EOF'
[Unit]
Description=lidarMONK - LiDAR Processing Service
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/lidarMONK/scan-lab
ExecStart=%h/.local/share/lidarmonk/venv/bin/python server.py
Restart=on-failure
RestartSec=5
Environment=FLASK_APP=server.py
Environment=FLASK_ENV=production

[Install]
WantedBy=default.target
EOF

    # Limit für 8GB RAM
    sed -i '/RestartSec/a MemoryMax=8G' "$SERVICE_DIR/lidarmonk.service"
    
    log_info "Service-Datei erstellt: $SERVICE_DIR/lidarmonk.service"
}

# Installation
install() {
    log_info "Starte Installation von $APP_NAME..."
    
    check_root
    check_requirements
    
    # Verzeichnisstruktur
    log_info "Erstelle Verzeichnisstruktur..."
    mkdir -p "$APP_DIR"
    mkdir -p "$APP_DIR/bin"
    mkdir -p "$APP_DIR/logs"
    mkdir -p "$APP_DIR/cache"
    
    # Virtual Environment
    if [[ ! -d "$APP_DIR/venv" ]]; then
        log_info "Erstelle Python Virtual Environment..."
        python3 -m venv "$APP_DIR/venv"
    fi
    
    # Abhängigkeiten installieren
    log_info "Installiere Python-Abhängigkeiten..."
    source "$APP_DIR/venv/bin/activate"
    pip install --upgrade pip setuptools wheel
    pip install $PYDEPS
    
    # Flask im User-Modus (nicht systemweit)
    pip install flask-cors
    
    # Startskript verlinken
    if [[ ! -L "$HOME/.local/bin/lidarmonk" ]]; then
        mkdir -p "$HOME/.local/bin"
        ln -sf "$APP_DIR/venv/bin/python" "$HOME/.local/bin/lidarmonk"
    fi
    
    # Systemd-Service
    create_systemd_service
    
    # Service enablen
    systemctl --user daemon-reload
    systemctl --user enable lidarmonk.service
    
    log_info "Installation abgeschlossen!"
    echo ""
    echo "Nächste Schritte:"
    echo "  1. Starte den Service: systemctl --user start lidarmonk"
    echo "  2. Status prüfen: systemctl --user status lidarmonk"
    echo "  3. Log anzeigen: journalctl --user -u lidarmonk -f"
    echo ""
    echo "Der Service ist erhältlich unter: http://localhost:$SERVICE_PORT"
}

# Deinstallation
uninstall() {
    log_info "Deinstalliere $APP_NAME..."
    
    # Service stoppen
    systemctl --user stop lidarmonk.service 2>/dev/null || true
    systemctl --user disable lidarmonk.service 2>/dev/null || true
    
    # Service-Datei löschen
    rm -f "$HOME/.config/systemd/user/lidarmonk.service"
    systemctl --user daemon-reload
    
    # Anwendungsverzeichnis
    read -p "Completely remove $APP_DIR? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$APP_DIR"
        log_info "Anwendungsverzeichnis gelöscht"
    fi
    
    log_info "Deinstallierung abgeschlossen"
}

# Status anzeigen
status() {
    echo "lidarMONK Status:"
    echo "=================="
    echo "Installation: $APP_DIR"
    echo "Virtual Env: $([ -d "$APP_DIR/venv" ] && echo "✓ vorhanden" || echo "✗ nicht gefunden")"
    echo "Service: $(systemctl --user is-active lidarmonk.service 2>/dev/null || echo "nicht aktiv")"
    echo "Python: $(python3 --version)"
    
    if [[ -f "$APP_DIR/logs"/*.log ]]; then
        echo "Logs:"
        ls -lh "$APP_DIR/logs/"*.log 2>/dev/null | tail -3
    fi
}

# Hilfe
usage() {
    cat << EOF
Usage: $0 {install|uninstall|status|service-start|service-stop|service-restart}

Befehle:
    install         Installation durchführen
    uninstall       Deinstallieren
    status          Status anzeigen
    service-start   Service starten
    service-stop    Service stoppen
    service-restart Service neustarten

Umgebungsvariablen:
    PORT=8080       Port für Web-Oberfläche (default: 8080)
    APP_DIR         Installationsverzeichnis (default: ~/.local/share/lidarmonk)

Sicherheitshinweise:
    - Verwende --lan nur im vertrauenswürdigen lokalen Netz
    - Portfreigaben nicht einrichten (keine Sicherheit)
    - Service läuft als user, nicht als root
EOF
}

# Hauptlogik
case "$1" in
    install)
        install
        ;;
    uninstall)
        uninstall
        ;;
    status)
        status
        ;;
    service-start)
        systemctl --user start lidarmonk.service
        log_info "Service gestartet"
        ;;
    service-stop)
        systemctl --user stop lidarmonk.service
        log_info "Service gestoppt"
        ;;
    service-restart)
        systemctl --user restart lidarmonk.service
        log_info "Service neugestartet"
        ;;
    *)
        usage
        exit 1
        ;;
esac