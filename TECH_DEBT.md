# Technical Debt

Bekende bugs en inconsistenties die (nog) niet urgent zijn omdat het huidige gebruikspad ze niet raakt, maar wel opgelost moeten worden voor het systeem robuust is.

---

## 1. `open_wearables_user_id` fallback in `agent.py` geeft verkeerd type terug

**Locatie:** `src/coaching/agent.py`, functie `morning_update()`

```python
open_wearables_id = user.open_wearables_user_id if user.open_wearables_user_id else await get_open_wearables_user_id(user.firstname, user.lastname)
health_client = HealthClient(open_wearables_id)
```

**Probleem:** `get_open_wearables_user_id()` (in `src/health/client.py`) geeft het volledige user-dict terug (`{"id": ..., "first_name": ..., ...}`), niet enkel de id-string. `HealthClient.__init__` verwacht een string als `user_id`. Als deze fallback ooit wordt geraakt (bv. een user met `open_wearables_user_id = None` in de database), krijgt `HealthClient` een dict in plaats van een string, wat requests naar de Open Wearables API stil laat falen of corrumperen.

**Waarom het nu niet opvalt:** `user.open_wearables_user_id` wordt tijdens onboarding al correct gezet via `.get("id", "")` (zie `src/users/onboarding.py`), dus de fallback-tak wordt in de praktijk nooit uitgevoerd.

**Fix:** de fallback-regel aanpassen naar:
```python
open_wearables_id = user.open_wearables_user_id if user.open_wearables_user_id else (await get_open_wearables_user_id(user.firstname, user.lastname) or {}).get("id", "")
```

---

## 2. `evening_update()` mist de fallback die `morning_update()` wel heeft

**Locatie:** `src/coaching/agent.py`, functie `evening_update()`

```python
health_client = HealthClient(user.open_wearables_user_id)
```

**Probleem:** geen fallback naar `get_open_wearables_user_id()` als `user.open_wearables_user_id` `None` is. Inconsistent met `morning_update()`, en faalt op een andere (minder nette) manier als het veld leeg is.

**Fix:** zodra bug #1 is opgelost, dezelfde fallback-logica toepassen in `evening_update()` als in `morning_update()`.

---

## Prioriteit

Laag — beide paden worden vandaag niet geraakt omdat onboarding de `open_wearables_user_id` altijd correct zet. Wel oppakken zodra er robuustheid/error-handling wordt toegevoegd, of als er ooit users in de database komen te staan zonder geldige Open Wearables match.