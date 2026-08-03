"""Synthetic FS-shaped service corpus generator (G5 rehearsal spec, 2026-08-03).
COLLUSION FIREWALL: like calgen, this module must never reference the detection
side's judgment machinery — it consumes pathology descriptions from the service
spec and nothing else (R-VAL-2 discipline; enforced by tests/test_service_spec.py).
Output is synthetic and O1-only by construction (PRD §2.3)."""
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, model_validator
from cix.contracts import InteractionUnit
from cix.model import MalformedResponse, ModelClient, complete_json

GEN_PROMPT_VERSION = "1.0.0"

class ServicePathology(BaseModel):
    key: str
    maps_to_item: str            # item id only — never item text (firewall holds)
    description: str
    source_type: Literal["transcript", "email", "note"] = "transcript"
    participants: list[str] = ["agent", "customer"]

class ThreadSpec(BaseModel):
    key: str
    pathology: str               # planted in contacts 2..n; contact 1 just raises the issue
    interactions: int = Field(ge=2)
    issue: str                   # continuity anchor fed to every contact's prompt

class SingleSpec(BaseModel):
    pathology: str
    count: int = Field(ge=1)

class ServiceSpec(BaseModel):
    version: str
    id_prefix: str
    seed: int
    style_guide: str
    threads: list[ThreadSpec]
    singles: list[SingleSpec]
    clean_interactions: int
    pathologies: list[ServicePathology]

    @model_validator(mode="after")
    def _referenced_pathologies_exist(self):
        keys = {p.key for p in self.pathologies}
        missing = ({t.pathology for t in self.threads} | {s.pathology for s in self.singles}) - keys
        if missing:
            raise ValueError(f"spec references unknown pathology keys: {sorted(missing)}")
        return self

def load_service_spec(path: Path) -> ServiceSpec:
    return ServiceSpec.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

def build_service_slots(spec: ServiceSpec) -> list[dict]:
    """Deterministic slot assignment per spec seed (mirrors calgen.build_slots discipline)."""
    by_key = {p.key: p for p in spec.pathologies}
    slots: list[dict] = []
    for t in spec.threads:
        for k in range(1, t.interactions + 1):
            slots.append({"kind": "thread", "thread": t, "contact_index": k,
                          "pathology": by_key[t.pathology] if k > 1 else None})
    for s in spec.singles:
        for _ in range(s.count):
            slots.append({"kind": "plant", "pathology": by_key[s.pathology]})
    slots += [{"kind": "clean"} for _ in range(spec.clean_interactions)]
    random.Random(spec.seed).shuffle(slots)
    return slots
