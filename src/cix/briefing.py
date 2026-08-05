"""Business Briefing presentation layer (model-free): re-render a persisted run for a
commercial reader. Reads report.json + manifest.json + the run store (read-only),
enforces honesty rules, and emits briefing.json + self-contained HTML + PDF.

Nothing here calls a model or mutates the store — the instrument stays frozen.
"""
from pathlib import Path
import yaml

def load_presentation(path: Path) -> dict:
    """Load the versioned presentation config (labels/glosses + headline-metric membership)."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
