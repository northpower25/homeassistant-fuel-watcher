# Home Assistant Fuel Watcher

**Fuel Watcher** ist eine erweiterte Home‑Assistant‑Integration, die Tankerkoenig‑Preise, Fahrzeugdaten, Standort und historische Fahrprofile kombiniert, um intelligente Tankempfehlungen zu geben.  
Die Integration sendet kontextbasierte Telegram‑Benachrichtigungen und unterstützt mehrere Kraftstoffsorten.

---

## 🚀 Features

- Live‑Preisabfrage über die Tankerkoenig‑API  
- Unterstützung mehrerer Kraftstoffsorten (E5, E10, Diesel, SuperPlus, LPG, CNG)  
- Telegram‑Benachrichtigungen bei Preisfall  
- Preisschwellen & Distanzschwellen  
- Fahrzeugdaten‑Integration:
  - Tankinhalt  
  - Reichweite  
  - Verbrauch  
  - GPS‑Position  
- Historische Verbrauchsanalyse (km/Tag)  
- Strategische Tankempfehlungen:
  - „Jetzt tanken“  
  - „Warten“  
  - „Könnte knapp werden“  
- Berücksichtigung statistisch günstiger Tankzeiten  
- Sensor mit umfangreichen Attributen

---

## 📦 Installation über HACS (Custom Integration)

### Voraussetzungen
- Home Assistant  
- HACS installiert  
- Telegram Bot + Chat ID  
- Tankerkoenig API Key  

### Schritt‑für‑Schritt

1. **Repository hinzufügen**
   - Öffne **HACS → Integrationen**
   - Klicke oben rechts auf **⋮ → Custom repositories**
   - Trage dein Repository ein, z. B.:  
     ```
     https://github.com/northpower25/homeassistant-fuel-watcher-
     ```
   - Kategorie: **Integration**

2. **Integration installieren**
   - Nach dem Hinzufügen erscheint „Fuel Watcher“ in HACS
   - Klicke auf **Installieren**

3. **Home Assistant neu starten**

4. **Integration einrichten**
   - Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**
   - Wähle **Fuel Watcher**
   - Gib folgende Daten ein:
     - Tankerkoenig API Key  
     - Telegram Bot Token  
     - Telegram Chat ID  
     - PLZ  
     - Radius (km)  
     - Kraftstofftyp  
     - Preisschwelle (optional)  
     - Distanzschwelle (optional)  
     - Tankinhalt‑Entität (optional)  
     - Reichweite‑Entität (optional)  
     - Verbrauch‑Entität (optional)  
     - Positionsentität (lat,lon)

---

## 🧩 Sensor

### Attribute:

- `station` – günstigste Tankstelle  
- `fuel` – Kraftstofftyp  
- `distance_km` – Entfernung zur Tankstelle  
- `fuel_level` – Tankinhalt  
- `range_km` – Reichweite  
- `consumption_l_100km` – Verbrauch  
- `strategy_decision` – wait / warning / tank_now  
- `strategy_reason` – Begründung  

---

## 🔔 Benachrichtigungslogik

Eine Telegram‑Nachricht wird gesendet, wenn:

- der Preis gefallen ist  
- UND optional unter der Preisschwelle liegt  
- UND optional innerhalb der Distanzschwelle liegt  

Die Nachricht enthält:

- Preis & Tankstelle  
- Fahrzeugstatus  
- Entfernung  
- Strategische Empfehlung  
- Historische Verbrauchsprognose  

---

## 📊 Historische Verbrauchsanalyse

Fuel Watcher speichert:

- tägliche gefahrene Kilometer  
- geschätzte Reichweitenentwicklung  
- Durchschnitt der letzten 14 Tage  

Diese Daten fließen in die Tankstrategie ein.

---

## 🕒 Statistisch günstige Tankzeiten

Die Integration nutzt interne Heuristiken:

- Abends (18–22 Uhr) günstiger  
- Montag & Dienstag tendenziell am günstigsten  
- Individuelle Zeitfenster pro Wochentag  

Diese werden mit deiner Reichweite und deinem Verbrauch kombiniert.

---

## 📝 Lizenz

MIT

---

## ❤️ Support

Issues & Feature Requests bitte über GitHub einreichen.

Die Integration erstellt:

   custom_components/fuel_watcher/
