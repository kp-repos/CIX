"""Deterministic G2 fixture generator. Run: uv run python tests/fixtures/generate_g2.py"""
import json
import random
from pathlib import Path

TEMPLATES = {
    "billing_double_charge": [
        ("customer", "My card was charged twice for the {item} order, ${amt} each time."),
        ("agent", "I can see the duplicate charge. Let me open a billing correction."),
        ("customer", "I already called about this last time and it is still not fixed."),
        ("agent", "I will escalate this to the billing team."),
    ],
    "fee_dispute": [
        ("customer", "I was told the {fee} fee would be waived but I see a ${amt} charge."),
        ("agent", "Please hold on while I transfer you to the fees desk."),
    ],
    "password_reset": [
        ("customer", "How do I reset my password for {item} access?"),
        ("agent", "I can send you a reset link right now."),
        ("customer", "That worked, thanks."),
    ],
    "delivery_complaint": [
        ("customer", "My {item} statement never arrived this month."),
        ("agent", "I have re-sent it and confirmed your mailing preference."),
        ("customer", "Great, that resolves it, thanks."),
    ],
}
BILLING = {"billing_double_charge", "fee_dispute"}
ITEMS = ["chequing", "savings", "credit card", "mortgage", "loan"]
FEES = ["annual", "overdraft", "wire", "statement"]

def gen(out_dir: Path, n: int, allowed: list[str], seed: int) -> None:
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.json"):
        old.unlink()
    for i in range(n):
        name = allowed[i % len(allowed)]
        subs = {"item": rng.choice(ITEMS), "amt": rng.choice([25, 40, 75, 120]), "fee": rng.choice(FEES)}
        uid = f"g2-{out_dir.name.split('_')[-1]}-{i:03d}"
        doc = {
            "id": uid, "source_type": "transcript",
            "participants": ["agent", "customer"],
            "date": f"2026-06-{(i % 28) + 1:02d}",
            "account_id": f"acct-{rng.randint(1, 9)}",
            "segments": [{"speaker": s, "text": t.format(**subs)} for s, t in TEMPLATES[name]],
        }
        (out_dir / f"{uid}.json").write_text(json.dumps(doc, indent=2))

if __name__ == "__main__":
    base = Path(__file__).parent
    gen(base / "corpus_g2", 24, list(TEMPLATES), seed=101)
    gen(base / "corpus_g2_null", 12, [t for t in TEMPLATES if t not in BILLING], seed=202)
    print("fixtures written")
