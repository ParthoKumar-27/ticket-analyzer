# Ticket Analyzer — Product Requirement Document

Minimal full-stack engineering demo for bKash presents SUST CSE Carnival 2026
— Codex Community Hackathon.

## 1. Product Overview
Ticket Analyzer accepts a support ticket, analyzes its sentiment with a tiny
Hugging Face model, stores it in PostgreSQL, and shows ticket history in a
simple frontend.

## 2. Scope
| Area | Included | Not included |
|---|---|---|
| Frontend | One form + ticket list | Auth, dashboard |
| Backend | Three API endpoints | Complex service layers |
| AI | Tiny sentiment model | Fine-tuning, LLM agents |
| Database | PostgreSQL persistence | Migrations, analytics |
| Deployment | Docker Compose on VM | Kubernetes, CI/CD |

## 3. API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | Backend status |
| POST | /tickets | Create ticket, analyze sentiment |
| GET | /tickets | List saved tickets |

## 4. Data Model
| Field | Type | Notes |
|---|---|---|
| id | integer | Primary key |
| title | string | Ticket title |
| message | text | Ticket body |
| category | string | Optional |
| sentiment | string | Model output label |
| confidence | float | Model confidence |
| created_at | timestamp | Set by backend |

## 5. AI Model
`distilbert-base-uncased-finetuned-sst-2-english`, weights baked into the
backend image at build time, loaded once into memory at startup.

## 6. Acceptance Criteria
- Frontend opens successfully (local and deployed).
- `GET /health` returns `ok`.
- A ticket submitted from the frontend is analyzed and persisted.
- Refreshing the page still shows saved tickets.
- Code on GitHub; images on DockerHub.
- App runs on AWS / Poridhi Cloud VM, deployed via the documented workflow.
- Backend starts with no network access to huggingface.co (weights are baked in).
- A fresh Postgres volume auto-creates the `tickets` table on first start.
- A non-localhost browser can submit a ticket against the deployed app.
- Sentiment output uses `POSITIVE`/`NEGATIVE` labels, confirming the real model.