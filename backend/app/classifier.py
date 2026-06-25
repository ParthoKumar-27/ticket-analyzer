"""Rule-based classifier for the QueueStorm /sort-ticket endpoint.

Why rule-based:
- Task spec allows it ("LLM usage allowed but not required. Rules based
  solutions are accepted.")
- No GPU, no network, no model weights — keeps the backend image small and
  responses fast (< 10s health, < 30s classify).
- Deterministic output, easy for the grader to reproduce.

The classifier scores the message against a few keyword families and picks
the highest-scoring case_type. A handful of money-amount and urgency signals
adjust severity. ``agent_summary`` is a templated neutral sentence and
**never** asks the customer for PIN, OTP, password, or card numbers (see
spec §5 Safety Rule).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


# --- Keyword families ------------------------------------------------------

# Each entry: (case_type, list_of_regex_patterns). Patterns are matched
# case-insensitively across the lower-cased message.
PHISHING_PATTERNS: list[str] = [
    r"\botp\b",
    r"\bpin\b",
    r"\bpassword\b",
    r"\bcvv\b",
    r"\bcard\s*number\b",
    r"\bshare\b.*\b(otp|pin|password|code)\b",
    r"\bask(?:ing|ed|s)?\b.*\b(otp|pin|password|code|verification)\b",
    r"\bverify\b.*\b(account|number|identity)\b",
    r"\bscammer?\b",
    r"\bscam\b",
    r"\bphish(?:ing)?\b",
    r"\bsuspicious\s+(call|sms|message|person)\b",
    r"\bsomeone\s+call(?:ed|ing)\b",
    r"\bimpersonat(?:e|ion|or)\b",
    r"\bfraud(?:ster)?\b",
]

WRONG_TRANSFER_PATTERNS: list[str] = [
    r"\bwrong\s+(number|person|account|recipient)\b",
    r"\bsent\b.*\bby\s+mistake\b",
    r"\bsent\b.*\baccidentally\b",
    r"\baccidentally\s+sent\b",
    r"\btransfer(?:red|ring)?\b.*\bwrong\b",
    r"\bsent\b.*\bto\s+(?:the\s+)?wrong\b",
    r"\bmisdirected\b",
    r"\bnot\s+(?:the\s+)?intended\b",
    r"\bget\s+(?:it\s+)?back\b",
    r"\brecover\b.*\bmoney\b",
    r"\brefund\b.*\bwrong\b",
]

PAYMENT_FAILED_PATTERNS: list[str] = [
    r"\bpayment\s+fail(?:ed|ure)?\b",
    r"\btransaction\s+fail(?:ed|ure)?\b",
    r"\btransaction\s+(?:didn'?t|did\s+not)\s+go\s+through\b",
    r"\bbalance\s+(?:is\s+)?deduct(?:ed|ion)\b",
    r"\bmoney\s+(?:is\s+)?deduct(?:ed|ion)\b",
    r"\bcharged\b.*\b(?:but|however|yet)\b",
    r"\bdeduct(?:ed|ion)\b.*\b(?:but|however|yet)\b.*\b(?:fail|not\s+received|missing)\b",
    r"\bdouble\s+charg(?:ed|e)\b",
    r"\bpending\b",
    r"\bnot\s+credited\b",
    r"\bdeclin(?:ed|e)\b",
    r"\berror\b.*\b(?:payment|transaction)\b",
]

REFUND_PATTERNS: list[str] = [
    r"\brefund\b",
    r"\bmoney\s+back\b",
    r"\bchargeback\b",
    r"\breverse\b.*\b(?:payment|transaction|charge)\b",
    r"\bchanged\s+my\s+mind\b",
    r"\bcancel\b.*\border\b",
    r"\breturn\b.*\bmoney\b",
]


# --- Severity boosters -----------------------------------------------------

URGENCY_PATTERNS: list[str] = [
    r"\burgent(?:ly)?\b",
    r"\bimmediately\b",
    r"\bright\s+now\b",
    r"\basap\b",
    r"\bplease\s+help\b",
]

LARGE_AMOUNT_RE = re.compile(
    r"\b(\d{1,3}(?:[, ]\d{2,3}){1,}|\d{4,})\s*(?:taka|tk|bdt|৳)\b",
    re.IGNORECASE,
)

# Detect "lost money / stolen / hacked" to push severity up.
LOSS_PATTERNS: list[str] = [
    r"\blost\b",
    r"\bstolen\b",
    r"\bhacked\b",
    r"\b(?:was|got|have\s+been)\s+scammed\b",
    r"\bscammer\b",
]


# --- Result type -----------------------------------------------------------


@dataclass
class Classification:
    case_type: str
    severity: str
    department: str
    agent_summary: str
    human_review_required: bool
    confidence: float


# --- Helpers ---------------------------------------------------------------


def _count_hits(patterns: Iterable[str], text: str) -> tuple[int, list[str]]:
    hits: list[str] = []
    for p in patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            hits.append(p)
    return len(hits), hits


def _extract_amount(text: str) -> str | None:
    m = LARGE_AMOUNT_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return None
    # Format with comma separators, no currency code in summary (kept neutral).
    try:
        return f"{int(digits):,}"
    except ValueError:
        return None


def _build_summary(
    case_type: str,
    amount: str | None,
    message: str,
) -> str:
    """Produce one or two neutral sentences describing the ticket.

    Crucially: never ask the customer to share PIN, OTP, password, or full
    card number (spec §5 Safety Rule). We only describe what the customer
    reported.
    """
    snippet = message.strip()
    if len(snippet) > 140:
        snippet = snippet[:137].rstrip() + "..."

    if case_type == "wrong_transfer":
        amt = f" {amount} BDT" if amount else " money"
        return (
            f"Customer reports sending{amt} to the wrong recipient "
            f"and asks for help recovering it."
        )
    if case_type == "payment_failed":
        amt = f" {amount} BDT" if amount else " balance"
        return (
            f"Customer reports a failed transaction and asks the team "
            f"to investigate the{amt} that may have been deducted."
        )
    if case_type == "refund_request":
        return (
            "Customer is requesting a refund for a recent transaction."
        )
    if case_type == "phishing_or_social_engineering":
        return (
            "Customer reports a possible social-engineering or phishing "
            "attempt and is being routed to the fraud team for review."
        )
    # other
    return (
        "Customer submitted a support message that did not match a known "
        "case category and is being routed to general support."
    )


def _department_for(case_type: str) -> str:
    # Per spec §4.2 enum table.
    if case_type == "wrong_transfer":
        return "dispute_resolution"
    if case_type == "payment_failed":
        return "payments_ops"
    if case_type == "phishing_or_social_engineering":
        return "fraud_risk"
    if case_type == "refund_request":
        return "dispute_resolution"
    return "customer_support"


# --- Public entry point ----------------------------------------------------


def classify_ticket(message: str) -> Classification:
    """Classify a free-text customer message into the spec's response shape."""
    text = (message or "").strip()
    if not text:
        return Classification(
            case_type="other",
            severity="low",
            department="customer_support",
            agent_summary="Empty ticket received; routing to general support.",
            human_review_required=False,
            confidence=0.5,
        )

    lower = text.lower()

    # Score each case family.
    phishing_score, _ = _count_hits(PHISHING_PATTERNS, lower)
    wrong_score, _ = _count_hits(WRONG_TRANSFER_PATTERNS, lower)
    pay_score, _ = _count_hits(PAYMENT_FAILED_PATTERNS, lower)
    refund_score, _ = _count_hits(REFUND_PATTERNS, lower)

    # Disambiguation: if a "refund" message is clearly about a wrong transfer,
    # it should be wrong_transfer, not refund_request. E.g. "refund my wrong
    # transfer" — refund hits but wrong hits too and the intent is recovery.
    if wrong_score > 0 and refund_score > 0 and wrong_score >= refund_score:
        refund_score = 0

    scores = {
        "phishing_or_social_engineering": phishing_score,
        "wrong_transfer": wrong_score,
        "payment_failed": pay_score,
        "refund_request": refund_score,
    }

    # Pick the highest-scoring case_type (prefer the first one in the
    # priority order on ties — phishing first, then wrong, then pay, then
    # refund, to satisfy the safety-critical default of the spec).
    priority = [
        "phishing_or_social_engineering",
        "wrong_transfer",
        "payment_failed",
        "refund_request",
    ]
    best = "other"
    best_score = 0
    for name in priority:
        s = scores[name]
        if s > best_score:
            best = name
            best_score = s

    case_type = best

    # Severity.
    urgency_hits, _ = _count_hits(URGENCY_PATTERNS, lower)
    loss_hits, _ = _count_hits(LOSS_PATTERNS, lower)
    amount = _extract_amount(lower)
    amount_value = int(re.sub(r"[^\d]", "", amount)) if amount else 0
    is_large_amount = amount_value >= 5000

    if case_type == "phishing_or_social_engineering":
        # Spec sample #3 expects "critical" for OTP-style phishing.
        severity = "critical"
    elif case_type == "wrong_transfer":
        # Money already left the customer's account → high by default.
        # Only soften when the wording explicitly frames it as low-stakes
        # (e.g. "small amount", "test transfer", "no money lost").
        small = bool(re.search(r"\b(small|tiny|test|little)\b", lower))
        if small and not (is_large_amount or loss_hits or urgency_hits):
            severity = "medium"
        else:
            severity = "high"
    elif case_type == "payment_failed":
        # Balance already deducted → high by default (money is at risk).
        severity = "high"
    elif case_type == "refund_request":
        if is_large_amount:
            severity = "medium"
        else:
            severity = "low"
    else:  # other
        severity = "low"

    department = _department_for(case_type)
    summary = _build_summary(case_type, amount, text)
    human_review = severity == "critical" or case_type == "phishing_or_social_engineering"

    # Confidence: based on how decisively a single case family won.
    total = sum(scores.values())
    if total == 0:
        confidence = 0.55  # default for "other"
    else:
        # Winner share, floored at 0.6 and capped at 0.95.
        share = best_score / total
        confidence = max(0.6, min(0.95, 0.6 + 0.35 * share))

    return Classification(
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=summary,
        human_review_required=human_review,
        confidence=round(confidence, 2),
    )
