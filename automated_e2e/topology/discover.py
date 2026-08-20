"""Find and parse whatever infra manifest describes a repo's service topology."""

from __future__ import annotations

from pathlib import Path

from automated_e2e.models import Topology
from automated_e2e.topology.base import TopologySource
from automated_e2e.topology.compose_parser import ComposeTopologySource

DEFAULT_SOURCES: list[TopologySource] = [ComposeTopologySource()]


class TopologyNotFoundError(Exception):
    pass


def discover_topology(
    repo_path: Path,
    sources: list[TopologySource] | None = None,
) -> Topology:
    for source in sources if sources is not None else DEFAULT_SOURCES:
        manifest_path = source.detect(repo_path)
        if manifest_path is not None:
            return source.parse(manifest_path)

    raise TopologyNotFoundError(
        f"No supported infra manifest found in {repo_path}. "
        "Currently supported: docker-compose. Kubernetes manifest support isn't implemented yet."
    )
