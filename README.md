# Fuel Watcher – Intelligente Tank‑Assistenz für Home Assistant 🚗⛽

Fuel Watcher ist eine selbstlernende Tank‑ und Preis‑Assistenz für Home Assistant.  
Die Integration kombiniert Fahrzeugdaten, Preisabfragen, Verbrauchsstatistiken und Telegram‑Benachrichtigungen zu einer echten „Tank‑KI“.

---

## ✨ Features

### 🔍 Preisabfrage (Tankerkoenig)
- Automatische Abfrage der günstigsten Tankstelle in der Nähe
- Preis, Entfernung, Adresse, Koordinaten
- Navigation per Klick (Google Maps / Apple Maps / Waze)

### 🧠 Selbstlernende Verbrauchsstatistik
Fuel Watcher analysiert automatisch:
- Odometer‑Verlauf
- Tageskilometer
- Wochentags‑Durchschnitt
- Reichweite in Tagen

→ Die Prognosen werden mit der Zeit immer genauer.

### ⛽ Tankhistorie
Tankvorgänge können erfasst werden:
- über die Options‑Maske  
- oder per Telegram‑Antwort (z. B. „42.5L @ 1.72“)

Fuel Watcher speichert:
- Liter
- Preis pro Liter
- Gesamtkosten
- Tankstelle
- Odometer

### 💬 Telegram‑Benachrichtigungen (Markdown + Emojis)
Benachrichtigungen bei:
- Tankempfehlung
- Preis‑Delta (absolut/prozentual)
- Preis‑Spike
- Reichweite in km
- Reichweite in Tagen
- Tankstellenwechsel
- API‑Fehler

Alle Texte sind parametrierbar.

### 🧪 Testfunktion
Im Options‑Flow:
**„Testnachricht senden“**

### 📊 Sensoren
- `sensor.fuel_watcher`
- `sensor.fuel_watcher_price`
- `sensor.fuel_watcher_station`
- `sensor.fuel_watcher_distance_km`
- `sensor.fuel_watcher_range_km`
- `sensor.fuel_watcher_days_left`
- `sensor.fuel_watcher_price_delta`
- `sensor.fuel_watcher_price_delta_percent`
- uvm.

---

## 🛠 Installation

### HACS (empfohlen)
1. HACS → Integrationen → Benutzerdefinierte Repositories  
2. Repository hinzufügen:  
   `https://github.com/<dein-repo>/fuel_watcher`
3. Integration installieren  
4. Home Assistant neu starten  
5. Fuel Watcher hinzufügen

### Manuell
1. Ordner `custom_components/fuel_watcher` in HA kopieren  
2. Home Assistant neu starten  
3. Integration hinzufügen

---

## ⚙️ Konfiguration

### Benötigte Daten
- Tankerkoenig API‑Key  
- Telegram Bot Token  
- Telegram Chat ID  
- Fahrzeug‑Entitäten:
  - Reichweite (km)
  - Odometer
  - Verbrauch (optional)
  - Tankfüllstand (optional)
  - GPS‑Position

### Optionale Einstellungen
- Preis‑Schwellen
- Preis‑Delta (absolut/prozentual)
- Benachrichtigungs‑Trigger
- Nachrichtentexte
- Tankhistorie erfassen
- Testnachricht senden

Alle Felder haben Tooltips, die erklären, was benötigt wird.

---

## 📁 Datenhaltung

Fuel Watcher speichert Daten in:
