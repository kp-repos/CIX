from pathlib import Path
import yaml
from pydantic import BaseModel
from cix.model import MalformedResponse

def _content_or_raise(response) -> str:
    """GPT-5.x reasoning tiers can return content=None when max_completion_tokens
    is exhausted by reasoning before any text is emitted. Fail with a clear,
    actionable error rather than a misleading downstream JSON-parse failure."""
    choice = response.choices[0]
    content = choice.message.content
    if content is None:
        raise MalformedResponse(
            f"second-lab returned no content (finish_reason={choice.finish_reason}); "
            "likely truncated — raise max_tokens in second_lab_config_v1.yaml")
    return content

class SecondLabConfig(BaseModel):
    version: str
    lab: str
    model: str
    max_tokens: int
    audit_sample_hits: int
    agreement_floor: float
    min_sample_for_validity: int

def load_second_lab_config(path: Path) -> SecondLabConfig:
    return SecondLabConfig.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))

class OpenAIClient:
    """Second-lab seat/generator (OD-2). Satisfies the ModelClient protocol.
    Temperature is deliberately not sent — GPT-5.x reasoning tiers reject non-default values."""
    def __init__(self, config: SecondLabConfig):
        import openai
        self._client = openai.OpenAI()
        self._config = config

    def complete(self, prompt: str) -> str:
        r = self._client.chat.completions.create(
            model=self._config.model,
            max_completion_tokens=self._config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return _content_or_raise(r)
