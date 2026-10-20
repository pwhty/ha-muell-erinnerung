# Müll-Erinnerung für Home Assistant

Eine HACS-kompatible Custom Integration für Müllabholungs-Erinnerungen mit konfigurierbaren Sensoren, einer Lovelace-Karte, Schlummern, Erledigt-Datum und optionalen Companion-App-Benachrichtigungen.

> **Status:** erster funktionsfähiger Projektstand zur Erprobung. Vor produktivem Einsatz auf einer Testinstanz prüfen. Die Integration und eine eigene Lovelace-Karte sind enthalten; alternativ gibt es ein Bubble-Card-Pop-up als Beispiel.

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
5. Die Müllarten als YAML-Liste angeben (`label`, `entity_id`, optional `attribute` und `value`). Später änderbar über **Konfigurieren**.
6. Karte ins Dashboard einfügen (siehe unten).

### Dashboard-Karten

Die Integration liefert ihre eigene Karte `custom:muell-erinnerung-card` selbst aus und lädt sie automatisch im Frontend. Du musst also **keine Ressource** manuell hinzufügen. Die Karte erscheint in der Kartenauswahl als „Müll-Erinnerung“. Nach einem Update ggf. den Browser-Cache leeren.

Beispiele im Ordner [`examples/`](examples/):
- [`lovelace-card.yaml`](examples/lovelace-card.yaml): eigene Karte der Integration.
- [`bubble-card-popup.yaml`](examples/bubble-card-popup.yaml): Bubble Card Pop-up, das sich automatisch öffnet und nach „Später“/„Erledigt“ wieder schließt (benötigt [Bubble Card](https://github.com/Clooos/Bubble-Card) ≥ 3.0).

Der Ordner `examples/` wird von HACS **nicht** nach Home Assistant kopiert (HACS installiert nur `custom_components/muell_erinnerung`). Den YAML-Inhalt kopierst du von GitHub und fügst ihn unter Dashboard bearbeiten → Karte hinzufügen → **Manuell** ein.

## Companion-App-Benachrichtigungen

In der Integration optional ein `notify`-Ziel auswählen/eintragen, z. B. `notify.mobile_app_dein_iphone`. Der Name hängt von deiner Home Assistant Companion App ab. Lege die Aktion in der App einmalig an, damit die `notify.mobile_app_*`-Entität existiert.

Die Benachrichtigung enthält Müllarten und eine Aktions-URL zum Dashboard. Die interaktiven Buttons der persistenten Lovelace-Karte sind die primäre Bedienoberfläche. Mobile-Aktionsbuttons werden in diesem ersten Stand nicht als bidirektionale Aktionen ausgewertet; nutze für „Später“/„Erledigt“ die Karte.

## Konfiguration und Bedienung

Die Integration legt ein Gerät „Müllerinnerung“ mit folgenden Entitäten an:
- `sensor.muellerinnerung_naechste_abholung`: Müllarten, die morgen abgeholt werden (Attribute: `muellarten`, `popup_aktiv`, `erledigt_am`, `schlummer_bis`).
- `binary_sensor.muellerinnerung_aktiv`: `on`, sobald die Erinnerungszeit erreicht ist, morgen etwas abgeholt wird und weder geschlummert noch erledigt wurde. Dient als Trigger für das Pop-up.
- `button.muellerinnerung_spaeter`: Schlummern.
- `button.muellerinnerung_erledigt`: Erledigt.
- `button.muellerinnerung_testbenachrichtigung`: Testbenachrichtigung.

Bei einem Update von 0.1.x werden bestehende Entitäten (z. B. `binary_sensor.erinnerung_aktiv`) automatisch auf die neuen IDs umbenannt. Automationen und Karten, die noch die alten IDs verwenden, musst du anpassen.

## Sensorformat

Standardmäßig wird das Attribut `anzahl_tage` ausgewertet. Beispiel:
```yaml
sensor.nachster_papier:
  anzahl_tage: 1
```
Soll stattdessen der Zustand der Entität verglichen werden, `attribute` leer lassen oder auf `state` setzen. Jeder Eintrag hat eine frei definierbare Bezeichnung und kann ein eigenes Attribut und einen eigenen Vergleichswert verwenden.

## Entwicklung

Python-Code ist für moderne Home Assistant-Versionen geschrieben. Für Änderungen lokal testen und `manifest.json`-Version erhöhen. Pull Requests sind willkommen.

## Lizenz

MIT
