"""Differential-perturbation tooling (R-VAL-7, AC-16). Pure functions over a scrubbed +
labeled corpus: each returns the perturbed variant and its predeclared expected delta.
score_delta compares an instrument reading to the expected delta against T-DIFF tolerance.
Variant *construction on real language* is the post-G4 follow-on; the mechanism is proven
here on synthetic units."""
from cix.contracts import InteractionUnit

def delete_subset(units: list[InteractionUnit], drop_ids: set[str]) -> tuple[list[InteractionUnit], dict]:
    kept = [u for u in units if u.id not in drop_ids]
    return kept, {"perturbation": "delete_subset", "interactions_delta": len(kept) - len(units),
                  "dropped": sorted(drop_ids)}

def duplicate_chains(units: list[InteractionUnit], thread_id: str) -> tuple[list[InteractionUnit], dict]:
    """Duplicate every member of one thread (chain) once, giving copies fresh `-dup` ids.
    Apply once per thread per variant — re-applying to the same thread would collide `-dup` ids."""
    members = [u for u in units if u.thread_id == thread_id]
    dupes = [u.model_copy(update={"id": f"{u.id}-dup"}) for u in members]
    return units + dupes, {"perturbation": "duplicate_chains", "thread_id": thread_id,
                           "interactions_delta": len(dupes)}

def splice_instances(units: list[InteractionUnit], donor: InteractionUnit, copies: int) -> tuple[list[InteractionUnit], dict]:
    spliced = [donor.model_copy(update={"id": f"{donor.id}-{i:03d}"}) for i in range(copies)]
    return units + spliced, {"perturbation": "splice_instances", "copies": copies,
                             "interactions_delta": copies}

def score_delta(expected: dict, observed: dict, tolerance: float) -> dict:
    """Per-variant: does the instrument reading track the predeclared delta within tolerance?"""
    exp, obs = expected["count"], observed["count"]
    abs_err = abs(obs - exp)
    rel_err = abs_err / exp if exp else (0.0 if obs == 0 else 1.0)
    status = "pass" if rel_err <= tolerance else "fail"
    return {"status": status, "expected": exp, "observed": obs,
            "abs_error": abs_err, "rel_error": round(rel_err, 3), "tolerance": tolerance}
