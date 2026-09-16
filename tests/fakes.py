"""Fake OpenAI-compatible client. Mimics client.chat.completions.create()."""
import json
from types import SimpleNamespace as NS


class _Completions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        if not self.responses:
            raise AssertionError("FakeClient ran out of responses")
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, *responses):
        comps = _Completions(responses)
        self.chat = NS(completions=comps)
        self._completions = comps

    @property
    def calls(self):
        return self._completions.calls


def tool_result(obj, finish_reason="tool_calls"):
    """Triage happy path: response carries a tool_call with JSON arguments."""
    args = json.dumps(obj.model_dump() if hasattr(obj, "model_dump") else obj)
    tool_call = NS(function=NS(arguments=args, name="triage"), id="tc1", type="function")
    msg = NS(tool_calls=[tool_call], content=None)
    return NS(choices=[NS(message=msg, finish_reason=finish_reason)])


def incomplete(finish_reason="length"):
    """Simulate truncated output (no tool_call, length finish_reason) → triage retries."""
    msg = NS(content=None, tool_calls=None)
    return NS(choices=[NS(message=msg, finish_reason=finish_reason)])


def refusal(explanation="declined by safety system"):
    """No tool_call + text content. Triage falls back; assistant/sustainability return the text."""
    msg = NS(content=explanation, tool_calls=None)
    return NS(choices=[NS(message=msg, finish_reason="stop")])


def text_result(text, finish_reason="stop"):
    """Plain text response for assistant and sustainability."""
    msg = NS(content=text, tool_calls=None)
    return NS(choices=[NS(message=msg, finish_reason=finish_reason)])
