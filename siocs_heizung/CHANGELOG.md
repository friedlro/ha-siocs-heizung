# Changelog

## 0.1.15
- Heizzeiten werden alle 6 Stunden aus dem Portal gelesen (Seite HEIZZEITEN) und in /state als schedule bereitgestellt.

## 0.1.14
- Option url hat keinen Standardwert mehr; die App prüft beim Start url, username und password und meldet fehlende Angaben klar.

## 0.1.13
- Timeout beim Lesen der gewählten Betriebsart behoben: längere Wartezeit, ein Fehler dabei stört die Auslese nicht mehr.

## 0.1.12
- Beim Setzen der Betriebsart wird das Statuswort (z. B. „Aus/FS") angeklickt, nicht die „MANUELL-…"-Zeile darüber. Behebt das Zurückstellen auf Automatik.

## 0.1.11
- Alte Markierungen der Bedienelemente werden vor jedem Auslesen entfernt (Fehler „strict mode violation").

## 0.1.10
- Befehle (Betriebsart, Korrektur) werden sofort angenommen und im Hintergrund umgesetzt; es zählt jeweils der neueste Wunsch.
- Bedienelemente werden vor jedem Setzen neu markiert; bis zu drei Versuche mit erneuter Anmeldung.

## 0.1.9
- Auslese relativ zur Beschriftung „Raumsoll.:", mehrere Versuche, falls das Portal noch aufbaut.

## 0.1.8
- Browserfenster 731 × 698 Pixel für ein stabiles Layout.

## 0.1.7
- Login-Felder werden über Feldtyp (Text, Passwort) und Schaltfläche „Anmelden" gefunden.

## 0.1.6
- /debug listet sichtbare Eingabefelder und Schaltflächen.

## 0.1.5
- Login: Eingabe wie ein Mensch tippen.

## 0.1.4
- Nach einem fehlgeschlagenen Login wird der Seitentext protokolliert.

## 0.1.3
- Login: wartet auf das vollständige Laden der Seite und wiederholt den Versuch.

## 0.1.2
- Diagnose-Endpunkt /debug.

## 0.1.1
- Wartet auf ein sichtbares „Raumsoll.:"-Element (versteckte Vorlagen im Portal); die App beendet sich bei einem Netzwerkfehler beim Start nicht mehr.

## 0.1.0
- Erste Version: Messwerte lesen sowie Betriebsart und Korrektur setzen über das SIOCS-Webportal.
