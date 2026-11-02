# lidarMONK Scan Lab

Ein lokales Testlabor zum Prüfen von Fotos und Videos und zum Visualisieren importierter Tiefenkarten als 3D-Punktwolke. Alle Daten bleiben im Browser beziehungsweise auf dem Gerät; es gibt kein Backend und keine Telemetrie.

## Starten

`index.html` über einen statischen Webserver öffnen, z. B. im Projektverzeichnis:

```sh
python3 -m http.server 8000
```

Dann `http://localhost:8000` öffnen. Für den Zugriff vom iPhone muss das Gerät den Rechner im Netzwerk erreichen. Für eine echte öffentliche Internetadresse oder HTTPS ist ein separat konfiguriertes Hosting erforderlich; GitHub-Repository bedeutet nicht automatisch, dass GitHub Pages aktiviert ist.

Zum Kennenlernen kann `tests/demo-depth.json` geladen werden. Diese Datei enthält ausdrücklich künstliche Werte und keine echte Aufnahme.

## Ablauf

1. HEIC, JPEG, PNG, MOV, MP4 oder JSON auswählen. Bei Bild- und Videodateien sucht das Tool nur nach einigen Textmarkern im Anfang der Datei; ein Treffer ist kein Beleg für tatsächliche Tiefendaten und ein fehlender Treffer kein Ausschluss. Ein Video wird nicht vollständig auf Zusatzspuren analysiert.
2. Das separate iOS-Hilfsprogramm in `native/LidarMonkApp.swift` prüft ein ausgewähltes Foto mit ImageIO und AVFoundation auf eingebettete Tiefen-/Disparitätsdaten und exportiert sie, sofern auslesbar, in das JSON-Testformat. Es unterstützt keine Videos und kann fehlende Tiefendaten nicht rekonstruieren.
3. Das JSON ins Scan Lab laden. Für die Prozentzahl werden alle Tiefenpixel als Nenner verwendet. Zähler: positive endliche Tiefenwerte innerhalb des gewählten Abstandes, standardmäßig 5 m. Nullwerte und ungültige Werte zählen nicht als verwendbar. Das ist weder ein Genauigkeits- noch ein Qualitätsmaß und keine Aussage darüber, wie viel des Raums erfasst wurde.
4. Eine oder mehrere Punktwolken erscheinen in der Ansicht. Weitere Aufnahmen mit X/Y/Z und Drehung manuell ausrichten. Der PLY-Export enthält die aktuell innerhalb der gewählten Entfernung dargestellten Punkte.

## iPhone-Exporter in Xcode

1. Auf einem Mac mit Xcode ein neues iOS-App-Projekt (SwiftUI) erstellen, iOS 16 oder neuer auswählen.
2. Die automatisch erzeugten App- und ContentView-Dateien durch den Inhalt von `native/LidarMonkApp.swift` ersetzen; nur einen `@main`-Einstieg behalten.
3. Auf einem iPhone ausführen. Den System-Fotopicker öffnen, ein geeignetes Original auswählen, auf eine erfolgreiche Prüfung warten und das JSON über „In Dateien sichern“ teilen.
4. Im Browser die gesicherte JSON-Datei auswählen. Auch Porträt-Tiefen aus anderen Sensorquellen können vorhanden sein: Die App identifiziert die konkrete Sensorquelle nicht.

Dieser Quelltext wurde in dieser Umgebung nicht mit Xcode oder auf einem echten iPhone gebaut bzw. getestet. Fotoauswahl und verfügbare Zusatzdaten können je nach iOS-Version, Original, iCloud und Dateiformat abweichen. Der Picker fordert eine möglichst unveränderte aktuelle Repräsentation an; dies garantiert nicht, dass jedes Foto seine Zusatzdaten behält.

## Technische Grenzen

- Eine normale Webseite erhält auf dem iPhone keinen hier genutzten direkten ARKit-LiDAR-Zugriff. Die Hilfsapp liest nur Tiefendaten, die in der gewählten Bilddatei bereits als Apple-kompatible Zusatzdaten vorhanden sind. Standardfotos enthalten nicht zwangsläufig eine Tiefenkarte; Live-LiDAR-Streams müssen separat nativ erfasst werden.
- Der Dateiexporter verwendet, wenn möglich, die AVFoundation-Konvertierung zu `DepthFloat32` und behandelt positive endliche Werte als Meter. Nur vom System als absolut eingestufte Tiefendaten werden akzeptiert; andere werden abgelehnt. Bei Disparität ist deren Genauigkeit und Konvertierbarkeit abhängig von den verfügbaren Kalibrierungsinformationen. Bei ungeeigneten Daten bricht er ab. Sensorherkunft und Messgenauigkeit bleiben unbekannt.
- Ein pauschal angenommener horizontaler Bildwinkel von 60° ersetzt tatsächliche Kamerakalibrierung. Bild- und Tiefenorientierung sowie Farbzuordnung können abweichen. Das Modell ist experimentell und nicht für Vermessung, CAD oder Fertigung geeignet.
- Die App berechnet keine automatische gemeinsame Kamerapose, Fotogrammetrie, geschlossene Oberfläche oder Mesh. Mehrere Bildaufnahmen müssen manuell positioniert werden; der Export ist eine unkalibrierte Punktwolke im ASCII-PLY-Format.
- Der Browser begrenzt einzelne Dateien auf 200 MB und Tiefenkarten auf 2 Millionen Pixel; die Ansicht tastet für interaktive Darstellung aus. Ein positiver Tiefenwert ist kein Nachweis für korrekte Entfernung oder dass dieser vom LiDAR stammt.
- Picker-Ergebnisse, Dateinamen, Videos und Farbbilder können sensible Informationen enthalten; es gibt keine Übertragung an Dritte durch die App.

## Nächste Ausbaustufe

Native ARKit-Aufnahme mit synchronisierten `sceneDepth`, RGB, Kameraintrinsik und Kamera-zu-Welt-Transformation je Frame. Erst diese Posen und Kalibrierung ermöglichen eine sinnvolle automatische Registrierung mehrerer Ansichten. Dazu Geräteprüfung, Fehleranzeige und Tests auf echter Hardware ergänzen.
