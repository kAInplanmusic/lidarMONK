# lidarMONK unter Linux Mint

Das Linux-Werkzeug prüft **echte lokale Dateien**, ohne Apple-Entwicklerkonto oder eigene iPhone-App. Es erkennt mit `pillow-heif` die vom verwendeten libheif-Decoder unterstützten HEIF-Tiefenzusatzbilder und listet deren Größe und Bildmodus. Optional speichert es auslesbare Tiefenbilder als PNG. Für MOV/MP4 zeigt `ffprobe` eine Liste der erkannten Spuren.

**Wichtig:** Ein Tiefenzusatzbild ist nicht automatisch ein metrischer LiDAR-Scan. Seine Werte können Disparität oder anders kodierte relative Tiefe sein. Diese Version kennt weder die sichere Umrechnung in Meter noch die Sensorherkunft und errechnet daher keine 5-m-Prozentzahl. Ein negativer Decoderbefund schließt nicht jedes unbekannte Zusatzdatenformat aus. PNGs sind Analyse-Kopien; Originale werden nicht verändert.

## Installation (Linux Mint / Ubuntu)

```bash
sudo apt update
sudo apt install python3 python3-venv python3-tk ffmpeg libimage-exiftool-perl
cd scan-lab/linux
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python ScanLab.py
```

Installation benötigt Internetzugang und eventuell passende Systempakete für libheif. `ffmpeg` ist nur für Video-Spurinformationen erforderlich. ExifTool liefert zusätzliche Metadaten und ist optional; ein Metadatenhinweis allein ist kein Nachweis für eine nutzbare Tiefenkarte. Auf anderen Linux-Distributionen heißen Pakete möglicherweise anders. Die GUI benötigt eine Desktop-Sitzung.

## Dateien vom iPhone

1. Fotos auf dem iPhone auswählen und über Teilen → **Unbearbeitetes Original exportieren** auf USB-Speicher oder an einen geeigneten Ort in „Dateien“ sichern. Eine reine HEIC-Endung beweist keine Tiefenkarte.
2. Originaldateien ohne Konvertierung auf den Linux-Rechner kopieren und im Scan Lab auswählen. USB-Verbindung zum Rechner oder eine Dateifreigabe sind mögliche Alternativen; die tatsächliche Originaltreue muss pro Übertragungsweg geprüft werden.
3. Bei HEIC/HEIF den optionalen Exportordner auswählen. Der Bericht zeigt erkannte Depth-Bilder und weitere Auxiliary-Typen. Ein HDR-Gainmap- oder Masken-Bild ist kein Tiefennachweis.
4. Bei Video erscheinen die durch ffprobe erkennbaren Spuren. Eine eindeutige Identifikation und Dekodierung von LiDAR-Streams aus Videos ist noch nicht implementiert.

Eine sofort verwendbare Alternative für echte 3D-Scans ist eine iPhone-Scanner-App aus dem App Store, z. B. Scaniverse, und danach der Export in ein unterstütztes 3D-Format. Das Ergebnis ist ein verarbeitetes Modell und kein nachweislich vollständiger Original-LiDAR-Rohdatenstrom. Funktionen und Exportoptionen in der jeweils aktuellen App-Version prüfen.

## Kommandozeile

```bash
.venv/bin/python inspect_media.py ~/Bilder/IMG_0001.HEIC ~/Videos/IMG_0002.MOV --export-depth ~/Bilder/lidarMONK-Ausgabe
```

Für Modellrekonstruktion aus vielen Standardfotos ist Fotogrammetrie mit COLMAP eine separate Option. Ohne CUDA ist in COLMAP eine dünne Rekonstruktion möglich, aber dessen dichte Standardrekonstruktion benötigt CUDA; Rechenzeit und RAM hängen stark von Bildgröße und -menge ab. Die HEIF-Prüfung oben erzeugt noch kein automatisch registriertes 3D-Modell.

## Projektstatus

Quellcode und Kommandozeile wurden mit synthetischen Daten und Abhängigkeitsfehlern geprüft; ein echter iPhone-HEIC mit eingebetteter Tiefenkarte und eine Linux-Mint-GUI müssen noch praktisch getestet werden. Die vorhandene Browser-Ansicht kann nur das separat definierte metrische JSON importieren; die nichtmetrisierte PNG-Ausgabe dieses Werkzeugs ist dafür bewusst nicht zugelassen.

## Aufnahmeformate und Prüftiefe

| Format / Beispiele | Prüfung in dieser Version |
|---|---|
| HEIC, HEIF, AVIF | Metadaten; unterstützte HEIF-Tiefenzusatzbilder und Auxiliary-Typen über pillow-heif/libheif |
| JPEG/JPG, PNG, TIFF, WebP, GIF, BMP, JPEG XL | Metadaten mit ExifTool, soweit unterstützt; keine Tiefenkarten-Dekodierung |
| DNG/Apple ProRAW, RAW, CR2/CR3, NEF/NRW, ARW, RAF, RW2, ORF | Metadaten mit ExifTool, soweit unterstützt; keine Tiefenkarten-Dekodierung |
| MOV, MP4, M4V, 3GP, AVI, MKV, WebM, MTS/M2TS, ProRes-Dateien | Metadaten und verfügbare Spuren via ffprobe; keine spezielle Tiefenspur-Dekodierung |
| Andere Dateitypen | Versuch der Metadatenprüfung; Inhalt und Tiefe nicht garantiert auswertbar |

Ein Format wie HEIC oder MOV ist ein Container; HEVC/H.265, H.264, ProRes, HDR/Dolby Vision und Log beschreiben Codec oder Aufnahme-/Farbverfahren. Foto, Live Photo, Porträt, RAW/ProRAW und räumliche Videos sind Aufnahmearten und garantieren weder dieselben Zusatzdaten noch einen verwendbaren LiDAR-Strom. Ein Live Photo kann aus separatem Foto und Video bestehen; beide Originale behalten. Zeitlupen, Zeitraffer und filmische Videoeffekte benötigen eine eigene fachliche Auswertung. ffprobe kann eine unterstützte Datei öffnen, auch wenn ihre Endung ungewöhnlich ist, aber dieses Programm wählt den Video-Prüfpfad derzeit anhand der oben genannten Endungen.

Beim Übertragen Originalformat und Originaldateien erhalten. ExifTool und ffprobe können je nach Version und Datenaufbau Informationen übersehen; ein Hinweis auf „depth“ ist nicht automatisch eine auslesbare Karte, ein HDR-Gainmap ist keine Tiefenkarte, und die Sensorquelle bleibt ungeklärt.
