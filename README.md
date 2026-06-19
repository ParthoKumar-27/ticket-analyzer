# Ticket Analyzer

A minimal full-stack demo: submit a support ticket, get its sentiment analyzed
by a tiny Hugging Face model, and see it persisted in PostgreSQL.

## Architecture

React (Nginx) → FastAPI (Uvicorn) → [distilbert-sst-2 sentiment model, PostgreSQL]

The frontend talks to the backend only through Nginx's `/api/*` reverse proxy,
so no CORS configuration is needed and the same images work on localhost and
in production.

## Local Setup

Prerequisites: Docker and Docker Compose.

```bash
git clone https://github.com/<your-username>/ticket-analyzer.git
cd ticket-analyzer
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend health check: http://localhost:8000/health

Environment variables (see `.env.example`): `DATABASE_URL`, `MODEL_NAME`,
`HF_HOME`, `TRANSFORMERS_OFFLINE`.

## API Reference

### `GET /health`
Response: `{"status": "ok"}`

### `POST /tickets`
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

- GitHub: https://github.com/<your-username>/ticket-analyzer
- DockerHub backend: https://hub.docker.com/r/<dockerhub-username>/ticket-analyzer-backend
- DockerHub frontend: https://hub.docker.com/r/<dockerhub-username>/ticket-analyzer-frontend
- Live URL: http://<vm-public-ip>:3000

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