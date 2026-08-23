from pathlib import Path

import pytest

from automated_e2e.models import Service, Topology
from automated_e2e.topology import TopologyNotFoundError, discover_topology

FIXTURE = Path(__file__).parent / "fixtures" / "sample-shop"


class _FakeSource:
    """Stands in for a future source (e.g. Kubernetes) to prove discover_topology
    is open for extension: new sources plug in without changing discover_topology."""

    def __init__(self, *, matches: bool, topology: Topology | None = None):
        self._matches = matches
        self._topology = topology

    def detect(self, repo_path: Path) -> Path | None:
        return repo_path if self._matches else None

    def parse(self, manifest_path: Path) -> Topology:
        return self._topology


def test_uses_first_matching_source():
    expected = Topology(services=[Service(name="from-fake-source")])
    sources = [_FakeSource(matches=True, topology=expected)]
    assert discover_topology(FIXTURE, sources) is expected


def test_falls_through_to_next_source_when_first_does_not_match():
    expected = Topology(services=[Service(name="from-second-source")])
    sources = [_FakeSource(matches=False), _FakeSource(matches=True, topology=expected)]
    assert discover_topology(FIXTURE, sources) is expected


def test_raises_when_no_source_matches():
    with pytest.raises(TopologyNotFoundError):
        discover_topology(FIXTURE, [_FakeSource(matches=False)])
