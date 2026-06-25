# Ticket Analyzer

A minimal full-stack demo: submit a support ticket, get its sentiment analyzed
by a tiny Hugging Face model, and see it persisted in PostgreSQL.

It also ships a second endpoint, `POST /sort-ticket`, that classifies a
single customer message into a case type, severity, routing department, and a
one-sentence agent summary. This endpoint is built for the
**QueueStorm Warmup: Mock Preliminary Task** (bKash presents SUST CSE
Carnival 2026 — Codex Community Hackathon) and accepts the exact request
and response schemas from that brief.

## Architecture

React (Nginx) → FastAPI (Uvicorn) → [distilbert-sst-2 sentiment model, rule-based classifier, PostgreSQL]

The frontend talks to the backend only through Nginx's `/api/*` reverse proxy,
so no CORS configuration is needed and the same images work on localhost and
in production.

The `/sort-ticket` classifier is **rule-based**: keyword/regex families,
no LLM, no GPU, no external network call at request time. This keeps the
service within the spec's runtime budget (health < 10s, classify < 30s)
and makes the output deterministic for grading.

## Local Setup

Prerequisites: Docker and Docker Compose.

```bash
git clone https://github.com/ParthoKumar-27/ticket-analyzer.git
cd ticket-analyzer
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend health check: http://localhost:8000/health

Environment variables (see `docker-compose.yml`): `DATABASE_URL`, `MODEL_NAME`,
`HF_HOME`, `TRANSFORMERS_OFFLINE`.

## API Reference

### `GET /health`
Response: `{"status": "ok"}`

### `POST /tickets` (existing demo)
Request:
```json
{
  "title": "Lab VM issue",
  "message": "My lab VM is not opening before the deadline.",
  "category": "lab"
}
```
Response:
```json
{
  "id": 1,
  "title": "Lab VM issue",
  "sentiment": "NEGATIVE",
  "confidence": 0.999,
  "created_at": "2026-05-20T10:30:00"
}
```

### `GET /tickets`
Response: array of ticket objects in the same shape as above, newest first.

### `POST /sort-ticket` (QueueStorm)
Request (matches QueueStorm §2 schema):
```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```
Response (matches QueueStorm §3 schema):
```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending 5,000 BDT to the wrong recipient and asks for help recovering it.",
  "human_review_required": true,
  "confidence": 0.85
}
```

`case_type`, `severity`, and `department` are closed enums (see
`backend/app/schemas.py`). `human_review_required` is `true` for any
phishing case or any `critical` severity (QueueStorm §3 + §4).

#### Quick smoke test
```bash
curl -s http://localhost:8000/sort-ticket \
  -H 'Content-Type: application/json' \
  -d '{
        "ticket_id": "T-001",
        "channel": "app",
        "locale": "en",
        "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
      }'
```

The five public sample cases from the brief are expected to resolve as:

| # | Message | case_type | severity |
|---|---|---|---|
| 1 | I sent 3000 to wrong number | `wrong_transfer` | `high` |
| 2 | Payment failed but balance deducted | `payment_failed` | `high` |
| 3 | Someone called asking my OTP, is that bKash? | `phishing_or_social_engineering` | `critical` |
| 4 | Please refund my last transaction, I changed my mind | `refund_request` | `low` |
| 5 | App crashed when I opened it | `other` | `low` |

You can re-run them locally with:

```bash
python scripts/smoke_sort_ticket.py
```

## Deployment

Images are published to DockerHub and pulled directly on the target VM
(AWS instance or Poridhi Cloud VM):

```bash
docker login
docker compose pull
docker compose up -d
```

AWS credentials used to provision/access the VM are sourced from the Poridhi
Lab environment at deploy time (`aws configure`) and are never committed to
this repository.

- GitHub: https://github.com/ParthoKumar-27/ticket-analyzer
- DockerHub backend: https://hub.docker.com/r/parthokumar/ticket-analyzer-backend
- DockerHub frontend: https://hub.docker.com/r/parthokumar/ticket-analyzer-frontend
- Live URL: https://6a32b9355dde7994028daae3_a23f9086.lb.poridhi.io/

### Deployment Runbook (for graders)
If a fresh redeploy is needed on any Docker host (Render / Railway / Fly /
Poridhi VM / EC2):

```bash
# 1. clone
git clone https://github.com/ParthoKumar-27/ticket-analyzer.git
cd ticket-analyzer

# 2. bring the stack up
docker compose up -d --build

# 3. verify
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/sort-ticket \
  -H 'Content-Type: application/json' \
  -d '{"ticket_id":"T-001","channel":"app","locale":"en","message":"I sent 3000 to wrong number"}'
```

No GPU is required and no secrets are baked in — all credentials come from
environment variables (set via `docker compose`, the host's env, or the
platform's secret manager).

## Troubleshooting Notes

- **Backend exits on startup, "connection refused" to Postgres** — fixed by
  the `depends_on: db: condition: service_healthy` healthcheck in
  `docker-compose.yml`, which makes the backend wait for Postgres instead of
  racing it on cold boot.
- **Model tries to download at runtime** — `TRANSFORMERS_OFFLINE=1` makes
  this fail loudly instead of silently hitting the network, confirming the
  weights were actually baked into the image during build.
- **Frontend can't reach backend from a non-localhost browser** — solved by
  the Nginx reverse proxy (`/api/*` → `backend:8000`), so the frontend never
  needs a hardcoded backend hostname or CORS headers.
- **`/sort-ticket` returns unexpected case_type** — the classifier is
  keyword-driven; inspect `backend/app/classifier.py` (pattern lists and
  the disambiguation rules) and adjust before changing the API surface.

## Contributors
### Team Name: **DU_CyberCentinels**

### University: **University of Dhaka**

### Team Members

1. **Md. Samiul Islam Siam**  

2. **Partho Kumar Mondal**  

3. **Faiaz Ibne Iqbal**  
