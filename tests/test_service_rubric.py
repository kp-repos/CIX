from pathlib import Path
import yaml
from cix.rubric import load_rubric
from cix.catalogue import load_catalogue
from textcheck import ngrams

RUBRIC = Path("configs/service_rubric_v1.yaml")
PARAS = Path("configs/paraphrases_service_v1.yaml")

def _rubric():
    return load_rubric(RUBRIC, "1.0.0", "1.0.0")

def _para_doc():
    return yaml.safe_load(PARAS.read_text(encoding="utf-8"))

def test_service_rubric_meets_floor():
    r = _rubric()
    assert len(r.items) >= 8                       # PRD §3 evaluable floor
    assert any(i.polarity == "positive" for i in r.items)   # R-RUB-1 one mechanism, two polarities

def test_units_are_linkage_free_or_declared():
    r = _rubric()
    # calibration/real corpora may lack account linkage; keep units to occurrence/interaction
    assert {i.unit_of_count for i in r.items} <= {"occurrence", "interaction"}

def test_swap_refs_resolve_against_catalogue():
    r = _rubric()
    cat = load_catalogue(Path("configs/catalogue_v0_1.yaml"))
    for i in r.items:
        if i.swap_ref is not None:
            assert cat.by_id(i.swap_ref) is not None, f"{i.id} -> dangling swap_ref {i.swap_ref}"

def test_swap_ref_units_are_compatible():
    r = _rubric()
    cat = load_catalogue(Path("configs/catalogue_v0_1.yaml"))
    for i in r.items:
        if i.swap_ref is not None:
            e = cat.by_id(i.swap_ref)
            assert e.unit_basis == i.unit_of_count, (
                f"{i.id} unit '{i.unit_of_count}' incompatible with {e.id} basis '{e.unit_basis}'")

# --- T-PARA paraphrase set (frozen instrument for A9) ---

def test_service_paraphrase_set_is_bound_to_the_rubric():
    r = _rubric()
    doc = _para_doc()
    assert doc["rubric_version"] == r.version
    assert doc["rubric_file"] == RUBRIC.name        # identity bind, not version-only

def test_service_paraphrase_set_covers_rubric_exactly():
    r = _rubric()
    paras = _para_doc()["paraphrases"]
    assert set(paras) == {i.id for i in r.items}     # every item, and no extras
    for item in r.items:
        assert paras[item.id].strip()                # non-empty

def test_service_paraphrases_are_lexically_disjoint_from_their_item():
    """Stronger than the sales `!= criterion` check: each paraphrase must be
    5-gram-disjoint from its own criterion AND its exemplars — a real reword,
    not a surface edit, so T-PARA measures meaning-stability, not string reuse."""
    r = _rubric()
    paras = _para_doc()["paraphrases"]
    for item in r.items:
        item_text = " ".join([item.criterion] + item.exemplars)
        overlap = ngrams(paras[item.id]) & ngrams(item_text)
        assert not overlap, f"{item.id} paraphrase reuses wording: {overlap}"
