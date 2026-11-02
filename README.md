# lidarMONK

Ein experimentelles LiDAR-Testlabor für Scans vom iPhone. Das Python-Backend läuft auf einem Linux-Rechner; die Upload-Oberfläche lässt sich im Heimnetz mit Safari auf dem iPhone öffnen. Für die Verarbeitung selbst ist keine dedizierte Grafikkarte nötig.

## Schnellstart auf Linux Mint

Voraussetzungen: 64-Bit-Linux, Python 3.10–3.14 (erprobt: 3.12), `ffmpeg` und bei der ersten Einrichtung Internet für Python-Pakete. Für Mint 22 / Ubuntu 24.04:

```bash
sudo apt update
sudo apt install git python3 python3-venv ffmpeg libgl1 libglib2.0-0
```

Repository einmalig herunterladen:

```bash
git clone https://github.com/kAInplanmusic/lidarMONK.git
cd lidarMONK
```

Bei bereits vorhandenem Repository stattdessen im Ordner `lidarMONK` `git pull` ausführen. Anschließend starten:

```bash
bash scan-lab/start.sh --lan
```

Der erste Start richtet unter `~/.local/share/lidarmonk/venv` eine Python-Umgebung ein und installiert die Abhängigkeiten; das kann einige Minuten dauern. Danach startet der Server und zeigt einen oder mehrere vollständige Links mit Zugangsschlüssel. Öffne auf dem iPhone den Link mit der IP-Adresse des heimischen WLANs. Das iPhone muss im selben Netz sein; bei mehreren Adressen sind Docker-/VPN-Adressen oft nicht die richtige Wahl. Der Schlüssel ändert sich bei jedem Neustart. Zum Beenden im Terminal `Strg+C` drücken.

**Nur im vertrauenswürdigen Heimnetz verwenden:** Der LAN-Modus überträgt Daten und Zugangsschlüssel unverschlüsselt über HTTP. Keine Router-Portfreigabe oder öffentliche Bereitstellung einrichten und den Link nicht veröffentlichen. Für Zugriffe nur auf dem Linux-Rechner `bash scan-lab/start.sh` ohne `--lan` verwenden.

Uploads und Ergebnisse liegen unter `~/.local/share/lidarmonk/data`, nicht im Git-Repository. Ist `XDG_DATA_HOME` gesetzt, wird stattdessen dessen Unterordner `lidarmonk/data` verwendet. Die Verarbeitung und Speicherung erfolgen lokal auf dem Rechner. Der Ordner wird nicht automatisch geleert; bei Bedarf Dateien selbst sichern oder löschen. Aufträge sind nach Serverneustart nicht mehr in der Weboberfläche verzeichnet, die Dateien bleiben auf dem Rechner.

## Erste Aufnahme

1. Ein kleines, unbewegtes Objekt aus zwei Durchgängen mit vielen gemeinsamen Ansichten aufnehmen. In Stray Scanner den vollständigen Aufnahmeordner als ZIP exportieren; WurldCam als `.webm` oder `.mkv`. Optional ein SplatCapture-Trainingsdaten-ZIP mit `points.ply`, `images/` und `sparse/0/`.
2. Den Server wie oben starten und den angezeigten WLAN-Link auf dem iPhone öffnen.
3. Zwei unterschiedliche Dateien auswählen und hochladen, bei Bedarf eine dritte. Stray-/SplatCapture-ZIPs müssen jeweils genau einen vollständigen Export enthalten.
4. Objekt wählen und die Verarbeitung starten. Die regionale TSDF-Fusion ist experimentell und kann bei ungeeigneter Auflösung/Kalibrierung scheitern. Bei Personen für den ersten Test möglichst stillhalten; die optionale Bewegungskorrektur ist starr und experimentell.
5. Die Ergebnisdateien herunterladen. PLY-Dateien können etwa in MeshLab oder der [GitHub-Pages-Testseite](https://kainplanmusic.github.io/lidarMONK/) als Punktwolke betrachtet werden; ein Bericht erläutert die Tiefenwerte.

**Gültigkeitsgrenzen:** Keine echte iPhone-Aufnahme oder iPhone-Safari-Übertragung wurde im bisherigen Entwicklungstest verifiziert. Eine zuverlässige geometrische Genauigkeit ist nicht zugesichert. SplatCapture liefert dem Backend derzeit nur die exportierte Punktwolke; Bildtextur und Confidence werden nicht fusioniert. Die dritte Aufnahme ergänzt die gemeinsame Punktwolke, aber nicht das TSDF-Mesh. Große Exporte können auch mit 32 GB RAM zu groß sein; mit kurzen Aufnahmen beginnen. `report.json` beschreibt gültige Tiefenpixel, nicht die tatsächliche Qualität des Gesamtmodells.

## Falls etwas nicht klappt

- `bash scan-lab/start.sh --check` richtet die Umgebung ein und prüft die Python-Imports, ohne den Server zu starten.
- `Adresse bereits belegt`: `bash scan-lab/start.sh --lan --port 8766` verwenden.
- Das iPhone erreicht die Seite nicht: gleiches WLAN, WLAN-IP und lokale Firewall prüfen. Ein Gastnetz kann Geräte voneinander trennen. Keine öffentliche Portfreigabe aktivieren.
- Beim Paketinstallieren werden Internet und ausreichend freier Speicher benötigt; Fehlermeldung vollständig beachten.
- Weitere Hinweise: [Backend-Dokumentation](scan-lab/backend/README.md). Die [statische Testseite](https://kainplanmusic.github.io/lidarMONK/) läuft eigenständig, führt aber dieses Python-Backend nicht aus.
