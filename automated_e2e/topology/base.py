"""Abstraction for a strategy that can detect and parse one kind of infra manifest."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from automated_e2e.models import Topology


class TopologySource(Protocol):
    """A single source of topology info (docker-compose, k8s manifests, ...).

    Implementations must be substitutable for one another: `detect` returns the
    manifest path it found or None, and `parse` turns that path into a Topology.
    Adding a new source (e.g. Kubernetes) means writing a new implementation,
    never modifying the code that consumes this protocol.
    """

    def detect(self, repo_path: Path) -> Path | None: ...

    def parse(self, manifest_path: Path) -> Topology: ...
