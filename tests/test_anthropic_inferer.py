from dataclasses import dataclass
from pathlib import Path

from automated_e2e.inference import AnthropicJourneyInferer
from automated_e2e.models import Topology

FIXTURE = Path(__file__).parent / "fixtures" / "sample-shop"


@dataclass
class _FakeTextBlock:
    text: str
    type: str = "text"


class _FakeMessages:
    def __init__(self, response_text: str):
        self._response_text = response_text

    def create(self, **kwargs):
        return type("FakeResponse", (), {"content": [_FakeTextBlock(self._response_text)]})()


class _FakeClient:
    def __init__(self, response_text: str):
        self.messages = _FakeMessages(response_text)


def test_parses_plain_json_response():
    topology = Topology()
    inferer = AnthropicJourneyInferer(
        client=_FakeClient(
            '{"journeys": [{"id": "checkout", "priority": "high", '
            '"steps": ["login"], "services": ["frontend"]}]}'
        )
    )
    journeys = inferer.infer(topology, FIXTURE)
    assert len(journeys) == 1
    assert journeys[0].id == "checkout"


def test_parses_response_wrapped_in_markdown_fence():
    topology = Topology()
    inferer = AnthropicJourneyInferer(
        client=_FakeClient(
            '```json\n{"journeys": [{"id": "checkout", "priority": "low", '
            '"steps": ["login"], "services": ["frontend"]}]}\n```'
        )
    )
    journeys = inferer.infer(topology, FIXTURE)
    assert len(journeys) == 1
    assert journeys[0].priority == "low"


def test_empty_journeys_list_is_valid():
    topology = Topology()
    inferer = AnthropicJourneyInferer(client=_FakeClient('{"journeys": []}'))
    assert inferer.infer(topology, FIXTURE) == []
