# lidarMONK: lokaler Import, Fernzugriff und optionale APIs

Stand: 2026-11-02. Entwurf; die nachfolgenden Funktionen sind nicht als implementiert bestätigt.

## Ziel
iPhone-Fotos, Videos und RGB-D-Exporte auf einem Linux-Rechner verarbeiten. Zwei Zugangswege: Dateien direkt am Rechner auswählen; optional unterwegs über eine geschützte Weboberfläche hochladen. Verarbeitung und Web-Viewer laufen standardmäßig lokal.

## Bestehender Stand
Das Backend unterstützt laut scan-lab/backend/README.md Stray/Wurld-Uploads und eine optionale dritte SplatCapture-Punktwolke. Foto-/Video-Fotogrammetrie und ein integrierter Ergebnisviewer sind dort noch nicht als implementiert belegt. Die vorhandene LAN-Oberfläche benutzt HTTP mit Zugangsschlüssel und ist nur für vertrauenswürdige Netze vorgesehen; sie ist nicht für direkte Veröffentlichung im Internet ausgelegt.

## Lokaler Dateizugriff
- Weboberfläche: Mehrfachauswahl und Drag-and-drop für Fotos, Videos und bestehende Exportformate; diese werden auch auf localhost über HTTP an den lokalen Prozess übertragen, aber nicht ins Internet.
- Optional verwalteter Importordner auf dem Rechner: Dateien registrieren oder kopieren, ohne erneute Netzwerkübertragung. Nur ausdrücklich konfigurierte Verzeichnisse; keine beliebigen Pfade aus Browseranfragen. Datei-Änderungen und Symlinks beachten, Quelle nicht überschreiben.
- Originale erhalten; HEIC/HEIF, JPG, PNG, MOV/MP4 zunächst prüfen, ausgewählte Arbeitskopien umwandeln; EXIF/Orientierung und ggf. vorhandene Zusatzdaten bewahren. Normale Bilder oder Videos nicht als LiDAR-Daten kennzeichnen.
- Foto- und Videofotogrammetrie benötigen separate Implementation, Unterstützung der Formate und installierte Verarbeitungstools.

## Fernzugriff
- Derselbe Linux-Server, Gerätezugang über privates Netz wie Tailscale Serve mit HTTPS und gerätegebundenen Zugriffsregeln: https://tailscale.com/docs/features/tailscale-serve
- Server an localhost binden; bestehende Tokenprüfung und Proxy-/Host-Kompatibilität prüfen. Kein direkter öffentlicher Betrieb der jetzigen HTTP-App. Rechner muss wach und erreichbar sein.
- Unterwegs Upload mit Fortschritt, Abbruch, Wiederaufnahme und Integritätsprüfung als geplante Funktion; iOS-Hintergrundverhalten real testen.
- Alternativ externe Ablage später prüfen, mit Aufbewahrung, Limits und Kosten. Jede Übertragung bleibt von Mobilfunk und Heim-Download abhängig.

## Optionale externe Rekonstruktions-API
- Provider-Adapter für Funktions- und Formatprüfung, Kostenvorschau, bewussten Auftragsstart, Status, Download und Fehlerbehandlung. Kein Anbieter als verfügbar oder integriert zugesichert.
- Schlüssel nur serverseitig und außerhalb des Repositorys; keine Geheimnisse im Browser. Anbieterbedingungen, Personenbilder, Speicherfristen, Löschung, Bildanzahl, Lizenzen, Bildübertragung, Kosten und Exportformate vor Einsatz prüfen.
- Das Hochladen zum Provider und Herunterladen der Ergebnisse ist weiterhin nötig. Bilder lokal auswählen/komprimieren nur als explizite Option und Qualitätsauswirkung prüfen.
- Lokaler und externer Weg erzeugen dokumentierte Projektartefakte und erscheinen im gleichen Viewer; Fähigkeiten und Koordinatensysteme unterscheiden.

## Umsetzung und Prüfung
1. Lokalen Import und gültige Typen mit kleinen echten iPhone-Dateien testen; Originale und Metadaten bewahren.
2. Backend für Foto-/Videodaten und CPU-Fotogrammetrie gesondert implementieren und auf Mint mit i7-4790K/32 GB validieren; COLMAP CPU plus OpenMVS als Kandidat, keine Laufzeitgarantie.
3. Ergebnisviewer für PLY/Mesh und dokumentierte Formate integrieren.
4. Fernzugriff privat absichern und Upload-Unterbrechung sowie Safari testen.
5. Provider erst nach konkreter Auswahl und Prüfung integrieren; Kosten und externe Datenverarbeitung ausdrücklich darstellen.

Zulieferungen und Experimente durch reale Referenzmaße evaluieren. Scans von Menschen enthalten sensible Bilddaten; Zugriff und Löschung im Produkt berücksichtigen.
