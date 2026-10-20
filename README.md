# Müll-Erinnerung für Home Assistant

Eine HACS-kompatible Custom Integration für Müllabholungs-Erinnerungen mit konfigurierbaren Sensoren, einer Lovelace-Karte, Schlummern, Erledigt-Datum und optionalen Companion-App-Benachrichtigungen.

> **Status:** erster funktionsfähiger Projektstand zur Erprobung. Vor produktivem Einsatz auf einer Testinstanz prüfen. Die Integration und die Lovelace-Karte sind in diesem Repository enthalten; Bubble Card ist nicht erforderlich.

## Funktionen

- Beliebig viele konfigurierbare Müllarten/Sensoren.
- Sensorattribut standardmäßig `anzahl_tage`, erwarteter Wert standardmäßig `1`.
- Erinnerung täglich zur konfigurierbaren Uhrzeit (Standard 19:00), sofern Abholung morgen ansteht.
- „Später“ schließt die Erinnerung und zeigt sie nach konfigurierbaren Minuten erneut.
- „Erledigt“ speichert nur das zuletzt erledigte Datum und unterdrückt weitere Erinnerungen an diesem lokalen Datum.
- Optionale Home Assistant Companion-App-Benachrichtigung an ein konfiguriertes `notify.*`-Ziel.
- Eigene Lovelace-Karte mit den Buttons „Später“ und „Erledigt“.
- HACS-Download und manuelle Installation.

## Installation über HACS (als benutzerdefiniertes Repository)

1. Lade dieses Repository in ein eigenes GitHub-Repository hoch.
2. In HACS → Integrationen → ⋮ → **Benutzerdefinierte Repositories** das Repository als **Integration** hinzufügen.
3. Installation starten und Home Assistant neu starten.
4. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Müll-Erinnerung**.
5. Den Sensoren Namen, Entity-ID, Attribut und den Zielwert zuweisen. Mehrere Müllarten können hinzugefügt werden.
6. Dashboard-Ressource einbinden (siehe unten).

### Dashboard-Ressource

Nach der Installation liegt die JS-Datei unter:
`/hacsfiles/muell-erinnerung/muell-erinnerung.js`

Dashboard → Einstellungen → Dashboards → Ressourcen → Ressource hinzufügen:
- URL: `/hacsfiles/muell-erinnerung/muell-erinnerung.js`
- Typ: JavaScript-Modul

Danach im Dashboard eine manuelle Karte aus `examples/lovelace-card.yaml` hinzufügen. Nach Änderungen an der JS-Datei ggf. Browser-Cache neu laden.

## Companion-App-Benachrichtigungen

In der Integration optional ein `notify`-Ziel auswählen/eintragen, z. B. `notify.mobile_app_dein_iphone`. Der Name hängt von deiner Home Assistant Companion App ab. Lege die Aktion in der App einmalig an, damit die `notify.mobile_app_*`-Entität existiert.

Die Benachrichtigung enthält Müllarten und eine Aktions-URL zum Dashboard. Die interaktiven Buttons der persistenten Lovelace-Karte sind die primäre Bedienoberfläche. Mobile-Aktionsbuttons werden in diesem ersten Stand nicht als bidirektionale Aktionen ausgewertet; nutze für „Später“/„Erledigt“ die Karte.

## Konfiguration und Bedienung

Die Integration legt folgende Entitäten an:
- `sensor.muell_erinnerung_naechste_abholung` – Liste der Müllarten, die morgen raus müssen.
- `binary_sensor.muell_erinnerung_aktiv` – Erinnerung ist relevant und noch nicht erledigt.
- `button.muell_erinnerung_spaeter` – Schlummern.
- `button.muell_erinnerung_erledigt` – Erledigt.
- `button.muell_erinnerung_testbenachrichtigung` – Testbenachrichtigung.

Die tatsächlichen Entity-IDs können bei Namenskonflikten von Home Assistant angepasst werden.

## Sensorformat

Standardmäßig wird das Attribut `anzahl_tage` ausgewertet. Beispiel:
```yaml
sensor.nachster_papier:
  anzahl_tage: 1
```
Die Zustände selbst werden nicht verwendet. Jeder Eintrag hat eine frei definierbare Bezeichnung und kann ein eigenes Attribut und einen eigenen Vergleichswert verwenden.

## Entwicklung

Python-Code ist für moderne Home Assistant-Versionen geschrieben. Für Änderungen lokal testen und `manifest.json`-Version erhöhen. Pull Requests sind willkommen.

## Lizenz

MIT
