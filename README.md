# SIOCS Heizung – Home-Assistant-App

Home-Assistant-App, die eine Fernwärme-Übergabestation mit **SIOCS-Webportal** (SCHNEID, Regler MR-12) in Home Assistant einbindet. Das Portal hat keine offene Schnittstelle, deshalb bedient die App es wie ein Mensch im Browser und stellt die Werte als kleine REST-Schnittstelle bereit.

> **Inoffiziell.** Die App stammt nicht vom Hersteller oder vom Fernwärme-Betreiber. Befehle wirken auf die echte Anlage. Nutzung auf eigene Verantwortung, ohne Gewähr.

## Funktionen

| Funktion | Beschreibung |
|---|---|
| Messwerte lesen | Raumtemperatur, Raumsoll, Korrektur, Außentemperatur (gemittelt), Leistung, Spreizung, Wärmemenge, Volumen, Status. Standard: jede Minute. |
| Betriebsart steuern | Automatik, Aus/Frostschutz, Absenkbetrieb, Heizbetrieb, Zeitprogramm, Partymodus. |
| Korrektur steuern | Raumtemperatur-Korrektur der Fernbedienung, −5 bis +5 K in Schritten von 0,1 K. |
| Heizzeiten anzeigen | Wochenplan je Heizkreis, alle 6 Stunden gelesen (nur Anzeige). |

## Voraussetzungen

- Home Assistant OS oder Supervised (mit Apps/Add-ons), Architektur amd64 oder aarch64.
- Ein Zugang zu einem SIOCS-Webportal (Adresse, Benutzername, Passwort).
- Rund 300 MB freier Arbeitsspeicher für den integrierten Browser (Chromium).

## Installation in 5 Schritten

1. **Repository hinzufügen:** Einstellungen → Apps → App-Store → Menü (⋮) → Repositories → `https://github.com/friedlro/ha-siocs-heizung`.
2. **Installieren:** „SIOCS Heizung" öffnen und installieren (der erste Build lädt ein großes Browser-Image, das dauert einige Minuten).
3. **Konfigurieren:** Reiter „Konfiguration" → `url`, `username`, `password` eintragen → Speichern. Das Passwort steht nur dort, nie im Repository.
4. **Starten:** App starten, im Protokoll darf kein „login fehler" stehen.
5. **Entitäten anlegen:** Inhalt von `ha_configuration_snippet.yaml` in die `configuration.yaml` übernehmen und den Hostnamen der App eintragen (siehe unten), Konfiguration prüfen, neu starten.

Optional: `dashboard_heizung.json` als fertiges Dashboard (Dashboard → Raw-Konfigurationseditor).

Ausführlich: [Dokumentation](siocs_heizung/DOCS.md) und [INSTALL.md](INSTALL.md).

## Konfiguration der App

| Option | Pflicht | Standard | Bedeutung |
|---|---|---|---|
| `url` | ja | leer | Adresse deines SIOCS-Portals, z. B. `https://dein-portal.example/` |
| `username` | ja | leer | Benutzername im Portal |
| `password` | ja | leer | Passwort im Portal |
| `poll_seconds` | nein | 60 | Abfrage-Intervall in Sekunden (30–3600) |

Fehlt eine Pflichtangabe, beendet sich die App mit einer klaren Meldung im Protokoll.

## Entitäten in Home Assistant

Nach dem Einfügen des Snippets entstehen:

| Entität | Typ | Inhalt |
|---|---|---|
| `sensor.heizung_raumtemperatur` | Sensor | Raumtemperatur (°C) |
| `sensor.heizung_raumsoll` | Sensor | Raumsoll (°C) |
| `sensor.heizung_korrektur` | Sensor | aktuelle Korrektur (K) |
| `sensor.heizung_aussentemperatur_regelung` | Sensor | Außentemperatur, gemittelt (°C) |
| `sensor.heizung_leistung` | Sensor | Leistung (kW) |
| `sensor.heizung_spreizung` | Sensor | Spreizung (K) |
| `sensor.heizung_waermemenge` | Sensor | Wärmemenge (kWh, Energie-Dashboard geeignet) |
| `sensor.heizung_volumen` | Sensor | Volumen (m³) |
| `sensor.heizung_status` | Sensor | Betriebszustand laut Portal (z. B. „Aus/FS") |
| `sensor.heizung_betriebsart_gewaehlt` | Sensor | gewählte Betriebsart |
| `sensor.heizung_heizzeiten` | Sensor | heute geltende Heizzeit, ganze Woche im Attribut `schedule` |
| `select.heizung_betriebsart` | Auswahl | Betriebsart setzen |
| `number.heizung_korrektur_einstellen` | Zahl | Korrektur setzen (−5…+5 K) |

**Hostname der App:** Bei der Installation aus diesem Repository lautet er `<repo-kennung>-siocs-heizung` (z. B. `55ec2b33-siocs-heizung`). Du findest ihn in Einstellungen → Apps → SIOCS Heizung → Info. Im Snippet steht als Platzhalter `local-siocs-heizung`; ersetze ihn an drei Stellen.

## Betriebsarten

| Wert in HA | Portal-Eintrag |
|---|---|
| `auto` | Wahlschalter (Automatik) |
| `off` | MANUELL-AUS/FS |
| `setback` | MANUELL-Absenkbetrieb |
| `heat` | MANUELL-Heizbetrieb |
| `schedule` | MANUELL-Zeitprogramm |
| `party` | MANUELL-Partymodus |

Für den Normalbetrieb `auto` wählen. Manuelle Betriebsarten bleiben aktiv, bis du sie zurückstellst.

## Grenzen und Hinweise

- Entwickelt und getestet an **einer** Anlage (SIOCS-Portal mit Regler MR-12, Heizkreis HK0). Andere Portale oder Layouts können Anpassungen brauchen, siehe Dokumentation.
- Das Portal übernimmt Änderungen verzögert (10–30 s); die Werte in HA ziehen bis zur nächsten Abfrage nach.
- Heizzeiten werden nur angezeigt, nicht geändert.
- Die Steuerung wurde für `auto` und `setback` gezielt getestet. `heat` und `party` wurden im Betrieb beobachtet, `off` und `schedule` nicht ausprobiert.
- Das Portal ist Eigentum des Betreibers. Prüfe, ob automatisierter Zugriff erlaubt ist, und frage nicht öfter ab als nötig.

## Fehlersuche (Kurzfassung)

| Meldung im Protokoll | Bedeutung |
|---|---|
| `Bitte 'url' … eintragen` | Pflichtoption fehlt |
| `nach login: … Anmeldung …` | Login fehlgeschlagen: Zugangsdaten prüfen |
| `setzen fehlgeschlagen` | Portal hat den Dialog nicht geöffnet; die App versucht es bis zu dreimal |
| `auslese unvollstaendig` | Portalseite noch nicht vollständig geladen oder Layout abweichend |
| `ERR_NETWORK_CHANGED` beim Start | kurzer Netzwerkwechsel, löst sich selbst |

Weitere Details in der [Dokumentation](siocs_heizung/DOCS.md).

## Sicherheit

- Zugangsdaten liegen in den App-Optionen von Home Assistant und sind für HA-Administratoren sichtbar. Wenn das Portal es erlaubt, nutze einen eigenen Benutzer für die App.
- Die REST-Schnittstelle (Port 8099) ist **nicht** nach außen freigegeben, sie ist nur im internen Netz der Apps erreichbar.
- Teile keine Protokolle mit Zugangsdaten. Das Passwort steht nicht in Protokollen; der Diagnose-Endpunkt zeigt nur sichtbaren Seitentext.

## Dateien

| Datei | Zweck |
|---|---|
| `siocs_heizung/` | die App (Dockerfile, Skript, Konfiguration, Dokumentation) |
| `ha_configuration_snippet.yaml` | Sensoren, Auswahl, Zahl und Dienste für die `configuration.yaml` |
| `dashboard_heizung.json` | fertiges Dashboard |
| `INSTALL.md` | Kurzanleitung |
| `siocs_heizung/CHANGELOG.md` | Änderungen |
| `LICENSE` | MIT-Lizenz |

## Lizenz

[MIT-Lizenz](LICENSE), Copyright (c) 2026 Roland Friedl. Du darfst den Code nutzen, ändern und weitergeben; er wird ohne Gewähr bereitgestellt.
