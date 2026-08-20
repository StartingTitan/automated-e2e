"""Build a Topology from a docker-compose file."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from automated_e2e.models import Service, Topology

_COMPOSE_FILENAMES = (
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
)


class ComposeTopologySource:
    """TopologySource backed by a docker-compose file."""

    def detect(self, repo_path: Path) -> Path | None:
        for filename in _COMPOSE_FILENAMES:
            candidate = repo_path / filename
            if candidate.exists():
                return candidate
        return None

    def parse(self, manifest_path: Path) -> Topology:
        return parse_compose_file(manifest_path)


def parse_compose_file(path: Path) -> Topology:
    raw = yaml.safe_load(path.read_text()) or {}
    services_raw = raw.get("services") or {}

    services = [
        Service(
            name=name,
            image=spec.get("image"),
            build_context=_parse_build(spec.get("build")),
            ports=[str(p) for p in (spec.get("ports") or [])],
            environment=_parse_environment(spec.get("environment")),
            depends_on=_parse_depends_on(spec.get("depends_on")),
        )
        for name, spec in services_raw.items()
        for spec in [spec or {}]
    ]

    topology = Topology(services=services)
    _infer_implicit_dependencies(topology)
    return topology


def _parse_build(build: object) -> str | None:
    if isinstance(build, str):
        return build
    if isinstance(build, dict):
        context = build.get("context")
        return str(context) if context is not None else None
    return None


def _parse_environment(environment: object) -> dict[str, str]:
    if environment is None:
        return {}
    if isinstance(environment, dict):
        return {str(k): str(v) for k, v in environment.items()}
    if isinstance(environment, list):
        result: dict[str, str] = {}
        for entry in environment:
            key, _, value = str(entry).partition("=")
            result[key] = value
        return result
    return {}


def _parse_depends_on(depends_on: object) -> list[str]:
    if depends_on is None:
        return []
    if isinstance(depends_on, list):
        return [str(d) for d in depends_on]
    if isinstance(depends_on, dict):
        return list(depends_on.keys())
    return []


def _infer_implicit_dependencies(topology: Topology) -> None:
    """Catch dependencies expressed only as a hostname in an env var (e.g. a *_URL pointing
    at another service), which docker-compose's own `depends_on` often misses or omits."""
    names = topology.service_names
    for service in topology.services:
        referenced = set(service.depends_on)
        for value in service.environment.values():
            for other in names:
                if other == service.name:
                    continue
                if re.search(rf"(?<![\w-]){re.escape(other)}(?![\w-])", value):
                    referenced.add(other)
        service.depends_on = sorted(referenced)
