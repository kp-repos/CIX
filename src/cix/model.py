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

# Purpose-framing system prompt for the CLASSIFICATION path (labels, rubric hits,
# audits). Establishes legitimate analytical context so the detector objectively
# classifies conduct-related content (e.g. off-system discounting) instead of issuing
# a spurious safety refusal. Deliberately neutral — it does NOT tell the model what to
# detect or bias toward finding anything, so it is calibration-neutral. Not used on the
# generation path. (G3 finding, 2026-08-01; v1.0.0)
ANALYST_SYSTEM_PROMPT = (
    "You are a business-operations analyst performing authorized process-improvement research. "
    "You are given transcripts of customer-facing and internal business interactions and asked to "
    "classify them or extract structured descriptive fields. The material is provided under "
    "authorization for legitimate analysis; some transcripts depict mistakes, policy exceptions, or "
    "improper conduct (for example, a discount arranged outside an approval workflow), and objectively "
    "labeling such content is exactly the purpose of the work — you are describing what happened, not "
    "endorsing or enabling it. Classify factually and completely, without moralizing. Do not refuse; "
    "return only the structured output requested."
)

class AnthropicClient:
    def __init__(self, config: RunConfig):
        import anthropic
        self._client = anthropic.Anthropic()
        self._config = config

    def complete(self, prompt: str) -> str:
        # temperature is deliberately not sent — some current Claude tiers deprecate
        # the parameter and reject the call if it is present; omitting it uses the
        # model default and is safe across tiers (as OpenAIClient does likewise).
        msg = self._client.messages.create(
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            system=ANALYST_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        # extended-thinking tiers may lead the response with thinking blocks that
        # carry no .text — concatenate the text blocks only.
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        if not text:
            raise MalformedResponse(f"no text block in response (stop_reason={msg.stop_reason})")
        return text

def _first_balanced_object(text: str) -> str | None:
    """Return the first brace-balanced {...} substring (string-literal aware), or None."""
    start = text.find("{")
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None

def _extract_json(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        obj = _first_balanced_object(text)  # tolerate a prose preamble around bare JSON
        if obj is None:
            raise
        return json.loads(obj)

def complete_json(client: ModelClient, prompt: str, attempts: int = 4) -> dict:
    """Retry transient failures — malformed JSON, and empty/`refusal` responses that
    reasoning tiers occasionally emit — up to `attempts` times, then fail cleanly (AC-13).
    Never drops an interaction silently: a persistent failure aborts the run rather than
    skewing calibration counts."""
    last: Exception | None = None
    for _ in range(attempts):
        try:
            return _extract_json(client.complete(prompt))
        except (json.JSONDecodeError, AttributeError, MalformedResponse) as e:
            last = e
    raise MalformedResponse(f"model returned unusable output {attempts}x: {last}")
