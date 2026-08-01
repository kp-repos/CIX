from pathlib import Path
import yaml

CORE_FIELDS = {"motion", "intent", "driver_origin", "automatability", "outcome", "handoff_events"}

def test_label_schema_is_core_only_and_versioned():
    schema = yaml.safe_load(Path("configs/label_schema_v1.yaml").read_text())
    assert schema["version"] == "1.0.0"
    assert set(schema["fields"].keys()) == CORE_FIELDS  # R-RUB-4: no domain extensions
