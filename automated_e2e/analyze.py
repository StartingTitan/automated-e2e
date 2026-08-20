"""Orchestrates the analyze pipeline: topology extraction -> journey inference -> validation.

Depends only on the TopologySource and JourneyInferer abstractions, never on a
concrete backend (docker-compose vs. k8s, Anthropic vs. no-op) — the caller
(the CLI, as composition root) decides which implementations to inject.
"""

from __future__ import annotations

import logging
from pathlib import Path

from automated_e2e.inference import JourneyInferer
from automated_e2e.models import SystemModel
from automated_e2e.topology import TopologySource, discover_topology
from automated_e2e.validation import validate_journeys

logger = logging.getLogger(__name__)


def analyze_repo(
    repo_path: Path,
    journey_inferer: JourneyInferer,
    *,
    topology_sources: list[TopologySource] | None = None,
) -> SystemModel:
    topology = discover_topology(repo_path, topology_sources)
    logger.info("Discovered %d service(s): %s", len(topology.services), topology.service_names)

    journeys = journey_inferer.infer(topology, repo_path)
    journeys = validate_journeys(journeys, topology)
    return SystemModel(journeys=journeys)
