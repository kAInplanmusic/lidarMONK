# lidarMONK RGB-D-Fusionsbackend (experimentell)

Kommandozeilen-Prototyp: zwei Wurld-Aufnahmen und/oder entpackte Stray-Scanner-Aufnahmen einlesen, Tiefenwerte mit Kameraposen projizieren, beide Scans ausrichten und drei Punktwolken-Strategien gegenüberstellen. Läuft lokal unter Linux; keine iPhone-Entwicklerinstallation, kein Server und kein automatischer Upload erforderlich.

## Installieren

```bash
sudo apt install python3 python3-venv ffmpeg libgl1 libgomp1
cd lidarMONK/scan-lab/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Open3D ist groß und benötigt eine passende x86_64-Linux/Python-Wheel-Version. Testumgebung: Python 3.12, Open3D 0.20.0, wurld 1.4.0. Falls `python3 -m venv` fehlt, passendes `python3-venv` nachinstallieren. Unter Ubuntu/Mint 24.04 sollte Python 3.12 verfügbar sein. Für `wurld`-Aufnahmen und insbesondere die Stray-Konvertierung ist ffmpeg erforderlich.

## Verwenden

Originale exportieren, unverändert auf Linux kopieren. Beide Aufnahmen müssen dasselbe unbewegte Objekt und ausreichend gemeinsame Flächen zeigen. Bei Stray wird ein **entpackter** Aufnahmeordner mit `camera_matrix.csv`, `odometry.csv`, `rgb.mp4` und `depth/` erwartet; ZIP muss vorher in einen eigenen Ordner entpackt werden. WurldCam: `.wurld.webm`.

```bash
.venv/bin/python lidarmonk_backend.py /pfad/stray-aufnahme /pfad/aufnahme.wurld.webm --output /pfad/ausgabe
```

Der Ausgabeordner muss neu oder leer sein. `report.json` zeigt pro Frame die Gesamtzahl der Tiefenpixel und positive endliche Werte innerhalb der voreingestellten 5 m. Diese Quote ist keine Genauigkeitsbewertung und misst keine Objektabdeckung. Die automatische Registrierung benutzt FPFH/RANSAC für eine grobe Ausrichtung und ICP zur Verfeinerung. Eine schwache Übereinstimmung wird abgelehnt; auch ein akzeptierter Wert kann bei Symmetrien falsch sein und muss visuell geprüft werden. Mit `--transform matrix.json` kann alternativ eine geprüfte starre 4×4-Transformation B→A vorgegeben werden. Beispiel für die Identität (nur bei bereits gleichem Koordinatensystem verwenden):

```json
[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
```

`--max-depth 5 --voxel 0.02 --stride 10 --max-frames 30 --pixel-step 4` sind veränderbar. Die Standardeinstellungen begrenzen den Speicherbedarf, sind aber noch keine für jedes Gerät optimierte Lösung. Der Wurld-Leser und der Stray-Konverter können ganze Sequenzen in den Speicher laden; große Aufnahmen können auf einem Rechner mit 24 GB RAM sehr langsam sein oder nicht hineinpassen. Kurze Aufnahmen und begrenzte Dateigrößen für erste Tests verwenden.

Ausgaben:

- `scan-a.ply`, `scan-b-local.ply`: einzelne Scans vor Ausrichtung, B in eigenem lokalen Koordinatensystem.
- `separate.ply`: je Aufnahme Punkte sammeln und reduzieren, dann B ausrichten und beide reduzieren.
- `joint.ply`: Punkte beider Aufnahmen zuerst in ein Koordinatensystem bringen, dann gemeinsam reduzieren.
- `incremental.ply`: Frames A/B abwechselnd einfügen und nach jedem Schritt reduzieren. Dies ist eine **inkrementelle Punktwolkenreduktion**, keine Pose-Graph-Optimierung oder TSDF-Fusion.
- `report.json`: Prozentwerte, Parameter, Transformation, Laufzeiten und Anzahl der Punkte. Laufzeit/Punktzahl allein sind keine Qualitätsmetrik.
- Optional `--mesh`: experimentelles Poisson-Mesh aus der zuletzt berechneten Punktwolke. Dies kann Löcher füllen und Oberflächen erfinden; Qualität und Dimensionen sind nicht garantiert.

## Was noch nicht funktioniert

- RGB-Farben und Confidence-Maskierung werden in der aktuellen Version nicht in die Punktwolken übernommen, obwohl sie in den Quelldaten vorhanden sein können.
- Kein Webserver/GUI oder Handy-Direktübertragung; Upload ist manuelles Dateikopieren.
- Kein echtes Multi-View-Fotogrammetrie- oder Gaussian-Splatting-Backend. Die drei ursprünglichen Vergleichsstrategien sind Punktwolkenvarianten; die zusätzliche CPU-TSDF-Variante ist experimentell.
- Nur unterstützte Wurld-Kameramodelle `PINHOLE` und `SIMPLE_PINHOLE` mit Kameraintrinsik auf Tiefenbildauflösung. Andere Modelle oder abweichende Auflösungen werden abgelehnt, anstatt ungeprüft kalibriert zu werden.
- `wurld` verarbeitet Stray über seinen Konverter. Laut upstream ist die reale Gerätevalidierung der Konventionen noch offen. Es gibt Hinweise auf verschiedene Odometry-Versionen; keine universelle Unterstützung behaupten.
- Keine Qualitätsverbesserung oder korrekte automatische Registrierung garantiert; Position, Achsen, Tiefenskala, Schärfe und metrische Maße mit realen Aufnahmen und Referenzmaßen prüfen.
- Bei unterbrochenem Lauf kann der Ausgabeordner teilweise gefüllt sein; neuen Ordner wählen. Große Dateien nicht automatisch ins Git-Repository übertragen.

## Reproduzierbarer Vergleich und Grenzen

Erzeugt wurde ein synthetischer Wurld-Datensatz aus dem Wurld-Demo und eine künstliche Stray-Struktur aus drei Tiefen-PNGs, CSVs und einem Testvideo. End-to-End wurden Wurld/Wurld und Stray/Stray getestet, zusätzlich Wurld/Wurld mit automatischer Registrierung. Beispiel Wurld/Wurld: 3 Frames pro Eingabe, stride 20, Pixelabstand 8, 2-cm-Voxel, identische Eingaben und Einheitsmatrix: separate 4758, joint 4758, incremental 4748 Punkte. Dies sind **keine gemessenen Qualitätswerte** und keine Überlegenheit eines Verfahrens. Reale iPhone-Aufnahmen, unabhängige Scans und eine verlässliche 3D-Ground-Truth lagen nicht vor.

## Weitere Wege / Forschung

- Open3D RGB-D TSDF, Pose-Graph und robuste Multiway-Registrierung: https://www.open3d.org/docs/latest/tutorial/pipelines/rgbd_integration.html und https://www.open3d.org/docs/latest/tutorial/pipelines/multiway_registration.html
- Wurld-Format und Stray-Konverter: https://github.com/kmatzen/wurld ; Stray-Format: https://github.com/strayrobots/scanner/blob/main/docs/format.md
- Weitere Datenpunkte durch zusätzliche Ansichten und Fotogrammetrie (COLMAP): https://colmap.github.io/ ; höhere visuelle Detailfülle ist nicht automatisch höhere metrische Genauigkeit.
- Gaussian Splatting/Nerfstudio: https://github.com/nerfstudio-project/nerfstudio ; vor allem für realistische Darstellung, nicht automatisch CAD-Mesh. Rechenbedarf und GPU-Kompatibilität beachten.
- iPhone TestFlight: Splatify-Anything/SplatCapture Studio exportiert laut Projekt zusätzlich ein COLMAP-Dataset und kann 3DGS lokal trainieren. Aktuelle Projektversion ist nicht kommerziell lizenziert: https://github.com/KuoFengYuan/splatify-anything
- Stray-RGBD-Referenzpipeline: https://github.com/MichaelFowler1/lidar-scan-pipeline ; aktuelle Version ist nicht kommerziell lizenziert. Kein Code daraus wurde übernommen.

Mit der Anzahl generierter Punkte steigt die echte Sensorinformation nicht automatisch. Interpolierte oder KI-geschätzte Geometrie ist von gemessenen Daten zu unterscheiden.

## Update: Ausrichtungsprüfung und Bildgrößen

Die automatische Registrierung überprüft nun den Überlappungswert in beiden Richtungen. Dies kann manche asymmetrische Fehlanpassung erkennen, aber auch ein hoher Wert belegt keine korrekte Zuordnung bei symmetrischen Objekten.

Bei unterschiedlichen RGB-/Tiefenauflösungen bricht die Software standardmäßig weiterhin ab. Nur wenn anhand der jeweiligen Aufnahme und Kalibrierung nachgewiesen wurde, dass beide Bilder denselben Ausschnitt und dieselbe optische Projektion verwenden, kann `--aligned-depth` die Kameraintrinsik auf die Tiefenauflösung skalieren. Unterschiedliche Bildausschnitte, Verzeichnung oder getrennte optische Zentren werden dadurch nicht korrigiert. WurldCam-Aufnahmen mit unterschiedlichen Stream-Größen sind damit nicht pauschal automatisch validiert.

Für jeden verarbeiteten Frame enthält der Bericht zusätzlich Prozentwerte für Distanzen bis 1, 2, 3, 4 und 5 Meter; Nenner sind sämtliche Tiefenpixel des jeweiligen Frames. Ein positiver numerischer Messwert ist nicht zwingend zuverlässig.

## Untersuchter Open3D-TSDF-Weg – nicht freigegeben

Die volumetrische TSDF-Integration mit Open3D 0.20.0 wurde an einer künstlichen Ebene mit bekanntem Abstand und am synthetischen Wurld-Beispiel ausprobiert. In der aktuellen Testumgebung wurde trotz gültiger Eingabewerte keine Oberfläche erzeugt. Die Ursache ist bisher ungeklärt. Deshalb wurde diese Funktion nicht in den ausführbaren Backend-Weg aufgenommen; eine erfolgreiche Rekonstruktion wäre derzeit nicht seriös zugesichert. Für den weiteren Ausbau sind reproduzierbare Minimaltests, Ursachenanalyse, geometrische Ground-Truth-Messungen und reale iPhone-Datensätze nötig.

## Experimentelle regionale CPU-TSDF-Fusion

Optional `--regional-tsdf` hinzufügen, beispielsweise:

```bash
.venv/bin/python lidarmonk_backend.py /pfad/stray /pfad/aufnahme.wurld.webm --output /pfad/ausgabe --voxel 0.08 --regional-tsdf
```

Die Implementierung nutzt eine eigene projektive TSDF-Integration mit NumPy und Marching Cubes aus scikit-image; Open3Ds fehlschlagende TSDF-Volumenfunktion wird nicht verwendet. Beide Aufnahmen werden nach der Registrierung separat auf demselben Raster integriert. Ein Router untersucht Blöcke von 4³ Voxeln: Bereiche, die nur ein Scan sieht, stammen von diesem Scan; bei übereinstimmenden gemeinsamen Messungen werden die TSDF-Werte anhand der Beobachtungszahl gemittelt; bei deutlichem Widerspruch wird das Voxel ausgeschlossen. Die im Bericht und der NPZ-Karte ausgewiesene bevorzugte Quelle basiert auf der regionalen Beobachtungszahl. Sie ist **keine tatsächliche Messgenauigkeit oder Sensor-Confidence** und verursacht derzeit keine automatische Auswahl eines feinen Detail-Meshes.

- Ergebnis: `regional-tsdf-mesh.ply` und `regional-tsdf-map.npz` (Rasterursprung, Voxelgröße, Unterstützung, Quelle und Konflikte). Für die Kartenwerte bedeutet 0: keine Daten, 1: bevorzugt A, 2: bevorzugt B, 3: Konflikt. Bei konsistenten Messungen beider Quellen wird gemittelt, auch wenn 1 oder 2 die regionale Präferenz kennzeichnet.
- Es werden nur Flächen behalten, deren Nachbarvoxel Messungen besitzen. Das reduziert künstliche Abschlüsse an unbekannten Bereichen, kann aber Löcher vergrößern.
- Das dichte CPU-Raster ist auf drei Millionen Voxel begrenzt. Voxelzahl wächst ungefähr kubisch mit der Auflösung; größere `--voxel`-Werte verwenden, um das Limit einzuhalten. RGB, Confidence, View-Angle- und Oberflächenrauschen sowie globale Pose-Graph-Optimierung sind noch nicht integriert. Es gibt keine automatische Objektfreistellung.
- `--regional-tsdf` wurde mit einer synthetischen RGB-D-Ebene bekannter Tiefe und synthetischem Wurld-Demomaterial getestet, nicht mit echten iPhone-Daten. Die ursprüngliche Open3D-TSDF-Ursache bleibt offen; ein vergleichbarer Fehlerbericht existiert unter https://github.com/isl-org/Open3D/issues/7592 .
- Originalscans sind getrennte Koordinatensysteme. Eine falsche Registrierung bleibt selbst bei geringer Punktwolkenabweichung möglich; bei gleichem Objekt real mit Referenzmaßen prüfen.

## Upload-Oberfläche für erste Aufnahmen

Auf Linux mit installierten Abhängigkeiten im `scan-lab/backend`-Ordner starten:

```bash
.venv/bin/python server.py
```

Den ausgegebenen vollständigen Link am Linux-Rechner öffnen. Für das iPhone im **vertrauenswürdigen selben WLAN**:

```bash
.venv/bin/python server.py --lan
```

Der Start gibt den Zugangslink mit Platzhalter `<LINUX-IP>` aus. Die passende lokale IP des Linux-Rechners kann mit `hostname -I` ermittelt werden. Den vollständigen Link einschließlich Schlüssel auf dem iPhone in Safari eingeben. `--lan` ist ausdrücklich optional: Die Verbindung ist HTTP und nicht verschlüsselt; nicht in öffentlichen/fremden Netzen oder per Portfreigabe verwenden. Der Zugangsschlüssel wird bei jedem Neustart neu erzeugt und darf nicht weitergegeben werden. HTTPS, Benutzerkonten und eine verschlüsselte Übertragung sind noch nicht implementiert.

1. In Stray Scanner den vollständigen Aufnahmeordner über Dateien als ZIP komprimieren; alternativ WurldCam-Datei in Dateien sichern. Originale bleiben auf dem iPhone.
2. Im Browser zwei ZIP-/Wurld-WebM-Dateien auswählen und hochladen (maximal 2 GiB je Datei; entpackte ZIP maximal 4 GiB und 20.000 Dateien). Entpackte Stray-/SplatCapture-ZIPs müssen genau einen vollständigen Aufnahmeordner enthalten. ZIPs mit Dateipfaden außerhalb des Zielordners oder Symlinks werden abgelehnt.
3. Zwei unterschiedliche Aufnahmen und optional eine dritte Aufnahme auswählen und Objekt oder Person angeben. Die regionale TSDF-Option ist zunächst aktiviert; falls sie wegen Konflikten, Speicherlimit oder fehlender Daten fehlschlägt, kann sie deaktiviert und ein neuer Auftrag gestartet werden.
4. Bei Erfolg stehen PLY-Dateien und der JSON-Bericht zum Download bereit. Aufträge laufen auf dem Linux-Rechner; Smartphone und Linux müssen während der Übertragung erreichbar sein. Ein Unterbrechen des Servers beendet laufende Aufträge. Die Dateien bleiben im lokalen Datenordner `lidarmonk-data`; löschen ist derzeit nur manuell über den Dateimanager möglich. Nach Neustart sind alte Auftragsdownloads nicht automatisch aufgelistet.

**Personenmodus:** führt eine experimentelle starre Frame-zu-Referenz-ICP-Korrektur innerhalb jeder Aufnahme aus. Frames mit geringer Überlappung oder zu großer Verschiebung/Drehung werden verworfen. Es gibt noch keine Personensegmentierung oder nichtstarre Korrektur; Hintergrundbewegung, Atmung und Gelenke sind ungelöst. Das Backend erwartet zwei starre Aufnahmen; eine einzelne Aufnahme kann in dieser Oberfläche noch nicht allein verarbeitet werden. Zustimmung der abgebildeten Person einholen und Daten angemessen schützen.

**Praxistest:** End-to-End wurden zwei synthetische Wurld-Dateien über HTTP hochgeladen und verarbeitet; unautorisierter Zugriff und ein ZIP mit Pfadmanipulation wurden abgewiesen. Ein echtes iPhone, eine echte Stray-ZIP und der Safari-Upload wurden hier noch nicht getestet. Die Weboberfläche enthält noch keine 3D-Vorschau, Objektfreistellung oder automatische Motion-Korrektur. Die Farbdaten und Confidence-Masken werden bei der Geometriefusion weiterhin nicht berücksichtigt.

## Experimentelle Bewegungskorrektur und dritte App

Der Personenmodus der Upload-Oberfläche aktiviert `--motion-correction`; auf der Kommandozeile kann der Schalter unabhängig vom Motiv gesetzt werden. Die Korrektur gleicht jeden Frame einer Aufnahme mittels Punkt-zu-Punkt-ICP an deren ersten akzeptierten Referenzframe an. Sie lässt standardmäßig höchstens 10 cm Translation und 12° Rotation zu und verwirft Frames bei zu geringer Überlappung oder Überschreitung dieser Grenzen. Berichte enthalten je Frame Status und Transformationsmetriken. Die Transformation wird bei RGB-D-Tiefenframes auch auf deren Kamerapose für TSDF übertragen.

**Grenzen:** Der Algorithmus ist keine Segmentierung, keine Körper- oder Gesichtsverfolgung und keine nichtstarre Bewegungskorrektur. Hintergrund kann dominieren, Selbstverdeckungen und große Aufnahmewinkel können Frames ablehnen, und starre Korrekturen können an einzelnen Körperteilen falsch sein. Verwerfungen und Ergebnisse müssen visuell geprüft werden. Es existiert kein direkter Bewegungskorrektur-Nachweis an echten Personenaufnahmen.

SplatCapture Studio (TestFlight; https://github.com/KuoFengYuan/splatify-anything) exportiert laut https://github.com/KuoFengYuan/splatify-anything/blob/main/docs/HISTORY_TRAINING_EXPORT.md eine COLMAP-Trainings-ZIP mit `images/`, `sparse/0/` und `points.ply`. Der Upload akzeptiert diese Ordnerstruktur als ZIP; das Backend verwendet derzeit **nur `points.ply` im ARKit-Weltkoordinatensystem**. Bilder, Posen, rohe Tiefen und Confidence dieser App werden noch nicht verarbeitet. COLMAP-Koordinaten und ARKit-Punktwolke dürfen nicht ohne Transformation vermischt werden.

Die optionale dritte Aufnahme wird global auf Scan A registriert und als `third-registered.ply` sowie gemeinsam mit A/B als `combined-three.ply` ausgegeben. Das regionale TSDF-Mesh verarbeitet weiterhin nur die RGB-D-Frames von A und B; die dritte Punktwolke ergänzt dieses Mesh nicht. Wird SplatCapture als A oder B verwendet, wird die regionale TSDF-Fusion übersprungen, weil für diese Quelle nur eine Punktwolke geladen wird. Empty-Cloud-Exporte werden abgewiesen. Beispiel:

```bash
.venv/bin/python lidarmonk_backend.py /pfad/stray /pfad/wurld.webm --capture-c /pfad/splat-entpackt --motion-correction --output /pfad/ausgabe
```

Für SplatCapture wurden nur künstliche Ordner-/Punktwolkenbeispiele getestet, keine App-Exportdatei. Nichtkommerzielle Drittanbieter-Lizenzen und Nutzungsbedingungen sind vor Übernahme von Drittcode zu beachten; die Integration hier verwendet die dokumentierten Dateiformate und kopiert keinen SplatCapture-Quellcode.
