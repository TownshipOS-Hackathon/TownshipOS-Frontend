"""Fake Anthropic client. Mimics only what core/ touches on client.beta.messages."""
from contextlib import contextmanager
from types import SimpleNamespace as NS


class _Messages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []  # kwargs of every call, for assertions

    def _next(self, kw):
        self.calls.append(kw)
        if not self.responses:
            raise AssertionError("FakeClient ran out of responses")
        return self.responses.pop(0)

    def parse(self, **kw):
        return self._next(kw)

    @contextmanager
    def stream(self, **kw):
        r = self._next(kw)
        yield NS(get_final_message=lambda: r)


class FakeClient:
    def __init__(self, *responses):
        self.beta = NS(messages=_Messages(responses))

    @property
    def calls(self):
        return self.beta.messages.calls


def parsed(obj, stop_reason="end_turn"):
    return NS(stop_reason=stop_reason, parsed_output=obj, stop_details=None, content=[])


def refusal(explanation="declined by safety system"):
    return NS(stop_reason="refusal", parsed_output=None, content=[],
              stop_details=NS(type="refusal", category="other", explanation=explanation))


def text_block(text, citations=None):
    return NS(type="text", text=text, citations=citations)


def citation(title, cited_text):
    return NS(type="char_location", document_title=title, cited_text=cited_text, document_index=0)


def message(*blocks, stop_reason="end_turn"):
    return NS(stop_reason=stop_reason, content=list(blocks), stop_details=None)
