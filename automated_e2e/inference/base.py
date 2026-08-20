"""Abstraction for a strategy that turns a topology into a list of journeys."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from automated_e2e.models import Journey, Topology


class JourneyInferer(Protocol):
    """Something that can propose journeys for a repo's topology.

    Swapping the backend (Anthropic today, another provider or a no-op later)
    means writing a new implementation of this protocol, never touching the
    orchestration code that calls it.
    """

    def infer(self, topology: Topology, repo_path: Path) -> list[Journey]: ...
