# lidarMONK – Umsetzungsvorgabe: zentraler Daten- und Fusionscontroller

Stand: 2026-11-02 · Status: Arbeitsauftrag, keine Implementierungsbehauptung.

## 1. Ziel und verbindliche Produktentscheidung

lidarMONK ist eine Linux-Anwendung mit Weboberfläche für 3D-Erfassung von Objekten und Personen. Das iPhone liefert Daten aus drei bereits identifizierten kostenlosen Anwendungen: **Stray Scanner**, **WurldCam** und **SplatCapture Studio**. Zusätzliche iPhone-Fotos und -Videos sollen lokal am Linux-Rechner oder über einen später sicher eingerichteten Fernzugang importierbar sein.

Der Controller ist die **zentrale Verarbeitungseinheit**: Er nimmt die vorhandenen Datensätze auf, analysiert und verarbeitet sie, richtet sie aus, führt geeignete Informationen zusammen und erzeugt einen erweiterten gemeinsamen Datensatz. Das Ausgabeformat ist anhand der Anforderungen und tatsächlicher Informationen zu wählen; eine einzelne PLY-Datei allein darf nicht als verlustfreie Gesamtlösung ausgegeben werden. Auf Basis dieses Datensatzes entsteht eine vereinfachte lokale Vorschau mit begrenzter Punktzahl und, soweit technisch möglich, vereinfachtem Mesh und Texturen.

Die lokale Vorschau soll auf dem Linux-Rechner (i7-4790K, 32 GB RAM, keine GPU voraussetzen) ein Budget von **höchstens 300 Sekunden** anstreben. Bei Zeitüberschreitung: echte, klar gekennzeichnete Teilergebnisse bzw. aussagekräftiger Status, nicht bloß Erfolg melden. Dateiübernahme/-hashing großer Datenmengen und Wartezeiten sind gesondert zu messen; das Ende-zu-Ende-Ziel nicht als bereits erreicht behaupten. Keine Bezahl-API zur bloßen lokalen Steuerung. Optional kann das Ergebnis samt den vom Anbieter unterstützten Originaldaten anschließend extern verarbeitet werden.

## 2. Tatsächlich vorhandener Projektstand

Vor Implementierung aktuellen Default-Branch, README, Tests und AGENTS.md prüfen; parallele Änderungen respektieren. Ausgangspunkt zum Zeitpunkt dieses Auftrags:
- scan-lab/backend/lidarmonk_backend.py verarbeitet zwei Stray-/Wurld-/SplatCapture-Eingaben und optional eine dritte. SplatCapture wird derzeit nur als exportiertes points.ply gelesen; Bilder, COLMAP-Kameras und -Posen werden bislang nicht fusioniert.
- Stray-Ordner erwartet camera_matrix.csv, odometry.csv, rgb.mp4, depth/; Wurld als .webm/.mkv. Formatprüfung und reale Versionen anhand vorhandener Adapter und Originaldaten verifizieren.
- FPFH/RANSAC + ICP registrieren Eingaben; separate/joint/incremental sind drei vorhandene Punktwolkenstrategien, keine drei unabhängigen Rekonstruktionssysteme.
- Regionale CPU-TSDF-Fusion ist experimentell, verarbeitet im Ist-Zustand nur A/B; die dritte Punktwolke ergänzt combined-three.ply, nicht das TSDF-Mesh.
- RGB und Confidence werden bisher nicht bei der Geometriefusion genutzt. Starre Bewegungskorrektur ist kein nichtstarrer Personen-Tracker.
- Web-Uploadserver akzeptiert zwei Pflicht- und eine optionale dritte Aufnahme. GitHub-Pages-Testseite kann PLY als Punkte darstellen; sie ist kein laufendes Python-Backend. Reale iPhone-Datensätze und Safari-Upload wurden laut bisheriger Dokumentation nicht verifiziert.
- Weitere Grenzen und Setup: scan-lab/backend/README.md, scan-lab/README.md und docs/3D_LiDAR_iPhone_Gesamtbericht.md. Quellenmaterial unter docs/quellen/ ist nicht automatisch verifiziert.

Nicht wieder bei null anfangen oder vorhandene Funktionsnamen als neue Fähigkeiten ausgeben. Diese Datei beschreibt Soll-Zustand, nicht bereits implementierte Fähigkeiten.

## 3. Eingaben und technische Anforderungen

- Zwei oder drei der bestehenden Scanner-Exporte; optionale Fotos und Videos als ergänzende Eingaben. Nutzerfreundlich vorbereiten, dass nicht jede Datenart in jedem Auftrag vorliegen muss.
- Bestehende ZIP- und Größenprüfungen, Schutz vor Pfad-Traversal und Symlinks erhalten. Keine willkürlichen Server-Dateipfade aus entfernten Browseranfragen.
- Lokaler Import vom Linux-Rechner ohne Internet sowie Upload im vertrauten LAN. Optional später privater Fernzugang über authentifizierten HTTPS-Zugang; das aktuelle unverschlüsselte LAN-HTTP nicht öffentlich bereitstellen.
- Originaldateien und vorhandene Metadaten erhalten; HEIC/HEIF/JPEG/PNG und MOV/MP4 in gesonderter Vorverarbeitung prüfen. Bei Konvertierung Originale und Orientierung/Kalibrierung bewahren. Normale Fotos/Videos nicht als metrische LiDAR-Daten bezeichnen.
- Videos: repräsentative Frames nach Schärfe, Bewegungsunschärfe, zeitlicher Verteilung und Überschneidung auswählen. Verfahrensgrenzen und Auswahlliste protokollieren. Fotos/Video sind zusätzliche Bilddaten; Video-Frames sind keine automatisch unabhängige dritte geometrische Messmethode.
- Eingabeadapter pro Format liefern einen gemeinsamen, versionierten internen Vertrag mit Datensatz-ID, Dateiherkunft, Prüfsummen (wo verfügbar/budgetiert), Kameramodell, Intrinsik und Auflösung, Zeitstempeln, Pose und Koordinatenkonvention, metrischer Einheit, RGB, Tiefe, Confidence, Punktwolke und Verfügbarkeit/Unbekannt-Status. Niemals fehlende Daten erfinden.

## 4. Controller als zentraler Prozessor

Controller führt nicht nur Importe und externe Skripte aus, sondern besitzt die Verarbeitungspipeline und deren Zustandsmodell:

1. **Prüfen und inventarisieren:** Formate, Struktur, Kalibrierung, Einheiten und Unterstützung validieren; Fehler einem Eingabedatensatz zuordnen. Datentypen, mögliche Qualitäts- und Formatgrenzen dokumentieren.
2. **Budget planen:** 300-s-Deadline anhand monotoner Uhr, konfigurierbare CPU-/Speichergrenzen und bild-/frame-/punktadaptive Vorselektion. Teure Arbeit in terminierbaren Prozessen; Kinderprozesse kontrolliert beenden. Kein vollständiges Einlesen unbegrenzter Exporte ohne Schutz. Kosten und die fünf Minuten nicht vortäuschen.
3. **Daten vorbereiten:** aus RGB-D Punkte/Kameras ableiten, PLY laden, Fotos und Video-Frames auswählen, gegebenenfalls korrigierte Vorschauen erstellen. Originalauflösung für spätere Verarbeitung erhalten.
4. **Ausrichten:** Koordinaten, Maßstab, Achsen, Kameramodelle und Zeitstempel prüfen; robuste grobe Registrierung, ggf. Feinregistrierung und mehrere Scanbeziehungen verwenden. Wenn unzuverlässig: manuelle Korrektur erlauben oder Fusion explizit ablehnen. Symmetrien, fehlende Überlappung, Drift, bewegte Personen und Hintergrund beachten.
5. **Regional zusammenführen:** gemessene Geometrie mehrerer Eingaben möglichst nutzen; Unterstützung, Herkunft und Konflikte sichtbar machen. Unterschiedliche Confidence-Skalen nicht ohne Kalibrierung gleichsetzen. Widersprüche nicht blind mitteln. Beobachtungsanzahl nicht als Genauigkeit ausgeben. Erhalten, welche Quellen welche Region stützen.
6. **Erweiterten Datensatz ausgeben:** versioniertes Projektpaket mit Manifest, Originalen oder kontrollierten relativen Verweisen, Datensatz-IDs, Prüfsummen, Kalibrierungen, Posen, Transformationsmatrizen, Zeitstempeln, Foto-/Frameauswahl, Farb-/Tiefen-/Confidence-Daten soweit verfügbar, registrierten Punktwolken, Qualitäts- und Konfliktangaben, Verarbeitungsparametern und Programmversionen. Robustes Format nach Machbarkeitsprüfung wählen (z. B. Ordner/ZIP + JSON + PLY/GLB und ggf. COLMAP-kompatible Dateien); Formatentscheidung und Grenzen dokumentieren.
7. **Schnellvorschau ausgeben:** begrenzte Punktwolke; wenn valide und innerhalb Budget möglich vereinfachtes Mesh/Farben/Textur. Keine erfundenen Texturen, keine Genauigkeitsgarantie. Vorläufige Daten klar kennzeichnen.
8. **Zustand und Fehler:** Fortschritt je Phase, Abbruch, kontrollierter Timeout, Ergebnisse nur bei erfolgreicher Konsistenzprüfung als abgeschlossen kennzeichnen. Teilresultate und Gründe anzeigen, Originale niemals überschreiben.

Die Geometriefusion aller drei kompatiblen Scans ist ein explizites Ziel. Eine dritte Punktwolke nur nachträglich an das bisherige A/B-Mesh anzuhängen erfüllt die gewünschte gemeinsame Fusion nicht. Wenn eine Quelle nur als Punktwolke vorliegt, die tatsächliche Einbindung in den Geometrieprozess implementieren oder den eingeschränkten Umfang deutlich ausweisen; keine fiktiven RGB-D-Frames erzeugen.

## 5. Weboberfläche und Viewer

- Aufnahme A/B und optional C, zusätzliche Fotos/Videos, lokaler Import, motivbezogener Modus.
- Zeitbudget und Fortschritt sichtbar; nach Abschluss Preview sofort im lokalen Web-Viewer.
- Punktwolke, Mesh und Farb-/Texturdarstellung soweit tatsächlich implementiert; Quellen A/B/C getrennt und gemeinsam anzeigen. Orbit/Zoom, Ein-/Ausblenden, lokale Transformationen, manueller Korrekturvorgang, Qualitäts-/Konfliktansicht und Downloads.
- Tracking- oder Skalierungsfehler und nicht erfasste Bereiche anzeigen. Synthetische Demo nicht als realer Scan kennzeichnen. Lokales Projekt unabhängig von GitHub Pages lauffähig halten.
- Personenmodus muss Grenzen starrer Verarbeitung benennen; keine medizinische oder biometrische Genauigkeit zusichern.

## 6. Optionale externe hochwertige Verarbeitung

Anbieterunabhängige Adapter-Schnittstelle für einen **echten 3D-Rekonstruktions-/Bearbeitungsdienst**, nicht LLM als vermeintlicher Qualitätsersatz. Externe Verarbeitung ist optional und nur nach aktivem Start durch Nutzer. Controller stellt erweiterten Datensatz, lokale Vorschau und kompatible Quellen bereit; Adapter deklariert unterstützte Eingänge, Limits, Formate, Kosten und Datenschutz. UI zeigt exakt, welche Quellen der Anbieter nutzt oder ignoriert. Kosten- und Übertragungsvolumen vor Start anzeigen, soweit verfügbar; Ergebnisse zurückholen, neben lokaler Vorschau vergleichen und als separates Artefakt speichern. Niemals behaupten, ein Anbieter kombiniere Mesh + drei Datenquellen + RGB-D, bevor die API dies nachweislich unterstützt. Kein API-Key im Git, Browser oder Log. Bezahltes Konto, Schlüssel und kostenpflichtige Jobs nicht ohne ausdrückliche Einrichtung starten.

Ein externer Dienst oder RunPod muss benötigte Daten tatsächlich übertragen bekommen; Zugriff ist keine Netzwerkbeschleunigung. Bestehende Originale sind für spätere Nachbearbeitung zu erhalten. Ausgabequalität ist nicht garantiert; generierte Details sind von Messungen zu unterscheiden.

## 7. Umsetzungsreihenfolge und Akzeptanz

1. **Repository und Schnittstellen prüfen:** Formate, bestehende Tests, reale Grenzen und bestehende Sicherheitsmaßnahmen dokumentieren. Kleine synthetische Datensätze für Wiederholbarkeit.
2. **Verarbeitungscontroller und Projektformat:** typisierte Eingabe-/Ausgabeverträge, drei Adapter, Phase-/Deadline-/Fehlersteuerung und persistente Projektzustände. Originaldaten nicht ändern.
3. **Verarbeitung und Fusion:** alle drei kompatiblen Eingaben registrieren und tatsächlich nutzen; Transparenz bei nicht unterstützten Daten. Fotos/Video nicht als implementierte Rekonstruktion bezeichnen, bevor sie verarbeitet werden. Einheit, Kamera, Pose und Ausrichtung testen.
4. **Vorschau und Web-Viewer:** lokale Resultate direkt in der App; Quellüberlagerung, Konflikt- und Statusanzeige, Downloads. Erreichbarkeit im lokalen Betrieb prüfen.
5. **Lokaler Import und Projektpaket:** Wiederaufnahme eines Projekts, Export/Import, Integrität und reproduzierbare Metadaten. Fernzugang separat sicher vorbereiten.
6. **Externe Adapter:** nach verifizierter Auswahl echte API-Schnittstelle mit Kostenanzeige, begrenztem Upload und Rückimport; Lizenz und Nutzungsbedingungen prüfen.

Notwendige Tests: synthetische drei Quellen mit bekannter Transformation, fehlende/unterschiedliche Formate, ungenügende Überlappung und symmetrische Fehlregistrierung, Timeout samt Prozessbereinigung, Teilresultate und ungültige Archive, Projektpaket-Roundtrip und Herkunft, UI-Status, Offline-Betrieb und lokale Sicherheitsgrenzen. Reale Stray-, WurldCam- und SplatCapture-Exporte mit iPhone und Safari sowie der fünfminütige Test auf i7-4790K/32 GB sind separat erforderlich. Laufzeit und Ergebnisse nicht aus synthetischen Tests ableiten.

## 8. Quellen

- Apple ARDepthData und Confidence: https://developer.apple.com/documentation/arkit/ardepthdata
- Open3D Mehrfachregistrierung: https://www.open3d.org/docs/latest/tutorial/pipelines/multiway_registration.html
- COLMAP bekannte Kameraposen: https://colmap.github.io/faq.html
- Stray-Format: https://github.com/strayrobots/scanner/blob/main/docs/format.md
- Wurld: https://github.com/kmatzen/wurld
- SplatCapture Export: https://github.com/KuoFengYuan/splatify-anything/blob/main/docs/HISTORY_TRAINING_EXPORT.md
- Meshy Retexture als Beispiel für Teilfunktion, kein Beleg für multimodale Fusion: https://docs.meshy.ai/en/api/retexture

Lizenz- und Verfügbarkeitsangaben vor Produktintegration aktuell prüfen. Dieser Auftrag priorisiert nachvollziehbare Datenverarbeitung und einen brauchbaren Datensatz gegenüber nicht belegten Versprechen von perfekter Rekonstruktion.
