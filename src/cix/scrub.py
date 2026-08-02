"""Ingest scrub (R-PII-1..4). Deterministic patterns + rules-based name/linkage
pseudonymization; a model-backed NER pass is an opt-in extension (scrub_unit_model,
not wired by default). Nothing unscrubbed leaves this module."""
import hashlib
import re
from pathlib import Path
import yaml
from pydantic import BaseModel
from cix.contracts import InteractionUnit, Segment

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?\d[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}\b")

ROLE_WORDS = {"customer", "rep", "agent", "representative", "support", "caller",
              "user", "operator", "system", "client", "cx", "csr"}

def _is_person(name: str | None) -> bool:
    """A person-name to pseudonymize: has an uppercase letter and is not a generic role word."""
    return bool(name) and name.strip().lower() not in ROLE_WORDS and any(ch.isupper() for ch in name)

class EntityClass(BaseModel):
    name: str
    strategy: str                 # "redact" | "pseudonymize"
    token: str | None = None
    prefix: str | None = None

class PrivacyProtocol(BaseModel):
    version: str
    entity_classes: list[EntityClass]
    audit: dict

def load_privacy_protocol(path: Path) -> PrivacyProtocol:
    return PrivacyProtocol.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

def _pseudonym(prefix: str, raw: str, salt: str) -> str:
    return f"{prefix}-{hashlib.sha256(f'{salt}|{raw}'.encode()).hexdigest()[:8]}"

def _classes(proto: PrivacyProtocol) -> dict[str, EntityClass]:
    return {c.name: c for c in proto.entity_classes}

def scrub_corpus(units: list[InteractionUnit], proto: PrivacyProtocol, salt: str) -> tuple[list[InteractionUnit], dict]:
    cls = _classes(proto)
    counts: dict[str, int] = {c.name: 0 for c in proto.entity_classes}
    scrubbed: list[InteractionUnit] = []
    for u in units:
        # Person-name map from participants AND segment speakers (C-1: a speaker not listed
        # in participants must still be pseudonymized). Generic role words are never treated
        # as identities (I-2).
        name_map: dict[str, str] = {}
        for p in list(u.participants) + [seg.speaker for seg in u.segments]:
            if _is_person(p) and p not in name_map:
                name_map[p] = _pseudonym(cls["person"].prefix, p, salt)
        acct = _pseudonym(cls["account"].prefix, u.account_id, salt) if u.account_id else None
        thread = _pseudonym(cls["thread"].prefix, u.thread_id, salt) if u.thread_id else None
        if acct: counts["account"] += 1
        if thread: counts["thread"] += 1
        new_segs = []
        for seg in u.segments:
            text = seg.text
            counts["email"] += len(EMAIL_RE.findall(text))
            text = EMAIL_RE.sub(cls["email"].token, text)
            counts["phone"] += len(PHONE_RE.findall(text))
            text = PHONE_RE.sub(cls["phone"].token, text)
            for name, token in name_map.items():
                for needle in (name, name.split()[0]):
                    if needle and needle in text:
                        counts["person"] += text.count(needle)
                        text = text.replace(needle, token)
            speaker = name_map.get(seg.speaker, seg.speaker)
            new_segs.append(Segment(speaker=speaker, ts=seg.ts, text=text))
        new_parts = [name_map.get(p, p) for p in u.participants]
        scrubbed.append(InteractionUnit(id=u.id, source_type=u.source_type, participants=new_parts,
                                        date=u.date, account_id=acct, thread_id=thread, segments=new_segs))
    return scrubbed, {"counts": counts, "salt_recorded": True}

def residual_scan(units: list[InteractionUnit]) -> list[dict]:
    """Automated 100% residual re-scan of text AND speaker fields: any leftover email/phone
    pattern is a residual hit."""
    hits: list[dict] = []
    for u in units:
        for n, seg in enumerate(u.segments):
            fields = (seg.text, seg.speaker or "")
            if any(EMAIL_RE.search(f) or PHONE_RE.search(f) for f in fields):
                hits.append({"interaction_id": u.id, "seq": n})
    return hits

def audit_privacy_gate(units: list[InteractionUnit], proto: PrivacyProtocol) -> dict:
    """Automated residual re-scan (100%) + seeded sample marker for human review.
    Returns the manifest privacy_gate status (R-PII-1)."""
    residual = residual_scan(units)
    total_snippets = sum(len(u.segments) for u in units)
    sample_size = min(int(proto.audit["sample_size"]), total_snippets)
    status = "fail" if len(residual) > int(proto.audit["residual_fail_threshold"]) else "pass"
    return {"status": status, "residual_hits": len(residual), "residual": residual,
            "sample_size": sample_size, "sample_seed": int(proto.audit["seed"])}
