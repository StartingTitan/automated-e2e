from automated_e2e.models import Journey, Service, Topology
from automated_e2e.validation import validate_journeys


def _topology(*names: str) -> Topology:
    return Topology(services=[Service(name=n) for n in names])


def test_journey_with_all_known_services_is_kept_unchanged():
    topology = _topology("frontend", "order-service")
    journey = Journey(
        id="checkout",
        priority="high",
        steps=["login", "checkout"],
        services=["frontend", "order-service"],
    )
    [result] = validate_journeys([journey], topology)
    assert result.services == ["frontend", "order-service"]


def test_journey_with_hallucinated_service_has_it_stripped():
    topology = _topology("frontend", "order-service")
    journey = Journey(
        id="checkout",
        priority="high",
        steps=["login", "checkout"],
        services=["frontend", "made-up-service"],
    )
    [result] = validate_journeys([journey], topology)
    assert result.services == ["frontend"]


def test_journey_with_no_known_services_is_dropped_entirely():
    topology = _topology("frontend")
    journey = Journey(
        id="checkout",
        priority="high",
        steps=["login"],
        services=["made-up-service"],
    )
    assert validate_journeys([journey], topology) == []
