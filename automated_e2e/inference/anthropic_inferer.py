"""Infer user journeys from a service topology using Claude.

This is intentionally the thinnest possible version: it hands the model the
topology plus the repo's README and asks for journeys back as JSON. Richer
signal (route/controller extraction via tree-sitter, OpenAPI specs, existing
test files) is a follow-up — see the design discussion for the full pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import anthropic

from automated_e2e.models import Journey, Topology

DEFAULT_MODEL = "claude-sonnet-5"

_README_NAMES = ("README.md", "README.rst", "README.txt", "readme.md")
_README_CHAR_LIMIT = 4000

_SYSTEM_PROMPT = """\
You analyze a microservices repository's service topology and infer the \
end-to-end user journeys it likely supports (e.g. "user checkout", \
"password reset"). You will be given the discovered services (with their \
ports, environment variables, and dependencies) and the repo's README.

Respond with ONLY a JSON object of this exact shape, no prose, no markdown \
fences:

{
  "journeys": [
    {
      "id": "kebab-case-id",
      "priority": "high" | "medium" | "low",
      "steps": ["short imperative step", "..."],
      "services": ["service-name", "..."]
    }
  ]
}

Rules:
- Every entry in "services" MUST be one of the service names given to you.
  Never invent a service name.
- Order "steps" in the sequence a real user would perform them.
- Prioritize "high" for journeys that touch money, auth, or core business
  value; "low" for peripheral flows.
- If you cannot infer any journeys with reasonable confidence, return an
  empty "journeys" list rather than guessing.
"""


class AnthropicJourneyInferer:
    """JourneyInferer backed by the Anthropic Messages API."""

    def __init__(self, *, model: str = DEFAULT_MODEL, client: anthropic.Anthropic | None = None):
        self._model = model
        self._client = client or anthropic.Anthropic()

    def infer(self, topology: Topology, repo_path: Path) -> list[Journey]:
        prompt = self._build_prompt(topology, self._read_readme(repo_path))

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        data = self._parse_json(self._extract_text(response))
        return [Journey.model_validate(j) for j in data.get("journeys", [])]

    @staticmethod
    def _build_prompt(topology: Topology, readme: str | None) -> str:
        services_desc = "\n".join(
            f"- {s.name}: ports={s.ports or 'none'}, "
            f"depends_on={s.depends_on or 'none'}, "
            f"env_keys={sorted(s.environment.keys()) or 'none'}"
            for s in topology.services
        )
        readme_section = (
            f"\n\nREADME excerpt:\n{readme[:_README_CHAR_LIMIT]}" if readme else ""
        )
        return f"Services discovered:\n{services_desc}{readme_section}"

    @staticmethod
    def _read_readme(repo_path: Path) -> str | None:
        for name in _README_NAMES:
            candidate = repo_path / name
            if candidate.exists():
                return candidate.read_text(errors="ignore")
        return None

    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        return "".join(block.text for block in response.content if block.type == "text")

    @staticmethod
    def _parse_json(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.partition("\n")[2] if "\n" in text else text
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Model did not return valid JSON: {text!r}") from exc
