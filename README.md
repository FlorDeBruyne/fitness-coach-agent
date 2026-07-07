# fitness-coach-agent

A personal AI fitness coach for a user, combining Apple Watch health data with a local LLM to send personalized messages via Telegram.

---

## Stack

| Component | Technology                            |
|-----------|---------------------------------------|
| Agent API | Python FastAPI                        |
| LLM | Ollama on laptop02                    |
| Messaging | Telegram Bot (python-telegram-bot)    |
| Health data | Open Wearables API (self-hosted fork) |
| Memory (structured) | PostgreSQL via CNPG operator          |
| Memory (semantic) | Qdrant (planned)                      |
| Deployment | Kubernetes homelab                    |
| GitOps | FluxCD v2                             |
| Secrets | SOPS + Age                            |

---

## Repo Structure

```
fitness-coach-agent/
├── src/
│   ├── main.py                    # FastAPI app
│   ├── coaching/
│   │   ├── __init__.py            
│   │   ├── agent.py               # morning_update() and evening_update() — CronJob entry points
│   │   └── llm.py                 # get_coaching_response(), main()
│   ├── health/
│   │   ├── __init__.py            
│   │   └── client.py              # HealthClient class + get_open_wearables_user_id()
│   ├── messaging/
│   │   ├── __init__.py            
│   │   └── bot.py                 # Telegram bot, ConversationHandler, send_proactive_message()
│   ├── users/
│   │   ├── __init__.py            
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── crud.py                # Database operations
│   │   └── onboarding.py          # check_onboarding(), save_onboarding()
│   └── core/
│       └── config.py
├── alembic/
│   ├── env.py                     # Replaces asyncpg → psycopg2 for Alembic
│   ├── versions/
│   │   ├── 001_initial.py         # users, goals, injuries tables
│   │   ├── 002_update_user_nullable_defaults.py
│   │   └── 003_add_open_wearables_user_id.py
│   └── alembic.ini
├── prompts/
│   ├── fitness_coach_nl.md        # Dutch system prompt
│   └── fitness_coach_en.md        # English system prompt
├── scripts/
│   └── start/
│       ├── app.sh                 # uvicorn src.main:app
│       ├── telegram_bot.sh        # python3 src/messaging/bot.py
│       ├── agent.sh               # python3 src/coaching/agent.py (morning)
│       └── evening_agent.sh       # python3 src/coaching/agent.py (evening)
├── .github/workflows/build.yaml
├── Dockerfile
└── requirements.txt
```

---

## Agent Flow

### Morning message (CronJob 08:00)
```
agent.py morning_update()
    → get_all_onboarded_users()             [database]
    → for each user:
        → HealthClient(user.open_wearables_user_id)
        → health_client.get_morning_context()       [Open Wearables API]
        → llm.main(message, context={user_context, health_context})
        → send_proactive_message(response)          [Telegram]
```

### Evening message (CronJob 22:30)
```
agent.py evening_update()
    → get_all_onboarded_users()             [database]
    → for each user:
        → HealthClient(user.open_wearables_user_id)
        → health_client.get_evening_context()       [Open Wearables API]
        → llm.main(message, context={user_context, health_context})
        → send_proactive_message(response)          [Telegram]
```

### Reactive message (Telegram → bot.py)
```
user sends message
    → send_message() handler
    → get_record_by_telegram(chat_id)       [database]
    → llm.main(message, context={user_context})
    → reply via context.bot.send_message()
```

---

## Database Schema

### users
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| open_wearables_user_id | VARCHAR | Link to Open Wearables |
| firstname / lastname | VARCHAR | Name |
| gender | VARCHAR | Gender |
| age | INTEGER | Age |
| height_cm / weight_kg | FLOAT | Nullable |
| fitness_level | VARCHAR | Inactive / Lightly Active / Moderately Active / Very Active / Athlete |
| telegram_chat_id | VARCHAR | String |
| preferred_language | VARCHAR | Default: nl |
| timezone | VARCHAR | Default: Europe/Brussels |
| onboarding_completed | BOOLEAN | True after completed onboarding |
| created_at / updated_at | DATETIME | Timestamps (naive UTC) |

### goals
Table exists via Alembic, not yet in use.

### injuries
Table exists via Alembic, not yet in use.

---

## Onboarding Flow

```
/start
  → check_onboarding(telegram_chat_id)
  → not done:
      → First name → Last name → Age → Gender → Fitness level
      → get_open_wearables_user_id(firstname, lastname)
      → save_onboarding(data) → PostgreSQL
  → done: "The setup is already done"
```

---

## Alembic

```sh
# Port-forward to PostgreSQL
kubectl port-forward -n ai-agent postgres-cluster-1 5433:5432

# Sync DATABASE_URL (without asyncpg)
export DATABASE_URL="postgresql://<user>:<password>@localhost:5433/ai-agent"

# Get password
kubectl get secret ai-agent-secret -n ai-agent -o jsonpath='{.data.password}' | base64 -d

# New migration
alembic revision -m "description"
alembic upgrade head
alembic downgrade <revision_id>
```

**Rules:**
- Never modify a migration that has already been applied
- Always review autogenerated migrations before running
- Do not convert UUID columns to String

---

## Deploy Workflow

```sh
# 1. Push code → GitHub Actions builds image automatically
git add . && git commit -m "description" && git push

# 2. Deploy k8s changes
git add . && git commit -m "description" && git push
flux reconcile kustomization apps --with-source

# 3. Restart deployments if needed
kubectl rollout restart deployment/agent -n ai-agent
kubectl rollout restart deployment/telegram-bot -n ai-agent

# 4. Manually test CronJobs
kubectl create job --from=cronjob/morning-agent-cron morning-test -n ai-agent
kubectl create job --from=cronjob/evening-agent-cron evening-test -n ai-agent
kubectl logs -n ai-agent -l job-name=morning-test -f
```

---

## HealthClient

```python
client = HealthClient(user_id="<open_wearables_user_id>")
```

| Method | Description |
|--------|-------------|
| `get_sleep(days_back)` | Sleep data per day |
| `get_activity(days_back)` | Steps, calories, active minutes |
| `get_workouts(days_back)` | Workout sessions |
| `get_timeseries(days_back, types)` | Granular timeseries data |
| `get_morning_context()` | Sleep + recovery summary for LLM |
| `get_evening_context()` | Activity + workouts for LLM |
| `get_workout_context()` | Latest workout details for LLM |
| `get_recovery_score(sleep_data)` | Custom recovery score 0–100 |
| `get_baseline()` | 14-day HRV/RHR/sleep baseline |

### Custom Recovery Score
```
hrv_score   = min(hrv_today / baseline_hrv, 1.0)         # weight 50%
rhr_score   = min(baseline_rhr / rhr_today, 1.0)          # weight 30% (inverted)
sleep_score = (min(duration_min / 480, 1.0) * 0.6) +
              (min(efficiency_pct / 100, 1.0) * 0.4)      # weight 20%

recovery_score = clamp(((hrv_score * 0.5) + (rhr_score * 0.3) + (sleep_score * 0.2)) * 100, 0, 100)
```

---

## Known Limitations — Apple Health / Open Wearables

- `avg_heart_rate_bpm` during sleep — always null, Apple does not provide this
- Recovery score — no native Apple score, hence custom implementation
- HRV RMSSD — null, only SDNN available
- Sleep sync delay — new data sometimes only appears after reconnecting in the Open Wearables app

---

## Roadmap

### ✅ Completed
- FastAPI agent + Telegram bot
- Ollama LLM connection (OpenAI-compatible API)
- HealthClient with all health functions
- Custom recovery score based on HRV, RHR and sleep
- PostgreSQL via CNPG + Alembic migrations
- GitHub Actions CI/CD pipeline
- FluxCD GitOps deployment
- Onboarding flow via Telegram ConversationHandler
- `open_wearables_user_id` automatically fetched and saved during onboarding
- Morning CronJob (08:00) with user profile + health context
- Evening CronJob (22:30) with activity + workout context
- User context in reactive messages (database lookup on telegram_chat_id)

### 🔜 Next steps (in order)

1. **Improve system prompt** — LLM sometimes invents goals that don't exist; prompt should explicitly forbid this and handle empty goals/injuries fields
2. **Goals flow** — collect goals via Telegram and save to `goals` table; inject into LLM context
3. **Injuries flow** — collect injuries via Telegram and save to `injuries` table; inject into LLM context
4. **LangChain integration** — replace raw OpenAI client with LangChain for prompt management, memory and tool abstractions
4. **Qdrant deployment** — store and retrieve conversation history for memory between sessions
5. **LangGraph implementation** — structured agent orchestration built on top of LangChain
6. **Cloudflare Tunnel** — external access for webhook endpoint
7. **Workout webhook** — Open Wearables webhook → FastAPI → direct Telegram notification after workout
8. **Sleep/wake trigger** — send messages based on actual sleep and wake time (Apple Health) instead of fixed CronJob times

### 💡 Nice to have
- Fetch weight/height via timeseries instead of manual input during onboarding
- Multi-user support — extend `send_proactive_message` with `chat_id` parameter per user

# Creating a invitiation token for the Apple app

1. Create a bearer token:
curl -X POST http://api.ai-fitness-coach.be/api/v1/auth/login   -H "Content-Type: application/x-www-form-urlencoded"   -d "username={USERNAME}&password={PASSWORD}"

2. Create an invitation code:
curl -X POST http://api.ai-fitness-coach.be/api/v1/users/{USER_ID}/invitation-code   -H "Authorization: Bearer {BEARER_TOKEN}"