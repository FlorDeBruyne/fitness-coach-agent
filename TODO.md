# TODO

## In progress — weer/temperatuur-bewustzijn
- [x] Locatie-opslag: `latitude`/`longitude` op `User` + `/location`-Telegram-flow (native "deel locatie"-knop)
- [ ] Migratie 006 (`add_user_location`) toepassen op de cluster-database — nog uit te zoeken hoe migraties hier normaal gezien uitgevoerd worden (niet meer geweten, geen job/documentatie teruggevonden)
- [ ] Weather-client bouwen (voorstel: Open-Meteo, gratis, geen API-key) — `src/weather/` naar analogie van `src/health/`
- [ ] Data-subset bevestigen: huidige temperatuur + "voelt als", neerslagkans, windsnelheid, min/max van vandaag
- [ ] Context-integratie in `llm.py`: altijd meegeven (zoals `date`/`time`), met een korte cache (~15-30 min per locatie) i.p.v. tool-calling — bewuste keuze gezien lokale modellen onbetrouwbaar zijn in zelf beslissen wanneer een tool aan te roepen
- [ ] Foutafhandeling: bij falende weer-API gewoon het veld weglaten, coach-response niet laten crashen
- [ ] Prompt (`fitness_coach_nl.md`) bijwerken met het nieuwe weerveld

## Kleine openstaande fixes
- [ ] Toon-afwijking: af en toe een formele afsluiter ("Groet, Je persoonlijke fitnescoach") i.p.v. appje-stijl — op te lossen met few-shot voorbeelden in de prompt

## Grotere roadmap-items
- [ ] Plan management (volgende fase volgens de originele roadmap: Level 1 → memory → plan management)
- [ ] Maaltijden-logging
- [ ] Google Calendar-koppeling
- [ ] Model-experimenten (qwen2.5:7b, aya:8b, quantized varianten) — geblokkeerd door NVIDIA driver/library-mismatch op laptop02

## Afgerond deze sessie (ter referentie)
- [x] Hallucinatie-bug gefixed (model verzon slaap/herstel-cijfers uit het prompt-voorbeeld)
- [x] Memory write-path (LLM-extractie → Qdrant, vaste categorieën)
- [x] Memory read-path (RAG-style search, altijd meegegeven in context)
- [x] `logging.basicConfig()` in alle 3 processen (`main.py`, `bot.py`, `agent.py`)
- [x] Datum + tijdstip altijd in coaching-context, niet enkel bij scenario's
- [x] Korte-termijn gespreksgeschiedenis (laatste 5 beurten, in-memory per chat)
