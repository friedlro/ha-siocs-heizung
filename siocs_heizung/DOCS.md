# SIOCS Heizung – Dokumentation

## Inhalt

1. [Funktionsweise](#funktionsweise)
2. [Einrichtung](#einrichtung)
3. [Optionen](#optionen)
4. [REST-Schnittstelle der App](#rest-schnittstelle-der-app)
5. [Entitäten und Konfiguration in Home Assistant](#entitäten-und-konfiguration-in-home-assistant)
6. [Betriebsarten und Korrektur](#betriebsarten-und-korrektur)
7. [Heizzeiten](#heizzeiten)
8. [Zeitverhalten](#zeitverhalten)
9. [Fehlersuche](#fehlersuche)
10. [Eigenes Portal anpassen](#eigenes-portal-anpassen)
11. [Sicherheit und Datenschutz](#sicherheit-und-datenschutz)
12. [Bekannte Grenzen](#bekannte-grenzen)

## Funktionsweise

Das SIOCS-Webportal ist eine Wt-Webanwendung (C++). Sie hält eine Sitzung auf dem Server, jede Anzeige und jeder Klick läuft als Ereignis über `POST /vis?wtd=…`. Es gibt keine REST- oder JSON-Schnittstelle und die Element-IDs ändern sich bei jeder Sitzung.

Die App startet deshalb einen **Chromium-Browser** (Playwright), meldet sich im Portal an und bedient die Seite wie ein Mensch:

- **Lesen:** Die Werte werden über ihre **Beschriftung** gefunden, zum Beispiel steht neben „Leistung" der Zahlenwert in derselben Zeile. Das Thermostat-Bild wird relativ zur Beschriftung „Raumsoll.:" ausgewertet.
- **Steuern:** Ein Klick auf das Statuswort (zum Beispiel „Aus/FS") öffnet den Dialog „Wahlschalter", ein Klick auf das Korrekturfeld öffnet einen Zahlen-Dialog. Die App trägt den Wert ein und bestätigt mit OK.
- **Bereitstellen:** Ein kleiner Webserver (Port 8099) liefert die Werte als JSON und nimmt Befehle an. Home Assistant fragt ihn über `rest`-Sensoren ab und ruft ihn über `rest_command` auf.

```
Home Assistant  ──REST──►  App (Port 8099)  ──Chromium──►  SIOCS-Webportal  ──►  Anlage
```

## Einrichtung

1. Repository `https://github.com/friedlro/ha-siocs-heizung` als App-Quelle hinzufügen und die App installieren (Einstellungen → Apps → App-Store → ⋮ → Repositories).
2. Reiter **Konfiguration**: `url`, `username`, `password` eintragen, speichern.
3. App **starten**. Im **Protokoll** darf kein „login fehler" oder „nach login:" stehen. Nach etwa einer Minute liefert `/state` Werte.
4. Den Hostnamen der App unter **Info** ablesen (z. B. `55ec2b33-siocs-heizung`).
5. Den Inhalt von `ha_configuration_snippet.yaml` in die `configuration.yaml` einfügen und `local-siocs-heizung` an **drei Stellen** durch den Hostnamen ersetzen.
6. Unter Entwicklerwerkzeuge → YAML „Konfiguration prüfen", danach neu starten.
7. Optional das Dashboard aus `dashboard_heizung.json` übernehmen: neues Dashboard anlegen → ⋮ → Raw-Konfigurationseditor → Inhalt einfügen.

Updates: Der App-Store zeigt neue Versionen an, die Optionen bleiben beim Update erhalten.

## Optionen

| Option | Typ | Standard | Hinweis |
|---|---|---|---|
| `url` | Text | leer | Adresse des Portals mit `https://`, Pflicht |
| `username` | Text | leer | Pflicht |
| `password` | Passwort | leer | Pflicht |
| `poll_seconds` | Zahl | 60 | 30 bis 3600 Sekunden |

Fehlt `url`, `username` oder `password`, beendet sich die App mit der Meldung „Bitte '…' in den App-Optionen eintragen".

## REST-Schnittstelle der App

Nur intern erreichbar: `http://<hostname>:8099`. Der Port ist nicht nach außen freigegeben.

### `GET /state`

Liefert den letzten Stand als JSON.

| Feld | Bedeutung |
|---|---|
| `ok` | `true`, wenn die letzte Auslese gelungen ist |
| `updated` | Zeitpunkt der letzten Auslese (Containerzeit) |
| `room_temp` | Raumtemperatur (°C) |
| `room_setpoint` | Raumsoll (°C) |
| `offset` | Korrektur (K) |
| `outdoor_avg_control` | Außentemperatur gemittelt „für Regelung" (°C) |
| `outdoor_avg_shutdown` | Außentemperatur gemittelt „für Abschaltung" (°C) |
| `power_kw` | Leistung (kW) |
| `spread_k` | Spreizung (K) |
| `energy_kwh` | Wärmemenge (kWh) |
| `volume_m3` | Volumen (m³) |
| `mode_status` | angezeigter Betriebszustand, z. B. „Aus/FS" |
| `mode_selected` | gewählte Betriebsart (`auto`, `off`, …) |
| `schedule` | Heizzeiten des ersten belegten Heizkreises: Tag → Liste von [von, bis] |
| `schedule_all` | Heizzeiten aller belegten Heizkreise |
| `schedule_circuit` | Name des Heizkreises, z. B. „HK0 - Basis B" |
| `schedule_updated` | Zeitpunkt der letzten Heizzeiten-Auslese |

### `POST /mode`

Körper: `{"mode": "auto"}`. Erlaubt: `auto`, `off`, `setback`, `heat`, `schedule`, `party`. Antwort sofort: `{"accepted": true, "mode": "auto"}`. Das Setzen im Portal läuft im Hintergrund.

### `POST /offset`

Körper: `{"value": 0.5}` (−5 bis +5, eine Nachkommastelle). Antwort sofort: `{"accepted": true, "value": 0.5}`.

Schnelle Folgeaufrufe werden zusammengefasst: Es wird jeweils nur der **neueste** Wunsch pro Art umgesetzt. Dadurch blockiert wiederholtes Klicken in HA nicht.

### `GET /debug`

Zeigt URL, Titel, den sichtbaren Seitentext (die ersten 1500 Zeichen) und eine Liste der sichtbaren Eingabefelder und Schaltflächen. Gedacht für die Fehlersuche, enthält keine Zugangsdaten.

## Entitäten und Konfiguration in Home Assistant

`ha_configuration_snippet.yaml` legt an:

- **Sensoren** (über `rest:`): Raumtemperatur, Raumsoll, Korrektur, Außentemperatur, Leistung, Spreizung, Wärmemenge, Volumen, Status, gewählte Betriebsart, Heizzeiten.
- **`rest_command`:** `siocs_set_mode` und `siocs_set_offset`.
- **`select.heizung_betriebsart`** und **`number.heizung_korrektur_einstellen`** (Vorlagen-Entitäten, die die `rest_command`-Dienste aufrufen und danach den Sensor aktualisieren).

Typische Stolperfallen:

- `options:` der Auswahl muss ein **Vorlagentext** sein (`"{{ ['auto', 'off', …] }}"`). Ein nacktes `off` liest YAML als `false`.
- Der Hostname gehört an **alle drei** Stellen (Sensoren, `siocs_set_mode`, `siocs_set_offset`).
- Die Sensoren heißen nach ihrem Namen, z. B. `sensor.heizung_raumtemperatur`. Änderst du die Namen im Snippet, ändern sich die Entitäts-IDs und das Dashboard muss angepasst werden.

## Betriebsarten und Korrektur

| Wert | Eintrag im Portal | Wirkung |
|---|---|---|
| `auto` | Wahlschalter (Automatik) | Normalbetrieb nach Zeitprogramm und Außentemperatur |
| `off` | MANUELL-AUS/FS | Heizung aus, Frostschutz |
| `setback` | MANUELL-Absenkbetrieb | dauerhaft abgesenkt (Raumsoll sinkt) |
| `heat` | MANUELL-Heizbetrieb | dauerhaft Tagbetrieb |
| `schedule` | MANUELL-Zeitprogramm | Zeitprogramm manuell gewählt |
| `party` | MANUELL-Partymodus | Partybetrieb |

Manuelle Betriebsarten bleiben aktiv, bis du `auto` wählst. Das Portal bietet weitere Handbetriebe (Pumpe/Mischer) an; die App setzt sie nicht.

**Korrektur:** Die Raumtemperatur-Korrektur der Fernbedienung (Anzeige oben im Thermostat). Die App begrenzt sie auf −5 bis +5 K. Sie verschiebt den Raumsoll, bei 22,0 °C Basis und +0,3 K zeigt das Portal 22,3 °C.

## Heizzeiten

Alle 6 Stunden (und nach jedem Start der App) öffnet die App die Seite „HEIZZEITEN", liest den Wochenplan und kehrt zur Stationsseite zurück. Je Heizkreis gibt es 7 Tage mit bis zu 3 Zeiträumen. Ein Zeitraum mit gleicher Von- und Bis-Zeit (z. B. 12:00–12:00) ist **nicht belegt**.

In HA zeigt `sensor.heizung_heizzeiten` die heute geltende Zeit; im Attribut `schedule` steht die ganze Woche. Die Heizzeiten lassen sich **nicht** aus HA ändern.

## Zeitverhalten

| Vorgang | Takt |
|---|---|
| Messwerte lesen | `poll_seconds` (Standard 60 s) |
| Gewählte Betriebsart lesen (Dialog öffnen und abbrechen) | alle 15 Minuten |
| Heizzeiten lesen | alle 6 Stunden |
| Neu anmelden | spätestens alle 30 Minuten und bei Fehlern |
| Anzeige im Portal nach einem Befehl | 10–30 Sekunden |

## Fehlersuche

Protokoll: Einstellungen → Apps → SIOCS Heizung → Protokoll.

| Meldung | Ursache und Abhilfe |
|---|---|
| `Bitte 'url' in den App-Optionen eintragen` | Pflichtoption leer. Konfiguration ausfüllen. |
| `login fehler: … wait_for_function … Timeout` und `nach login: … Anmeldung …` | Das Portal zeigt nach dem Login wieder das Formular. Zugangsdaten prüfen (Passwort-Manager des Browsers füllt manchmal Fremdes ein), Anmeldung im privaten Fenster testen. |
| `nach login:` mit anderem Seitentext | Nach dem Login liegt die Station nicht auf der Startseite. Mit `/debug` den Text ansehen. |
| `auslese unvollstaendig: {…}` | Werte nicht gefunden. Portalseite noch im Aufbau, oder das Layout weicht ab. Siehe „Eigenes Portal anpassen". |
| `setzen fehlgeschlagen (mode=…, Versuch n)` | Der Dialog öffnete sich nicht. Die App wiederholt dreimal und meldet sich zwischendurch neu an. |
| `modus lesen fehlgeschlagen` | Nur der 15-Minuten-Abgleich der gewählten Betriebsart ist gescheitert, Messwerte und Steuerung laufen weiter. |
| `heizzeiten lesen fehlgeschlagen` | Die Heizzeiten-Seite ließ sich nicht öffnen. Beim nächsten Takt neuer Versuch. |
| `ERR_NETWORK_CHANGED` / `chrome-error://chromewebdata` | Kurzer Netzwerkwechsel, meist beim Start. Löst sich selbst. |
| HA-Meldung `set_value: Already running` | Alte App-Version (vor 0.1.10) blockierte beim schnellen Klicken. App aktualisieren. |
| `select.heizung_betriebsart` fehlt | `options:` im Snippet nicht als Vorlagentext angegeben, siehe oben. |

Checkliste: `/state` zeigt `ok: true`? Hat der Hostname im Snippet gestimmt? Ist die Konfiguration geprüft und neu gestartet?

## Eigenes Portal anpassen

Andere Portale oder Stationen können abweichen. Die Anpassung liegt in `siocs_heizung/run.py`:

- **`LABELS`:** Zuordnung „Beschriftung im Portal → Feldname". Der Wert wird in derselben Zeile (Toleranz 6 px) gesucht.
- **`EXTRACT_JS`:** Findet Raumtemperatur, Korrektur und Statuswort relativ zur Beschriftung „Raumsoll.:". Das Statuswort muss zu `STATUS` (Liste bekannter Anzeigewörter) passen.
- **`MODES`:** Zuordnung Betriebsart → Wert im Dialog „Wahlschalter".
- **`SCHEDULE_JS`:** Liest die Seite HEIZZEITEN (Heizkreis-Beschriftung `HKn …`, Zeiten im Format `hh:mm`).
- Der Browser nutzt ein **Fenster von 731 × 698 Pixel**, weil das Layout und die Position der Elemente davon abhängen.

Zur Analyse hilft `/debug` und das Protokoll. Das Portal im eigenen Browser öffnen (F12 → Elemente) zeigt, welche Beschriftungen sichtbar sind.

## Sicherheit und Datenschutz

- Zugangsdaten stehen in den App-Optionen und sind für HA-Administratoren sichtbar, auch über die Supervisor-Schnittstelle. Nutze, wenn möglich, einen eigenen Portal-Benutzer.
- Die App hält die Sitzung nur im Arbeitsspeicher des Containers, es wird nichts auf Datenträger gespeichert.
- Die REST-Schnittstelle hat **keine Anmeldung**. Sie ist nur im internen Netz der Apps erreichbar. Gib den Port nicht ohne Schutz nach außen frei.
- Ändere das Portal-Passwort, wenn es versehentlich weitergegeben wurde (Chat, Protokoll, Screenshot), und trage das neue in den App-Optionen ein.
- Automatisierter Zugriff auf das Portal kann gegen die Nutzungsbedingungen des Betreibers verstoßen. Prüfe das vorab.

## Bekannte Grenzen

- Nur an einer Anlage entwickelt und getestet (Regler MR-12, Heizkreis HK0). Mehrere Heizkreise werden ausgelesen, gesteuert wird nur der auf der Stationsseite sichtbare.
- `off` und `schedule` wurden nicht ausprobiert.
- Das Portal braucht einige Sekunden für Änderungen; Sensoren zeigen den neuen Wert erst bei der nächsten Abfrage.
- Ein geänderter Portal-Aufbau (Update des Betreibers) kann die Auslese stören.
- Keine Lizenz festgelegt.
