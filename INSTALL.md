# SIOCS Heizung in Home Assistant einbinden

1. Dieses Repository in HA als App-Quelle hinzufuegen:
   Einstellungen > Apps > App-Store > oben rechts Menue > Repositories >
   https://github.com/friedlro/ha-siocs-heizung
2. "SIOCS Heizung" installieren.
3. Reiter "Konfiguration": url (Adresse deines SIOCS-Portals, z.B. https://dein-portal.example/),
   Benutzername und Passwort eintragen (nur dort!), speichern, App starten.
   Im Protokoll darf kein "poll fehler" / "login fehler" stehen.
4. ha_configuration_snippet.yaml in die configuration.yaml uebernehmen, HA neu starten.

Betriebsarten: auto, off (Aus/FS), setback (Absenk), heat (Heiz), schedule (Zeitprogramm), party.
Korrektur: -5 bis +5 K (Fernbedienungs-Verstellung am Thermostat).
Hostname der App fuer HA: local-siocs-heizung bei lokaler Installation, bei Repository-Installation
die in den App-Infos angezeigte Adresse (meist xxxxxxxx-siocs-heizung) - im Snippet anpassen.
