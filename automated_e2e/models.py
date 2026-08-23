"""Data models for the topology extracted from a repo and the system-model.json output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Service(BaseModel):
    """A single service discovered from infra manifests (docker-compose, k8s, ...)."""

    name: str
    image: str | None = None
    build_context: str | None = None
    ports: list[str] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class Topology(BaseModel):
    """The service graph for a repo, before any journeys have been inferred."""

    services: list[Service] = Field(default_factory=list)

    @property
    def service_names(self) -> list[str]:
        return [s.name for s in self.services]


class Journey(BaseModel):
    """A single user journey spanning one or more services."""

    id: str
    priority: Literal["high", "medium", "low"]
    steps: list[str]
    services: list[str]


class SystemModel(BaseModel):
    """The system-model.json output: the set of journeys a repo supports."""

    journeys: list[Journey] = Field(default_factory=list)
