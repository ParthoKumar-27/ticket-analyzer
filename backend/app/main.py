from typing import List

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models, schemas
from app.sentiment import load_model, analyze

app = FastAPI(title="Ticket Analyzer API")

# Only matters if you bypass the Nginx reverse proxy and call the backend
# cross-origin directly. Harmless to leave on otherwise.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)  # creates `tickets` table if missing
    load_model()  # load once at startup, not lazily on first request


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets", response_model=schemas.TicketOut)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    label, score = analyze(ticket.message)
    db_ticket = models.Ticket(
        title=ticket.title,
        message=ticket.message,
        category=ticket.category,
        sentiment=label,
        confidence=score,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.get("/tickets", response_model=List[schemas.TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    return db.query(models.Ticket).order_by(models.Ticket.created_at.desc()).all()