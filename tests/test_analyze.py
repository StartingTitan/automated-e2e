from pathlib import Path

from automated_e2e.analyze import analyze_repo
from automated_e2e.inference import NullJourneyInferer

FIXTURE = Path(__file__).parent / "fixtures" / "sample-shop"


def test_null_inferer_yields_topology_only_with_no_journeys():
    system_model = analyze_repo(FIXTURE, NullJourneyInferer())
    assert system_model.journeys == []
