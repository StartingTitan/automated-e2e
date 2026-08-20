"""Guards journeys against referencing services that don't actually exist in the topology."""

from __future__ import annotations

import logging

from automated_e2e.models import Journey, Topology

logger = logging.getLogger(__name__)


def validate_journeys(journeys: list[Journey], topology: Topology) -> list[Journey]:
    known = set(topology.service_names)
    validated: list[Journey] = []

    for journey in journeys:
        unknown = [s for s in journey.services if s not in known]
        if unknown:
            logger.warning(
                "Journey %r references unknown service(s) %s; dropping them.",
                journey.id,
                unknown,
            )
        kept_services = [s for s in journey.services if s in known]
        if not kept_services:
            logger.warning("Journey %r has no valid services left; discarding it.", journey.id)
            continue
        validated.append(journey.model_copy(update={"services": kept_services}))

    return validated
