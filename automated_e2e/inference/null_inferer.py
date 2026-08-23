"""No-op JourneyInferer for `--no-llm` runs: topology only, no journeys."""

from __future__ import annotations

from pathlib import Path

from automated_e2e.models import Journey, Topology


class NullJourneyInferer:
    def infer(self, topology: Topology, repo_path: Path) -> list[Journey]:
        return []
