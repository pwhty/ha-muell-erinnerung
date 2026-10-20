# Müll-Erinnerung für Home Assistant

Eine HACS-kompatible Custom Integration, die Abholtermine aus einem Abfallkalender liest, je Mülltyp einen Sensor bereitstellt und am Vorabend per Pop-up (und optional per Push) ans Rausstellen erinnert, mit „Später“ und „Erledigt“.

> **Status:** Projektstand zur Erprobung. Vor produktivem Einsatz auf einer Testinstanz prüfen. Benötigt Home Assistant ≥ 2025.4.

## Funktionen

- Liest Termine aus einer beliebigen `calendar.*`-Entität (z. B. ICS-/CalDAV-Abfallkalender).
- Mülltypen werden in der Oberfläche angelegt: Name + Suchmuster für den Termintitel. Je Mülltyp entsteht automatisch ein Sensor mit Tagen bis zur Abholung und einem Anzeigetext.
- Erinnerung täglich zur konfigurierbaren Uhrzeit (Standard 19:00), sofern morgen etwas abgeholt wird.
- „Später“ schließt die Erinnerung und zeigt sie nach konfigurierbaren Minuten erneut.
- „Erledigt“ unterdrückt weitere Erinnerungen an diesem Tag (übersteht Neustarts).
- Optionale Companion-App-Benachrichtigung an ein `notify.*`-Ziel.
- Eigene Lovelace-Karte, die automatisch geladen wird; Beispiele für Bubble Card.

## Installation über HACS (als benutzerdefiniertes Repository)

1. In HACS → ⋮ → **Benutzerdefinierte Repositories** dieses Repository als **Integration** hinzufügen.
2. Installieren und Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Müll-Erinnerung**.
4. Abfallkalender auswählen. Optional die Standard-Mülltypen (Biomüll, Restmüll, Papiermüll, Gelber Sack) anlegen lassen.
5. Karten ins Dashboard einfügen (siehe unten).

## Mülltypen

Unter Einstellungen → Geräte & Dienste → Müll-Erinnerung gibt es den Button **Mülltyp hinzufügen**. Jeder Mülltyp hat:

- **Name**, z. B. `Biomüll`. Daraus entsteht die Entity-ID `sensor.muellerinnerung_biomuell` (Umlaute werden zu ae/oe/ue).
- **Suchmuster**: regulärer Ausdruck, der im Termintitel gesucht wird, ohne Groß-/Kleinschreibung. Alternativen mit `|` trennen, z. B. `restmüll|restmuell|restabfall`. Im Dialog werden die im Kalender gefundenen Termintitel als Hilfe angezeigt.
- **Icon** (optional).

Bestehende Mülltypen lassen sich über das Stift-Symbol bearbeiten oder löschen; die Integration lädt danach automatisch neu.

Standard-Mülltypen:

| Name | Suchmuster |
|---|---|
| Biomüll | `bio` |
| Restmüll | `restmüll\|restmuell\|restabfall` |
| Papiermüll | `altpapier` |
| Gelber Sack | `gelb` |

## Entitäten

Alle Entitäten gehören zum Gerät „Müllerinnerung“:

| Entität | Beschreibung |
|---|---|
| `sensor.muellerinnerung_<mülltyp>` | Tage bis zur nächsten Abholung. Attribute: `anzahl_tage`, `anzeige` („Heute“, „Morgen“, „In 5 Tagen“, „unbekannt“), `date` (YYYY-MM-DD). |
| `sensor.muellerinnerung_naechste_abholung` | Müllarten, die morgen abgeholt werden. Attribute: `muellarten`, `popup_aktiv`, `erledigt_am`, `schlummer_bis`. |
| `binary_sensor.muellerinnerung_aktiv` | `on`, sobald die Erinnerungszeit erreicht ist, morgen etwas abgeholt wird und weder geschlummert noch erledigt wurde. Trigger für das Pop-up. |
| `button.muellerinnerung_spaeter` | Schlummern. |
| `button.muellerinnerung_erledigt` | Erledigt. |
| `button.muellerinnerung_testbenachrichtigung` | Testbenachrichtigung senden. |

Der Kalender wird beim Start, stündlich und kurz nach Mitternacht neu gelesen.

## Dashboard-Karten

Beispiele im Ordner [`examples/`](examples/):
- [`bubble-card-uebersicht.yaml`](examples/bubble-card-uebersicht.yaml): Bubble-Card-Buttons je Mülltyp mit Anzeigetext.
- [`bubble-card-popup.yaml`](examples/bubble-card-popup.yaml): Bubble-Card-Pop-up, das sich automatisch öffnet und nach „Später“/„Erledigt“ wieder schließt (benötigt [Bubble Card](https://github.com/Clooos/Bubble-Card) ≥ 3.0).
- [`lovelace-card.yaml`](examples/lovelace-card.yaml): eigene Karte der Integration (`custom:muell-erinnerung-card`). Sie wird automatisch geladen, eine Ressource ist nicht nötig, und sie erscheint in der Kartenauswahl als „Müll-Erinnerung“.

Der Ordner `examples/` wird von HACS **nicht** nach Home Assistant kopiert. Den YAML-Inhalt von GitHub kopieren und unter Dashboard bearbeiten → Karte hinzufügen → **Manuell** einfügen.

## Umstieg von Template-Sensoren

Wer die Sensoren bisher per `template:` mit `calendar.get_events` und einem Jinja-Makro berechnet hat, kann diesen Block aus der `configuration.yaml` und das Makro aus `custom_templates/` entfernen. Die Attribute `anzahl_tage`, `anzeige` und `date` heißen gleich, die Entity-IDs ändern sich aber (z. B. `sensor.nachster_biomull` → `sensor.muellerinnerung_biomuell`). Dashboards und Automationen entsprechend anpassen. Unterschied: Wird kein Termin gefunden, ist der Zustand `unknown` statt `-1`.

## Companion-App-Benachrichtigungen

In den Optionen der Integration ein `notify`-Ziel eintragen, z. B. `notify.mobile_app_dein_iphone`. Die Benachrichtigung enthält die Müllarten und einen Link zum konfigurierten Dashboard-Pfad. „Später“ und „Erledigt“ bedienst du über das Pop-up bzw. die Karte.

## Entwicklung

```bash
python3.13 -m venv .venv && .venv/bin/pip install -r requirements_test.txt
.venv/bin/pytest
```

## Lizenz

MIT
