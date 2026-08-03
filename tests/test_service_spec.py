import re
from pathlib import Path
from cix.servicegen import build_service_slots, load_service_spec
from cix.rubric import load_rubric

SPEC = Path("configs/service_corpus_spec_v1.yaml")

def _ngrams(text: str, n: int = 5) -> set[str]:
    toks = re.findall(r"[a-z']+", text.lower())
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}

def test_spec_loads_and_crosswalk_targets_real_a9_items():
    spec = load_service_spec(SPEC)
    rubric = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    item_ids = {i.id for i in rubric.items}
    assert {p.maps_to_item for p in spec.pathologies} <= item_ids
    assert len(spec.pathologies) == 8

def test_vocabulary_disjointness_against_a9():
    """R-VAL-2 discipline: the plant author sees pathology descriptions, never rubric text.
    No description (or thread issue) shares a 5-token n-gram with any A9 criterion/exemplar."""
    spec = load_service_spec(SPEC)
    rubric = load_rubric(Path("configs/service_rubric_v1.yaml"), "1.0.0", "1.0.0")
    rubric_text = " ".join([i.criterion for i in rubric.items]
                           + [e for i in rubric.items for e in i.exemplars])
    for p in spec.pathologies:
        overlap = _ngrams(p.description) & _ngrams(rubric_text)
        assert not overlap, f"{p.key} shares wording with A9 text: {overlap}"
    for t in spec.threads:
        overlap = _ngrams(t.issue) & _ngrams(rubric_text)
        assert not overlap, f"thread {t.key} issue shares wording with A9 text: {overlap}"

def test_differential_target_coverage_minimums():
    """Spec §3.1 hard requirement: >=6 repeat_contact plants, >=2 threads, >=3 deterministic."""
    spec = load_service_spec(SPEC)
    by_key = {p.key: p for p in spec.pathologies}
    repeat = sum(t.interactions - 1 for t in spec.threads
                 if by_key[t.pathology].maps_to_item == "repeat_contact_unresolved")
    repeat += sum(s.count for s in spec.singles
                  if by_key[s.pathology].maps_to_item == "repeat_contact_unresolved")
    determin = sum(s.count for s in spec.singles
                   if by_key[s.pathology].maps_to_item == "deterministic_request")
    assert repeat >= 6
    assert len(spec.threads) >= 2
    assert determin >= 3

def test_slot_shapes_and_determinism():
    spec = load_service_spec(SPEC)
    slots = build_service_slots(spec)
    thread_slots = [s for s in slots if s["kind"] == "thread"]
    plant_slots = [s for s in slots if s["kind"] == "plant"]
    clean_slots = [s for s in slots if s["kind"] == "clean"]
    assert len(thread_slots) == sum(t.interactions for t in spec.threads)
    assert len(plant_slots) == sum(s.count for s in spec.singles)
    assert len(clean_slots) == spec.clean_interactions
    assert len(slots) == 100
    # first contact of a thread carries no plant; later contacts carry the thread pathology
    firsts = [s for s in thread_slots if s["contact_index"] == 1]
    assert all(s["pathology"] is None for s in firsts)
    assert all(s["pathology"] is not None for s in thread_slots if s["contact_index"] > 1)
    assert build_service_slots(spec) == slots            # deterministic per seed

def test_servicegen_never_touches_rubric_code():
    """Collusion break, structural: the generator module must not import or read rubric machinery."""
    import cix.servicegen
    src = Path(cix.servicegen.__file__).read_text(encoding="utf-8")
    assert "rubric" not in src.lower()
