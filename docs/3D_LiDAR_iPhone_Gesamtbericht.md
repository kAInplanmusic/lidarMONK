# 3D-Erfassung mit dem iPhone 18 Pro
## Gesamtbericht zu LiDAR, Fotogrammetrie, Hardware, Web-App und Entwicklungsstrategie

Stand: 2. November 2026

### Grundlage und Einordnung

Dieser Bericht führt die drei Projektdateien „IPhone 18 Pro - lidar-foto.txt“, „LIDAR.txt“ und „Hardware-Architektur, Sensor-Integration und räumliche Datenerfassung des iPhone.txt“ mit dem im vorliegenden Verlauf sichtbaren Projektkontext zusammen. Der vollständige Inhalt anderer Chats lag bei der Erstellung nicht vor; deren Details werden nicht erfunden. Die drei Dokumente sind Ausgangsmaterial und keine durchgehend unabhängig bestätigten Primärquellen. Ergänzend wurden ausgewählte Hersteller- und Entwicklerdokumentationen geprüft. Aussagen werden als bestätigt, technisch plausibel oder offen gekennzeichnet. Nicht jede in den Ursprungsdokumenten genannte Produktfunktion und Zahl wurde einzeln verifiziert.

## 1. Das Projekt in einem Satz

Ziel ist eine Anwendung für das iPhone 18 Pro, die reale Objekte und/oder Räume dreidimensional erfasst und deren Ergebnisse möglichst einfach im Web sichtbar, bearbeitbar und exportierbar macht. Welche Objektgrößen, Genauigkeit, Exportformate und Betriebsbedingungen verbindlich sind, wurde im sichtbaren Material noch nicht abschließend festgelegt.

**Die wichtigste Architekturentscheidung:** Die Hardware besitzt laut Apple einen LiDAR-Scanner [1]. Daraus folgt aber nicht, dass eine normale Webseite in Safari dessen Tiefenstrom auslesen kann. Apples dokumentierter Zugriff erfolgt über native Frameworks wie ARKit und AVFoundation [2–5]. Eine Weboberfläche für Darstellung, Organisation und Bearbeitung lässt sich mit einer nativen iOS-Erfassung verbinden. Alternativ kann eine reine Web-App Fotos aufnehmen und fotogrammetrisch verarbeiten, ohne einen direkten LiDAR-Zugriff zu behaupten.

## 2. Die wichtigsten Ergebnisse

1. LiDAR, Kamerafotos und Bewegungssensoren ergänzen einander: Tiefenmessung liefert unmittelbare Abstandsinformation, Fotos liefern sichtbare Details und Textur, Tracking verknüpft Aufnahmen räumlich.
2. Eine Punktwolke, ein Dreiecksnetz und ein Gaussian Splat sind unterschiedliche Ergebnisse. Ein fotorealistischer Splat ist nicht automatisch ein maßhaltiges, editierbares CAD-Modell.
3. Für Räume sind ARKit-Umgebungsrekonstruktion und gegebenenfalls RoomPlan naheliegend; für detailreiche Einzelobjekte ist Fotogrammetrie besonders interessant. Beide müssen an konkreten Szenen getestet werden.
4. Eine hybride Architektur aus nativer Erfassung und Web-App verbindet Gerätesensorik und plattformübergreifende Nutzung. Ein Web-only-Ansatz ist leichter zugänglich, hat auf iOS aber andere Datenquellen und Fähigkeiten.
5. Die in den Quelldateien genannten Werte wie „5 mm“, „unter 1,5 cm“, „576 Punkte“ und konkrete Sony-Chipnummern sind ohne passenden unabhängigen Nachweis keine zugesicherte Spezifikation des iPhone 18 Pro. Gleiches gilt für versprochene Rechenzeiten, generelle Formatunterstützung und absolute Aussagen zur Dunkelheit.
6. Ein eigener Mess- und Kompatibilitätstest auf dem tatsächlichen Gerät ist wichtiger als die Übernahme von Präzisionsversprechen aus Marketing oder Einzelstudien.

## 3. Hardware und Sensoren

### 3.1 Sensorgruppen und Aufgaben

Das Gerät vereint rückseitige Kameras, einen rückseitigen LiDAR-Scanner, Bewegungssensorik und ein vorderseitiges TrueDepth-System. Apple nennt den LiDAR-Scanner in den technischen Daten [1]. Die Kameras zeichnen Helligkeit und Farbe auf; der LiDAR-Sensor liefert Tiefeninformation; Beschleunigungssensor und Gyroskop unterstützen zusammen mit Bildmerkmalen die räumliche Verfolgung der Gerätebewegung. Die Front-Tiefenkamera ist ein eigenständiger Aufnahmeweg für andere Blickrichtungen und Einsatzfälle; ihre Daten sind nicht einfach austauschbar mit dem rückseitigen LiDAR-Strom.

Die Quelldateien nennen konkrete Bildsensor-IDs, eine variable Blende, Prozessor-Fertigungsgröße, Neural-Engine-Aufbau und weitere Kameradetails. Diese Angaben sind für die grundsätzliche App-Architektur nicht notwendig und wurden hier nicht vollständig verifiziert. Die jeweils aktuelle Apple-Spezifikation und verfügbare Entwickler-APIs sind für Produktentscheidungen maßgeblich [1]. Interne Bauteilnummern sollten erst nach einer belastbaren technischen Quelle verwendet werden.

### 3.2 Wie Laufzeitmessung funktioniert

Bei einer direkten Laufzeitmessung wird Licht ausgesendet und die Laufzeit seines reflektierten Anteils ausgewertet. Vereinfacht gilt für die Strecke zwischen Sensor und Oberfläche:

**Entfernung d = Lichtgeschwindigkeit c × Laufzeit Δt / 2.**

Die Division durch zwei berücksichtigt Hin- und Rückweg. In einem realen Gerät bestimmen unter anderem Signalverarbeitung, Mehrwegeffekte, Material und Beleuchtung das Ergebnis. Apple beschreibt für die LiDAR-Kamera die Messung der Umlaufzeit eines künstlichen Lichtsignals [5]. Aussagen über das genaue interne Pixel- oder Strahlmuster und die verwendeten Bauteile benötigen gerätespezifische Belege.

### 3.3 Sichtfeld, Reichweite und Dunkelheit

Die Quellen nennen rund fünf Meter als Orientierung aus älteren Generationen bzw. allgemeinen Beschreibungen. Das ist keine hier verifizierte pauschale Leistungsgrenze oder Genauigkeitszusage für das iPhone 18 Pro. Ein großer Raum kann aus vielen Positionen erfasst werden, auch wenn die verlässliche Einzelmessdistanz begrenzt ist; dabei steigt die Bedeutung von Überlappung, Tracking und Driftkontrolle.

Aktives Infrarot kann Tiefenmessung unter bestimmten schwachen Lichtverhältnissen ermöglichen. Daraus folgt nicht, dass ein vollständiger Scan in völliger Dunkelheit robust ist: Kameratracking, Farbtexturen und Bildmerkmale benötigen gegebenenfalls sichtbares Licht. Starke Sonneneinstrahlung, Entfernung und Oberflächen beeinflussen die Qualität.

## 4. Grundbegriffe der 3D-Erfassung

### 4.1 Tiefenkarte

Eine Tiefenkarte ordnet Bildpositionen Entfernungswerte zu. Diese Werte können durch Sensorik und Software gemeinsam entstehen und müssen nicht identisch mit unverarbeiteten Laser-Rohmessungen sein. ARKit stellt auf unterstützten Geräten `sceneDepth` und `smoothedSceneDepth` bereit; zu den Tiefendaten gehört eine Einschätzung der Zuverlässigkeit [2, 3]. Smoothed Depth reduziert zeitliche Schwankungen, kann aber bei Bewegung und scharfen Kanten andere Artefakte zeigen. Beide Varianten sollten praktisch verglichen werden.

### 4.2 Punktwolke

Eine Punktwolke besteht aus 3D-Punkten, optional mit Farben oder anderen Attributen. Sie ist keine automatisch geschlossene Oberfläche. Aus einem Tiefenpixel kann mithilfe der Kameraintrinsik ein Punkt im Kamerakoordinatensystem berechnet und anschließend über die Kamerapose in ein gemeinsames Weltkoordinatensystem übertragen werden. Die korrekte Interpretation der Tiefe, Bildorientierung, Achsen, Auflösung und Kalibrierung muss zur jeweils verwendeten API passen.

### 4.3 Mesh und Textur

Ein Mesh verbindet Punkte durch Polygone, meistens Dreiecke. Es kann Oberflächen darstellen, ohne wasserdicht oder für Fertigung geeignet zu sein. Eine Textur projiziert Bildinformationen auf die Oberfläche. Unsichtbare oder verdeckte Bereiche bleiben unbekannt oder werden durch Algorithmen ergänzt. Automatisch gefüllte Löcher sind eine Schätzung und sollten entsprechend markiert werden.

### 4.4 Tracking und SLAM

SLAM steht für gleichzeitige Positionsbestimmung und Kartierung. Visual-Inertial Odometry kombiniert Bildmerkmale und Bewegungssensoren zur Schätzung der Gerätebewegung. Akkumulierte Fehler führen zu Drift: Ein Raum kann am Ende nicht exakt zum Anfang passen. Schlechte Texturen, schnelle Bewegung, Verdeckungen und wechselnde Beleuchtung erschweren das Tracking. Loop Closure und globale Optimierung können helfen, sind aber keine automatische Garantie und hängen von der verwendeten Pipeline ab.

### 4.5 Genauigkeit ist mehr als ein Zahlenwert

Zu unterscheiden sind Auflösung, Wiederholbarkeit, absoluter Maßfehler und visuelle Detailtreue. Ein schön texturiertes Ergebnis kann eine verzogene Geometrie besitzen; viele Punkte garantieren keine hohe Messgenauigkeit. Ein einzelner Fehlerwert ohne Entfernung, Material, Messmethode, Szenengröße und Softwareversion ist wenig aussagekräftig. Für Fertigung, sicherheitsrelevante oder baurechtlich verbindliche Maße sind geeignete, validierte Messverfahren erforderlich.

## 5. Vergleich der drei wichtigsten Aufnahmeverfahren

| Kriterium | LiDAR-gestützte Raumrekonstruktion | Fotogrammetrie | 3D Gaussian Splatting |
|---|---|---|---|
| Eingangsdaten | Tiefeninformationen, Kamerabilder und Tracking | Überlappende Fotos, optional Zusatzdaten | Überlappende Bilder und rekonstruierte Kamerapositionen, je nach Verfahren zusätzliche Daten |
| Typisches Ergebnis | Punktwolke oder Mesh, gegebenenfalls semantischer Raum | Texturiertes Mesh und/oder Punktwolke | Ansammlung trainierter 3D-Gauss-Elemente |
| Stärke | Rasches räumliches Feedback und metrische Tiefenhinweise | Geometrische und optische Details geeigneter statischer Objekte | Eindrucksvolle Darstellung komplexer Ansichten |
| Typische Schwächen | Feine Kanten, Glas, Glanz, Drift | Fehlende Textur, Bewegung, Reflexionen, Rechenaufwand | Keine direkt nutzbare saubere Polygonoberfläche; Probleme bei unbeobachteten Bereichen und dynamischen Szenen |
| Maßstab | Messwerte unterstützen metrischen Maßstab; Fehler bleiben | Ohne Referenz oder Zusatzdaten oft kein absoluter Maßstab | Maßstab und Genauigkeit hängen von Eingaben und Rekonstruktion ab |
| Gute Anwendung | Räume und schnelle Bestandsaufnahme | Einzelobjekte und texturierte Assets | Anschauliche Web-Präsentation und virtuelle Besichtigung |

Die Verfahren konkurrieren nicht zwingend: Fotos können die Textur ergänzen, während Tiefendaten Maßstab und Geometrie stützen. Diese Fusion verbessert nicht automatisch jede Szene; sie muss anhand von Vergleichsdaten bewertet werden.

## 6. Fotogrammetrie im Detail

Bei Structure from Motion werden korrespondierende Bildmerkmale gefunden und Kamerapositionen sowie eine zunächst dünne Punktwolke geschätzt. Multi-View Stereo nutzt mehrere Ansichten für dichtere Oberflächeninformationen. Daraus können Oberflächen und Texturen erzeugt werden. Manche Produkte verwenden andere Verfahren; die genauen Schritte und Ergebnisse hängen vom Werkzeug ab.

Apple empfiehlt für RealityKit Object Capture gut ausgeleuchtete, scharfe Bilder mit erheblicher Überlappung; als Orientierung werden mindestens etwa 70 % genannt [6]. Der genaue Bedarf hängt von Objekt, Oberfläche und Verfahren ab. Sinnvoll sind Bilder in mehreren Höhen und Winkeln, gleichmäßiges Licht und ein ruhiges Objekt. Dünne, durchsichtige, stark glänzende oder einfarbige Objekte sind besonders schwierig. Beim Drehteller muss der Hintergrund zur Aufnahmemethode passen; unbeabsichtigte Hintergrundbewegung kann die Rekonstruktion stören.

Tiefendaten können dem System nach Apples Dokumentation helfen, den realen Maßstab zu bestimmen; Bilder ohne Tiefe können ebenfalls verarbeitet werden [6]. Ein Vergleichsmaß oder Marker bleibt sinnvoll, wenn Maße wichtig sind. Höhere Schärfentiefe durch Abblenden kann die Ausleuchtung reduzieren und längere Belichtungen nötig machen: Bewegungsunschärfe wird dadurch nicht automatisch vermieden.

## 7. Gaussian Splatting und dynamische Szenen

3D Gaussian Splatting stellt eine Szene durch viele räumliche Gauss-Verteilungen mit Position, Ausdehnung, Orientierung, Deckkraft und Farbe dar. Aus trainierten Ansichten lassen sich oft optisch sehr überzeugende neue Blickwinkel rendern. Dies ist besonders für Präsentationen interessant, wenn die Szene nicht zwingend als klassisches CAD-Mesh bearbeitet werden muss.

Grenzen: Nicht erfasste Rückseiten werden nicht zuverlässig rekonstruiert. Spiegel, Glas und bewegte Objekte können ebenfalls fehlerhaft sein; blickwinkelabhängige Effekte werden teilweise gut dargestellt, aber nicht garantiert korrekt. Splat-to-Mesh-Verfahren wie SuGaR oder Gaussian Frosting sind Forschungs- bzw. Spezialansätze, keine universelle Ein-Klick-Garantie für saubere, animierbare oder maßhaltige Modelle. Für Animation können Segmentierung, Remeshing und Rigging nötig sein.

4D-Ansätze ergänzen den zeitlichen Verlauf dynamischer Szenen, sind aber für eine erste Scanner-Version deutlich komplexer. Das in der Quelle genannte TSOG ist ein Spezialformat bzw. Forschungsansatz und sollte erst nach Überprüfung von Implementierung, Lizenz und Browserunterstützung eingeplant werden. SPZ und Splat-PLY können für komprimierte bzw. interoperable Darstellung relevant sein; konkrete Kompressionsraten und Kompatibilität hängen von Inhalt, Version und Viewer ab.

## 8. Apple-Schnittstellen und ihre Rollen

### 8.1 ARKit

`ARWorldTrackingConfiguration` unterstützt räumliches Tracking. Auf geeigneten Geräten kann `sceneDepth` zugeschaltet werden; ARKit liefert laut Apple Tiefeninformationen passend zum Kamerabild [2]. `smoothedSceneDepth` glättet Tiefendaten über die Zeit [3]. `sceneReconstruction` liefert bei Unterstützung ein polygonales Umgebungsnetz [4]. Vor Aktivierung sind die jeweiligen `supports...`-Prüfungen notwendig.

ARKit-Scene-Depth ist ein durch das System bereitgestelltes Tiefenprodukt, keine zugesicherte Schnittstelle zu sämtlichen unverarbeiteten Einzelphotonen oder zum internen Lasermuster. Entwickler müssen Datenformate, Zeitbezug und Kameratransformationen korrekt verarbeiten.

### 8.2 AVFoundation

Apples Beispiel zur LiDAR-Kamera beschreibt synchronisierte Video- und Tiefendatenerfassung sowie Foto-Tiefendaten auf unterstützter Hardware [5]. Apple nennt perspektivisch angepasste Bild- und Tiefenströme mit gleichem Sichtfeld und Seitenverhältnis, obwohl sich die Auflösungen unterscheiden können [7]. Verfügbarkeit und Formate müssen zur Laufzeit ermittelt werden. Gleichzeitige Nutzung bestimmter Kamera- und AR-Funktionen darf nicht vorausgesetzt werden.

### 8.3 RoomPlan

RoomPlan eignet sich für strukturierte Innenraumerfassung mit semantischen Elementen wie Wänden und Öffnungen. Es ist kein Ersatz für eine vollständige fotorealistische Rekonstruktion oder eine garantierte Bauvermessung. Die tatsächlich erkannten Kategorien, Exportmöglichkeiten und Gerätelimits müssen gegen die aktuelle API-Dokumentation und eigene Tests geprüft werden [8].

### 8.4 Object Capture / RealityKit

Apple dokumentiert fotobasierte Objektrekonstruktion über `PhotogrammetrySession` auf geeigneten Macs und ausgewählten iOS-Geräten mit LiDAR [9]. Eine geführte native Aufnahme ist mit entsprechenden Object-Capture-Komponenten möglich. Aufnahme und Rekonstruktion sind zwei unterschiedliche Schritte; Verfügbarkeit, Speicherkosten und Laufzeit müssen gerätespezifisch geprüft werden. Einzelne in der Quelldatei genannte Zustandsnamen und interne Maskierungsmechanismen sollten vor Implementierung gegen die konkrete SDK-Version verifiziert werden.

## 9. Was eine Web-App kann – und wo ihre Grenze liegt

Eine normale Webseite kann nach Zustimmung über geeignete Browser-APIs Kamerabilder beziehen, Bilder hochladen und 3D-Daten mit WebGL-basierten Viewern darstellen. HTTPS, Berechtigungen, Browser- und Systemversion sowie verfügbare Formate beeinflussen die tatsächliche Nutzung. Browser-Unterstützung für WebGPU und WebXR muss zur Laufzeit geprüft werden; WebGL- und WebGPU-Implementierungen besitzen unterschiedliche Rendering- und Compute-Möglichkeiten. Ein WGSL-Compute-Shader ist keine WebGL-Funktion.

Die geprüften Apple-Quellen beschreiben LiDAR-Tiefenzugriff als native Framework-Funktion. Ein allgemeiner Zugriff auf ARKit-`sceneDepth` oder AVFoundation-LiDAR-Tiefenframes durch JavaScript in einer normalen iPhone-Webseite wird durch diese Quellen nicht belegt. In einem WebKit-Fehlerbericht erklärte ein WebKit-Mitarbeiter im März 2026, WebXR werde auf iOS nicht unterstützt [10]; dieser Stand ist kein Beweis für alle späteren Versionen oder Spezialbrowser. Daher ist ein aktueller Gerätetest erforderlich. Aus experimentellem oder spezialisiertem Browser-Support darf keine zuverlässige allgemeine Verfügbarkeit abgeleitet werden.

**Konsequenz:** Eine reine Webseite kann eine Foto-Scan-Pipeline und einen 3D-Viewer bieten. Für eine belastbare LiDAR-Erfassung empfiehlt sich eine native iOS-Komponente oder der Import aus einer geeigneten Scanner-App. Eine PWA oder ein einfaches WKWebView erhält nicht allein durch Installation automatisch einen nativen LiDAR-Zugriff.

## 10. Drei mögliche Produktarchitekturen

### A. Web-only: Fotos aufnehmen und rekonstruieren

Ablauf: Browser-Kamera oder Foto-Upload → Qualitätskontrolle → lokale oder serverseitige fotogrammetrische Verarbeitung → Modell im Web ansehen → Export.

Vorteile: Link-basiert, plattformübergreifend, keine eigene native Installation als Grundbedingung. Grenzen: keine nachgewiesene direkte LiDAR-Tiefenpipeline im normalen iOS-Browser, potenziell lange Upload- und Rechenzeiten, zusätzliche Infrastruktur bei Serververarbeitung. Für einfache Zugänglichkeit und einen frühen Viewer-Prototyp gut geeignet.

### B. Hybrid: native Erfassung plus Web-App

Ablauf: Native iOS-App erfasst je nach Modus RGB, ARKit-Tiefe, Posen oder System-Mesh → lokale Prüfung und optional Kompression → sicherer Upload oder Dateiexport → Web-App verarbeitet, zeigt und verwaltet → Ergebnisse exportieren.

Vorteile: Zugriff auf dokumentierte iOS-Frameworks, flexible Weboberfläche, mehrere Ausgabearten. Grenzen: native Entwicklung, App-Verteilung, Versionspflege und Synchronisation. **Dies ist meine Empfehlung, falls echte LiDAR-Erfassung Kernanforderung ist.** Ein eigener Wrapper ist nur dann sinnvoll, wenn er eine ausdrücklich implementierte und abgesicherte native Brücke besitzt.

### C. Native Komplett-App

Erfassung, Verarbeitung, Ansicht und Export erfolgen weitgehend auf dem iPhone. Vorteile: kurze Wege, potenziell Offline-Nutzung und lokaler Datenschutz. Grenzen: Entwicklungskosten, Gerätespeicher, Energie und thermische Belastung; aufwendige Rekonstruktionen können externe Rechenleistung erfordern.

### D. Import-first als schneller Machbarkeitstest

Bestehende Apps können Testscans exportieren, die ein eigener Web-Viewer importiert. Damit lassen sich Nutzeroberfläche, Dateiformate und Darstellung überprüfen, bevor eine vollständige eigene Erfassung entwickelt wird. Export, kommerzielle Nutzung, API-Zugriff und Preise des jeweiligen Anbieters sind vorab separat zu prüfen.

## 11. Vorgeschlagene Komponenten des Hybridsystems

1. **Erfassung:** ARKit-/AVFoundation-Session mit transparenten Berechtigungen und Geräteprüfung. Räume und Einzelobjekte als getrennte Modi.
2. **Qualitätskontrolle:** Hinweise auf Trackingverlust, fehlende Abdeckung, unscharfe Fotos, wenig Licht und übermäßige Bewegung. Wenn die API einen Zustand nicht zuverlässig meldet, keine Scheinsicherheit anzeigen.
3. **Datenpaket:** Projektkennung, Zeitstempel, Version, Einheiten, Kameraintrinsik und -pose, RGB, Tiefen- und Confidence-Daten soweit verfügbar, Datenformate und Datenschutzstatus. Große Daten in Blöcken speichern.
4. **Verarbeitung:** geeignete Bildauswahl, zeitliche Zuordnung, Tiefenfilterung, Registrierung, 3D-Fusion, optional Mesh-Erzeugung, Texturierung und Kompression.
5. **Web-App:** Projektübersicht, 3D-Viewer, Navigation, Sichtbarkeitsoptionen und Download. Messungen nur mit klar kommunizierter Genauigkeitsgrenze.
6. **Export:** Anwendungsabhängig zum Beispiel GLB/glTF für Web-Meshes, USDZ für kompatible Apple-Workflows, PLY für Punktwolken und je nach Pipeline OBJ. Konkrete Attribute und Unterstützung testen.
7. **Betrieb:** lokale Zwischenspeicherung, Wiederaufnahme fehlgeschlagener Uploads, Löschfunktion, Verschlüsselung bei Übertragung, klare Datenaufbewahrung und Kostenkontrolle.

## 12. Verarbeitungspipeline und Algorithmen

### 12.1 Bild und Tiefe zusammenführen

RGB- und Tiefenbilder können unterschiedliche Auflösungen und Koordinatensysteme besitzen. Synchronisation, Kamerakalibrierung, Orientierung und korrekte Projektion sind Voraussetzungen für gute Farben und Geometrie. Bei AVFoundation ist laut Apple die vom System bereitgestellte LiDAR-Tiefe auf den zugehörigen Videostrom perspektivisch abgestimmt [7]; Details anderer Kombinationen sind gesondert zu prüfen. Occlusion-Tests verhindern, dass Hintergrundfarben auf Vordergrundflächen übertragen werden.

### 12.2 Depth Completion

Depth Completion ergänzt lückenhafte Tiefe mithilfe von RGB-Bild, benachbarten Tiefenwerten oder trainierten Modellen. Aus einem ergänzten Tiefenbild lässt sich eine sogenannte Pseudo-Punktwolke ableiten. Das kann optisch dichte Daten liefern, erzeugt aber auch geschätzte Bereiche und mögliche Halluzinationen. Geschätzte Werte dürfen nicht als unabhängige physikalische Messpunkte ausgegeben werden. Für ein erstes Produkt ist zunächst der Vergleich der direkt verfügbaren Tiefenprodukte sinnvoll.

### 12.3 Registrierung und Geometrie

ICP richtet überlappende Punktwolken iterativ aus; das Ergebnis hängt von Startpose, Überlappung und Ausreißern ab. NDT ist eine alternative Registrierungsmethode. RANSAC kann beispielsweise Ebenen robust aus verrauschten Daten schätzen. Voxel-Downsampling reduziert Datenmengen; Ausreißerfilter und kantenbewusste Glättung reduzieren Rauschen. TSDF-Fusion und Marching Cubes sind mögliche Wege zum Mesh; Poisson-Rekonstruktion ist ein weiterer Ansatz mit eigenen Annahmen und Risiken. Kein Verfahren ist universell überlegen.

Automatisch erkannte Ebenen und Primitive können Wände und Flächen vereinfachen. Dabei können reale Unebenheiten oder Details verschwinden. Eine Qualitätsansicht sollte nach Möglichkeit sichtbar machen, wo Daten gemessen, geglättet oder ergänzt wurden.

### 12.4 Komplexe Forschungsansätze richtig einordnen

Die Quelldokumente erwähnen unter anderem PointNet++, Transformer, Bird’s-Eye-View-Fusion, LOAM, LeGO-LOAM, Faktorgrafen und lernbasierte Segmentierung. Das sind interessante Ansätze aus 3D-Forschung, Robotik und Fahrzeugtechnik. Sie sind nicht automatisch die beste oder verfügbare Lösung für ein mobiles iPhone-Produkt. Zuerst sollten Tracking, Datenzugang und Qualitätsmetriken mit einer einfachen Baseline funktionieren. Modelltraining und große neuronale Pipelines erst nach konkreter Bedarfsmessung hinzufügen.

### 12.5 Intensität und Reflektivität

Einige professionelle LiDAR-Systeme stellen Intensitäts- oder Reflektivitätsinformationen bereit. Die Quellen empfehlen deren Nutzung; sie belegen aber nicht, dass diese Werte über die relevanten iPhone-APIs verfügbar sind. Nur dokumentierte und tatsächlich getestete Datenfelder einplanen.

## 13. Werkzeuge und Formate

| Werkzeug | Stärken | Einordnung |
|---|---|---|
| ARKit / AVFoundation | Native Erfassung, Tracking, Tiefe und Systemfunktionen | Ausgangspunkt für iPhone-Sensorintegration |
| RealityKit / Object Capture | Geführte Aufnahme und fotobasierte Objekterstellung | Geräte- und API-Verfügbarkeit prüfen |
| RoomPlan | Semantische Innenraumerfassung | Strukturmodell statt universeller Präzisionsscanner |
| Open3D | Punktwolken, Registrierung, Filterung, Python/C++ | Gut für Prototyping und Offline-Auswertung |
| PCL | Umfangreiche C++-Punktwolkenverarbeitung | Nützlich bei C++-/Robotik-Integration, nicht zwingend erforderlich |
| PyTorch3D | 3D-Operatoren und ML-Forschung | Erst bei begründetem ML-Bedarf |
| WebGL-basierte 3D-Engines | Interaktive Browserdarstellung | Kompatibilität und Speicherkosten auf iPhone testen |
| WebGPU | Moderne GPU-Funktionen | Laufzeitprüfung und Fallback erforderlich |
| PyVista / laspy | Visualisierung bzw. LAS-Daten | Für passende Analyse- und Austauschaufgaben |

GLB/glTF eignet sich häufig für webtaugliche Meshes. USDZ ist im Apple-Ökosystem verbreitet. OBJ unterstützt Meshes, ist aber bei Material- und Austauschdetails sorgfältig zu testen. PLY kann Punkte oder Meshes enthalten; Attribute sind nicht immer einheitlich. LAS/LAZ ist für georeferenzierte Punktwolken verbreitet, benötigt aber saubere Angaben zu Koordinatensystem und Einheiten. Ein Splat-PLY darf nicht mit einem gewöhnlichen farbigen Punktwolken-PLY gleichgesetzt werden.

Polycam und Scaniverse werden in den Quellen als Beispiele genannt. Ihre heutigen Funktionen, Preise, Exportoptionen, Serververarbeitung und Lizenzbedingungen wurden für diesen Bericht nicht vollständig geprüft. Eine Anbieter-API oder ein spezieller Export darf daher nicht als bestehende Projektzusage behandelt werden.

## 14. Aufnahmeempfehlungen

### Räume

- Vor Beginn Beleuchtung einschalten und empfindliche oder private Inhalte aus dem Sichtfeld entfernen.
- Langsam und kontinuierlich gehen; die Kamera nicht ruckartig schwenken.
- Für Überlappung zwischen benachbarten Ansichten sorgen; schwierige Bereiche aus mehreren Winkeln erfassen.
- Strukturlose Wände, Spiegel, Fenster und verdeckte Ecken besonders kontrollieren.
- Bei Trackingverlust oder offensichtlichen Doppelkonturen zurückgehen oder den Abschnitt neu erfassen.
- Einen oder mehrere bekannte Abstände und ein längeres Referenzmaß mit dokumentieren.
- Große Flächen in nachvollziehbare Abschnitte aufteilen und deren Zusammensetzung kontrollieren.

### Einzelobjekte

- Objekt stabil platzieren und vorwiegend diffuse, gleichmäßige Beleuchtung nutzen.
- Fotos auf mehreren Höhen aufnehmen, mit ausreichender Überlappung; scharfe Bilder bevorzugen.
- Glänzende, transparente und stark einfarbige Flächen als schwierig einstufen. Abnehmbare Hilfsmarkierungen oder geeignete Scan-Sprays nur nach Materialverträglichkeit und Erlaubnis einsetzen.
- Wenn möglich auch Ober- und Unterseite erfassen; beim Umdrehen die Veränderung kontrolliert halten.
- Ein reales Vergleichsmaß aufnehmen. Für passgenaue Teile zusätzliche Messmittel verwenden.

## 15. Testplan: So wird aus Behauptungen belastbare Evidenz

### 15.1 Kompatibilität

Tatsächliches iPhone-Modell, iOS-Version, Browser-Version und App-Build protokollieren. Kamera-Zugriff, ARKit-Unterstützung, verfügbare Tiefen-/Confidence-Formate, native Mesh-Unterstützung, WebGL, WebGPU und gegebenenfalls WebXR jeweils zur Laufzeit testen. Ergebnisse nach Gerät und Version festhalten, keine Annahme aus Produktnamen ableiten.

### 15.2 Messgenauigkeit

Referenzobjekte und Räume mit verlässlich gemessenen Abständen vorbereiten: kurze und lange Distanzen, ebene Flächen, Kanten, Winkel, dunkle und helle Oberflächen. Mehrere Entfernungen, Blickwinkel und Beleuchtungen sowie wiederholte Scans testen. Für jeden Test Referenzwert, gemessenen Wert, absolute Abweichung, relative Abweichung, Wiederholbarkeit, Trackingbedingungen und genutzte Verarbeitung dokumentieren. Bei größeren Räumen zusätzlich Anfangs-/Endabweichung und Drift aufnehmen. Zahlen erst veröffentlichen, wenn Messverfahren und Stichprobe genannt werden.

### 15.3 Ergebnisqualität

Vollständigkeit, sichtbare Löcher, Doppelkonturen, Kantenqualität, Texturversatz, Modellgröße, Ladezeit, Bildrate, Energieverbrauch und Temperaturentwicklung bewerten. Ein optisch schöner Scan kann geometrisch schlecht sein; beide Kategorien getrennt beurteilen. Für Messfunktionen tolerierbare Fehler pro Anwendungsfall festlegen.

### 15.4 Robustheit und Datenschutz

Berechtigung verweigern, App unterbrechen, Speicher füllen, Netzwerk verlieren, Upload abbrechen und fortsetzen, große Dateien laden und Export auf Zielgeräten öffnen. Bei menschlichen Motiven Einwilligung und sensible Rauminformationen berücksichtigen. Erfassung und Upload sollen klar erkennbar sein; Speicherung und Löschung müssen verständlich sein.

## 16. Umsetzungsvorschlag in Phasen

**Phase 0 – Ziel und Nachweise:** Erstes Szenario wählen: Raum, Einzelobjekt oder beides. Zielgenauigkeit, Offline-Bedarf, Datenschutz, Kostenrahmen und gewünschte Ausgabeformate festlegen. Gerät und Softwareversion konkret testen.

**Phase 1 – Viewer und Import:** Weboberfläche mit lokalem Dateiimport, 3D-Navigation und mindestens einem verlässlich unterstützten Mesh-Format bauen. Reale Beispielscans auf dem iPhone testen; keine LiDAR-Erfassung versprechen.

**Phase 2 – Native Sensorprobe:** Kleine iOS-Test-App mit Geräteprüfung, ARKit-Tiefenanzeige, Trackingzustand und Speicherung eines kleinen Datensatzes. Messwerte und Dateigröße dokumentieren.

**Phase 3 – Erste vollständige Pipeline:** Einen klar begrenzten Raummodus oder Objektmodus implementieren. Datenpaket, Verarbeitung, Qualitätskontrolle und Import in den Web-Viewer verbinden.

**Phase 4 – Qualitätsausbau:** Vergleich zwischen System-Mesh und eigener Verarbeitung, bessere Texturen, Scan-Fortsetzung nur bei ausreichend geprüftem Tracking, Wiederaufnahme von Uploads und klarer Export.

**Phase 5 – Erweiterungen:** Fotogrammetrie, Splat-Anzeige, optionale Server-/GPU-Berechnung, erweiterte Bearbeitung und zusätzliche Exportformate erst nach Bedarf und Kostenvergleich.

## 17. Risiken und offene Entscheidungen

| Frage | Bedeutung | Nächster Schritt |
|---|---|---|
| Was soll hauptsächlich gescannt werden? | Räume, Menschen und kleine technische Teile benötigen verschiedene Methoden | Zwei bis drei reale Testszenen auswählen |
| Wie genau müssen Maße sein? | Bestimmt Messverfahren und Qualitätsanspruch | Konkrete Toleranzen je Anwendung definieren |
| Muss alles im Browser funktionieren? | Beeinflusst direkten Zugriff auf native Sensoren | Hybrid mit Web-only anhand echter Gerätetests vergleichen |
| Ist eine native Begleit-App akzeptabel? | Ermöglicht dokumentierten iOS-Sensorzugriff | Prototyp und Verteilungsweg klären |
| Offline oder Server? | Bestimmt Datenschutz, Leistung, Upload und Kosten | Datenmengen und gewünschte Privatsphäre festlegen |
| Ausgabeziel? | Präsentation, Spiel, CAD und Grundriss brauchen verschiedene Daten | Priorisierte Exportformate festlegen |
| Wie wird Qualität nachgewiesen? | Verhindert falsche Erwartungen und ungeeignete Messnutzung | Referenzobjekte und dokumentierte Testmatrix erstellen |

## 18. Korrekturen und Einschränkungen gegenüber den Ausgangstexten

- **Spezifische interne Sensorbezeichnungen:** IMX591, IMX905, IMX972, IMX973 und IMX914 werden in den Quellen behauptet. Ohne belastbaren gerätespezifischen Nachweis nicht als gesichert übernehmen.
- **Genauigkeit:** 5 mm pro Messpunkt, unter 1,5 cm oder allgemein niedrige Millimeterwerte sind nicht als universelle iPhone-18-Pro-Werte belegt. Bedingungen und Testmethode sind entscheidend.
- **Punktdichte und 576 Punkte:** Werte aus anderen Geräten, Studien oder Verarbeitungsstufen sind nicht automatisch auf dieses Gerät oder jedes ARKit-Tiefenbild übertragbar.
- **Dunkelheit:** Aktive Tiefenerfassung bedeutet keine garantierte vollständige Rekonstruktion ohne sichtbares Licht.
- **Schatten und Schärfe:** Abblenden vergrößert häufig die Schärfentiefe, erfordert aber mehr Licht oder längere Belichtung; es beseitigt Bewegungsunschärfe nicht automatisch.
- **Geschlossene Netze:** ARKit liefert eine geschätzte Oberflächenrekonstruktion, nicht zwingend ein geschlossenes, druckbares oder CAD-taugliches Volumen.
- **Fotogrammetrie:** Braucht weder grundsätzlich eine Cloud noch immer Hunderte Fotos. Unterstützte Geräte können bestimmte Rekonstruktionen lokal durchführen [9].
- **Splatting:** Ist keine garantierte Lösung für Glas und Spiegel und erzeugt nicht von selbst ein brauchbares CAD-Mesh.
- **Performance:** Aussagen wie „60–90 Sekunden“, bestimmte Kompressionsraten oder „kein thermisches Throttling“ sind ohne konkrete Messung nicht belastbar.
- **Web:** WebGL und WebGPU sind verschiedene APIs; native ARKit-Funktionen sind nicht automatisch im Browser verfügbar.
- **BIM:** LOD-Stufen beschreiben den Entwicklungs- und Informationsstand; aus einer LOD-Zahl allein folgt keine bestimmte geometrische Messgenauigkeit.
- **Rohdaten:** ProRAW ist nicht gleichbedeutend mit vollkommen unverarbeiteten Sensordaten; Video- und Fotoformate sowie deren Metadaten sind gesondert zu prüfen.
- **LiDAR-Trends:** FMCW, MEMS, OPA und Fahrzeug-LiDAR sind nützlicher Hintergrund, aber keine Aussage über das konkret verbaute iPhone-System. MEMS verwendet bewegliche Mikrostrukturen; die pauschale Aussage, alle unter „solid state“ vermarkteten Systeme hätten keinerlei bewegliche Teile, ist zu grob.
- **Quellenqualität:** Die Hardware-Datei enthält beschädigte Formeln und Platzhalterzeichen sowie Links auf frühere Gerüchte. Solche Stellen wurden nicht als präzise Spezifikationen übernommen.

## 19. Fazit und Empfehlung

Für dieses Projekt erscheint ein modularer Aufbau am sinnvollsten: ein webbasierter Viewer und Projektbereich, ergänzt um eine native iOS-Erfassung, sobald LiDAR tatsächlich zum Kern gehört. Fotogrammetrie für detailreiche Objekte und LiDAR für räumliche Erfassung können später nebeneinander bestehen. Gaussian Splatting wäre eine zusätzliche Visualisierungsoption für besonders eindrucksvolle Szenen, während Meshes und strukturierte Raummodelle für andere Aufgaben geeigneter sind.

Der schnellste belastbare nächste Schritt ist ein Vergleich auf deinem tatsächlichen iPhone: ein Raum und zwei sehr unterschiedliche Objekte, jeweils mit Referenzmaßen. Danach lässt sich entscheiden, ob das erste Produkt vorrangig ein Raumscanner, ein Objektscanner oder eine vielseitige Scan-Plattform sein soll.

## Quellen und Nachvollziehbarkeit

### Projektmaterial

- „IPhone 18 Pro - lidar-foto.txt“: gerätebezogene LiDAR-Aussagen, Anwendungen und Grenzen.
- „LIDAR.txt“: Sensorfusion, Algorithmen, Hardwaretrends, Bibliotheken und praktische Ansätze.
- „Hardware-Architektur, Sensor-Integration und räumliche Datenerfassung des iPhone.txt“: Kameras, iOS-APIs, Fotogrammetrie, Splats und mögliche App-Pipelines.
- Sichtbarer Chatkontext des Projekts „3DLidar App für iphone 18pro webapp“; weitere Chatverläufe lagen nicht vollständig vor.

### Überprüfte externe Quellen

[1] Apple, iPhone 18 Pro – technische Daten: https://www.apple.com/iphone-18-pro/specs/

[2] Apple Developer, ARKit `sceneDepth`: https://developer.apple.com/documentation/arkit/arconfiguration/framesemantics-swift.struct/scenedepth

[3] Apple Developer, `smoothedSceneDepth`: https://developer.apple.com/documentation/arkit/arframe/smoothedscenedepth

[4] Apple Developer, `sceneReconstruction`: https://developer.apple.com/documentation/arkit/arworldtrackingconfiguration/scenereconstruction

[5] Apple Developer, Capturing depth using the LiDAR camera: https://developer.apple.com/documentation/avfoundation/capturing-depth-using-the-lidar-camera

[6] Apple Developer, Capturing photographs for RealityKit Object Capture: https://developer.apple.com/documentation/realitykit/capturing-photographs-for-realitykit-object-capture/

[7] Apple Developer, `builtInLiDARDepthCamera`: https://developer.apple.com/documentation/avfoundation/avcapturedevicetypebuiltinlidardepthcamera

[8] Apple Developer, RoomPlan: https://developer.apple.com/augmented-reality/roomplan/

[9] Apple Developer, Creating 3D objects from photographs: https://developer.apple.com/documentation/realitykit/creating-3d-objects-from-photographs

[10] WebKit Bugzilla, Einordnung WebXR auf iOS in einem Fehlerbericht vom März 2026: https://bugs.webkit.org/show_bug.cgi?id=309550

Die Quellen [1–7], [9] und [10] wurden für die jeweils genannten Aussagen geprüft. [8] ist ein weiterführender Herstellerlink; die konkrete aktuelle Funktionsmatrix wurde nicht vollständig geprüft.
