"""Local smoke test for the /sort-ticket rule-based classifier.

Runs the 5 public sample cases from the QueueStorm brief through the
classifier and prints a small table. Useful for graders reproducing the
behaviour without spinning up the full Docker stack.

Usage:
    cd backend
    python -m scripts.smoke_sort_ticket

Or from the repo root:
    PYTHONPATH=backend python scripts/smoke_sort_ticket.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow `from app.classifier import ...` when run as a plain script.
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.classifier import classify_ticket  # noqa: E402


SAMPLES = [
    ("T-001", "I sent 3000 to wrong number"),
    ("T-002", "Payment failed but balance deducted"),
    ("T-003", "Someone called asking my OTP, is that bKash?"),
    ("T-004", "Please refund my last transaction, I changed my mind"),
    ("T-005", "App crashed when I opened it"),
]

EXPECTED = {
    "T-001": ("wrong_transfer", "high"),
    "T-002": ("payment_failed", "high"),
    "T-003": ("phishing_or_social_engineering", "critical"),
    "T-004": ("refund_request", "low"),
    "T-005": ("other", "low"),
}


def main() -> int:
    print(f"{'ticket_id':<10} {'case_type':<35} {'severity':<10} {'review':<6} {'conf':<6}")
    print("-" * 75)
    failures: list[str] = []
    for ticket_id, message in SAMPLES:
        c = classify_ticket(message)
        review = "yes" if c.human_review_required else "no"
        print(
            f"{ticket_id:<10} {c.case_type:<35} {c.severity:<10} {review:<6} {c.confidence:<6}"
        )
        exp_case, exp_sev = EXPECTED[ticket_id]
        if c.case_type != exp_case or c.severity != exp_sev:
            failures.append(
                f"  ! {ticket_id}: expected {exp_case}/{exp_sev}, "
                f"got {c.case_type}/{c.severity}"
            )
    print("-" * 75)
    if failures:
        print("MISMATCHES:")
        for f in failures:
            print(f)
        return 1
    print("All 5 public sample cases match expected case_type and severity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
