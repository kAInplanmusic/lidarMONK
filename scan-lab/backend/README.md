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
- Kein echtes Multi-View-Fotogrammetrie-, Gaussian-Splatting- oder TSDF-Backend. Die drei Vergleichsstrategien sind Punktwolkenvarianten, kein Ersatz für einen systematischen Vergleich unterschiedlicher Rekonstruktionsalgorithmen.
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

## Untersuchter TSDF-Weg – noch nicht freigegeben

Die volumetrische TSDF-Integration mit Open3D 0.20.0 wurde an einer künstlichen Ebene mit bekanntem Abstand und am synthetischen Wurld-Beispiel ausprobiert. In der aktuellen Testumgebung wurde trotz gültiger Eingabewerte keine Oberfläche erzeugt. Die Ursache ist bisher ungeklärt. Deshalb wurde diese Funktion nicht in den ausführbaren Backend-Weg aufgenommen; eine erfolgreiche Rekonstruktion wäre derzeit nicht seriös zugesichert. Für den weiteren Ausbau sind reproduzierbare Minimaltests, Ursachenanalyse, geometrische Ground-Truth-Messungen und reale iPhone-Datensätze nötig.
