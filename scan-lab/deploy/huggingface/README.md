# Private Hugging Face Space – Bereitstellungsvorlage

Dieses Verzeichnis bereitet den bestehenden Python-Server für eine **private Docker Space** mit CPU Basic vor. Ein Hosting-Account und die Space-Erstellung sind dadurch nicht automatisch vorhanden. Die Vorlage ist nicht auf Hugging Face getestet; Docker war in der Entwicklungsumgebung nicht verfügbar.

## Einschränkungen

- Stand 2. November 2026: CPU Basic selbst hat laut Hugging Face keinen Stundenpreis; für eine neu erstellte Docker Space ist jedoch ein geeigneter bezahlter Plan wie PRO erforderlich. Den eigenen Tarif und eventuell aktivierte kostenpflichtige Hardware vor der Erstellung prüfen: https://huggingface.co/docs/hub/spaces-overview . Keine GPU, kein Upgrade und keine kostenpflichtige persistente Speicherung auswählen.
- Die Space muss **privat** sein; der Prototyp bietet keine sichere Mehrbenutzertrennung. Personenscans nur mit Einverständnis hochladen. Privacy-/Hostingbedingungen des Anbieters berücksichtigen.
- Ein Space-Secret `LIDARMONK_ACCESS_TOKEN` mit mindestens 32 zufälligen Zeichen ist erforderlich. Als Secret in den Space-Einstellungen hinterlegen, nicht in den Code, Chat, URL oder öffentliche Repositories schreiben. Der Server gibt es nicht ins Log aus. Der Besitzer gibt es in das Zugangsfeld der App ein; es wird für den Tab in `sessionStorage` gehalten und bei HTTP-Anfragen im Header übertragen.
- CPU Basic ist begrenzt und kann nach Inaktivität schlafen; Rechenzeit, Speicher und Uploadgrößen können einschränken. Die temporären Scans/Ergebnisse liegen auf dem Space-Datenträger und können bei Neustarts verloren gehen. Ergebnisse nach der Verarbeitung herunterladen.
- Das derzeitige Backend ist ein experimenteller Prototyp, keine zugesicherte Präzisionsvermessung, keine robuste nichtstarre Personenkorrektur und kein vollständiger SplatCapture-RGB-D-Importer.

## Vorlage erzeugen

Aus dem GitHub-Repository im Projektordner:

```bash
python3 scan-lab/deploy/huggingface/assemble.py /tmp/lidarmonk-space
```

Der Zielordner muss neu oder leer sein. Er enthält ausschließlich die benötigten Backend-Dateien, `Dockerfile` und Space-README; weder Testscans noch Geheimnisse werden hineinkopiert. Den Inhalt dieses Ordners anschließend in das **private** Space-Repository übertragen. Vor echtem Einsatz Build-Logs, Zugriffskontrolle, Upload, Verarbeitung und Download mit synthetischen Daten prüfen. Die Space-URL ist erst nach erfolgreichem Build bekannt.
