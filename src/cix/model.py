import json
import re
from typing import Protocol
from cix.runconfig import RunConfig

class MalformedResponse(Exception):
    pass

class ModelClient(Protocol):
    def complete(self, prompt: str) -> str: ...

class ScriptedClient:
    """Offline test client. Match canned responses by prompt substring, or serve a fixed sequence."""
    def __init__(self, mapping: dict[str, str] | None = None, sequence: list[str] | None = None):
        self.mapping = mapping or {}
        self.sequence = list(sequence or [])
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        if self.sequence:
            return self.sequence.pop(0)
        for key, resp in self.mapping.items():
            if all(part in prompt for part in key.split("&&")):
                return resp
        raise AssertionError(f"ScriptedClient has no response for prompt: {prompt[:120]}...")

class AnthropicClient:
    def __init__(self, config: RunConfig):
        import anthropic
        self._client = anthropic.Anthropic()
        self._config = config

    def complete(self, prompt: str) -> str:
        msg = self._client.messages.create(
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

def _extract_json(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw = m.group(1) if m else text.strip()
    return json.loads(raw)

def complete_json(client: ModelClient, prompt: str) -> dict:
    """One retry on malformed output, then a clean failure (AC-13)."""
    for attempt in (1, 2):
        try:
            return _extract_json(client.complete(prompt))
        except (json.JSONDecodeError, AttributeError):
            if attempt == 2:
                raise MalformedResponse("model returned non-JSON twice")
    raise MalformedResponse("unreachable")
