# fitness nation | Studio Walk

Vierte Katalog-Ansicht — **komplett eigenständiges Konzept** (kein Umbau):
Der Katalog ist ein **begehbarer Studio-Rundgang**. Man scrollt und läuft
horizontal durch die Zonen (Eingang → Check-in → Fläche → Messraum → Lounge → Corporate).
Produkte stehen dort, wo sie im echten Studio stehen: Rotations-Clips drehen sich,
wenn man die Zone betritt, Software schwebt als Phones daneben — und an JEDEM Produkt
hängt ein **Preisschild** (Klick = volles Datenblatt als Schublade). Am Ende des
Rundgangs: die komplette Preisliste + Kontakt.

- Desktop: horizontaler Walk (Scroll→X), Zonen-Karte unten, Pfeiltasten springen Zonen
- Mobil & reduced-motion: Zonen gestapelt, Videos spielen im Sichtfeld
- Präsentationsmodus: Taste **F** (Zone = Folie, `.` = Blackout)
- Preise live aus dem Brain beim Build; Inhalte = dieselben content-JSONs

## Betrieb
`python3 build/build.py` → `site/de|en(+/smart)` · Deploy: push → Vercel (Output `site`)
