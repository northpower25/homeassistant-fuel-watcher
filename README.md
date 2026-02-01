# Fuel Watcher – Home Assistant Integration

Fuel Watcher ist eine vollständig GPS‑basierte Tankstrategie‑Integration für Home Assistant.  
Die Integration kombiniert:

- Live‑Kraftstoffpreise (Tankerkoenig API)
- Fahrzeugdaten (Tankfüllstand, Reichweite, Verbrauch, Odometer)
- Standortdaten (HA‑Device Tracker)
- Intelligente Entscheidungslogik („Jetzt tanken?“)
- Telegram‑Benachrichtigungen
- Diagnose‑ und Health‑Sensoren

Die Integration ist vollständig PLZ‑frei und arbeitet ausschließlich mit GPS‑Koordinaten.

---

## 🚀 Features

### 🔍 Preis- & Standortanalyse
- Live‑Preis der günstigsten Tankstelle im Radius
- Entfernung zur Tankstelle
- Tankstellenname & Standort
- Kraftstofftyp (E5, E10, Diesel, LPG, CNG, Super+)

### 🚗 Fahrzeugdaten
- Reichweite (km)
- Tankfüllstand (%)
- Verbrauch (l/100km)
- Odometer (km)

### 🧠 Tankstrategie
- Entscheidung: *Jetzt tanken?*
- Begründung: *Warum?*
- Preis‑ und Distanzschwellen
- Health‑Score & Fehlerdiagnose

### 📡 Telegram Alerts
- Push‑Benachrichtigungen bei günstigen Preisen
- Benachrichtigungen bei niedriger Reichweite
- Debug‑Nachrichten

---

## 🛠 Installation

### Via HACS (empfohlen)
1. HACS → Integrationen → Benutzerdefinierte Repositories  
2. Repository hinzufügen:  
   `https://github.com/northpower25/homeassistant-fuel-watcher`
3. Kategorie: **Integration**
4. Installieren
5. Home Assistant neu starten

### Manuell
1. Ordner `custom_components/fuel_watcher` in dein HA‑Config‑Verzeichnis kopieren
2. Home Assistant neu starten

---

## ⚙️ Einrichtung

1. Home Assistant → Einstellungen → Geräte & Dienste  
2. „Integration hinzufügen“ → **Fuel Watcher**
3. Folgende Daten eingeben:
   - Tankerkoenig API Key
   - Telegram Bot Token
   - Telegram Chat ID
   - Radius (km)
   - Kraftstofftyp
   - Preis‑Schwelle
   - Distanz‑Schwelle
   - Fahrzeug‑Entitäten (optional)

Nach Abschluss wird ein Config Entry erzeugt und alle Sensoren automatisch geladen.

---

## 📡 Sensoren

### Hauptsensor
| Sensor | Beschreibung |
|--------|--------------|
| `sensor.fuel_watcher` | Hauptsensor mit Preis als State + alle Rohattribute |

### Derived Sensoren (empfohlen)
| Sensor | Beschreibung |
|--------|--------------|
| `sensor.fuel_watcher_price` | Preis in €/l |
| `sensor.fuel_watcher_station_name` | Name der Tankstelle |
| `sensor.fuel_watcher_distance` | Entfernung in km |
| `sensor.fuel_watcher_range` | Reichweite in km |
| `sensor.fuel_watcher_fuel_level` | Tankfüllstand in % |
| `sensor.fuel_watcher_consumption` | Verbrauch l/100km |
| `sensor.fuel_watcher_odometer` | Kilometerstand |
| `sensor.fuel_watcher_strategy_decision` | Entscheidung |
| `sensor.fuel_watcher_strategy_reason` | Begründung |
| `sensor.fuel_watcher_health_score` | Health Score |
| `sensor.fuel_watcher_last_error` | Letzter Fehler |

---

## 🧪 Diagnose

Die Integration erzeugt zusätzliche Diagnose‑Sensoren:

- `sensor.fuel_watcher_health_score`
- `sensor.fuel_watcher_last_error`

---

## 📊 Beispiel Dashboard

Ein vollständiges Dashboard findest du weiter unten.

---

## 📨 Telegram Benachrichtigungen

Die Integration sendet Nachrichten bei:

- Preis unter Schwelle
- Reichweite unter Schwelle
- Fehlern
- Debug‑Events (optional)

---

## 🧩 Roadmap

- Mehr Datenquellen (z. B. Spritpreis API EU)
- Multi‑Vehicle Support
- Automatische Tankempfehlungen
- Kartenansicht mit Tankstellen
- HACS Dashboard‑Installer

---

## 🧑‍💻 Entwickler

- Autor: Daniel (northpower25)
- Mit Unterstützung von Microsoft Copilot

Pull Requests sind willkommen!
