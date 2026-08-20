from pathlib import Path

from automated_e2e.topology.discover import discover_topology

FIXTURE = Path(__file__).parent / "fixtures" / "sample-shop"


def test_discovers_all_services():
    topology = discover_topology(FIXTURE)
    assert sorted(topology.service_names) == ["frontend", "order-service", "payment-service"]


def test_explicit_depends_on_is_kept():
    topology = discover_topology(FIXTURE)
    order_service = next(s for s in topology.services if s.name == "order-service")
    assert "payment-service" in order_service.depends_on


def test_implicit_dependency_from_env_var_is_inferred():
    topology = discover_topology(FIXTURE)
    frontend = next(s for s in topology.services if s.name == "frontend")
    # frontend has no explicit depends_on, only an env var referencing order-service
    assert "order-service" in frontend.depends_on


def test_image_only_service_is_parsed():
    topology = discover_topology(FIXTURE)
    payment_service = next(s for s in topology.services if s.name == "payment-service")
    assert payment_service.image == "sample/payment-service:latest"
    assert payment_service.build_context is None


def test_ports_are_captured():
    topology = discover_topology(FIXTURE)
    frontend = next(s for s in topology.services if s.name == "frontend")
    assert frontend.ports == ["3000:3000"]
