# automated-e2e

An AI tool for microservices repos: point it at one and it should understand what the
repo does, generate Selenium end-to-end tests for it, and — when the repo changes — update
those tests automatically and document why. That's the full vision.

**Current state: only the first stage exists.** `automated-e2e analyze <repo>` looks at a
repo and produces a `system-model.json` describing the user journeys it supports (e.g.
"user checkout": login → add to cart → pay, spanning `frontend` → `order-service` →
`payment-service`). Test generation and change-tracking are not built yet — see
[What's not built yet](#whats-not-built-yet).

## Setup

Requires Python 3.10+ (the system Python on this machine was 3.8, EOL — installed 3.12 via
Homebrew for this project instead).

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Usage

```bash
# full run: topology extraction + LLM journey inference (needs ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
.venv/bin/automated-e2e analyze ./my-repository

# topology only, no LLM call, no API key needed
.venv/bin/automated-e2e analyze ./my-repository --no-llm

# other flags
.venv/bin/automated-e2e analyze ./my-repository --out custom-name.json --model claude-sonnet-5 -v
```

Writes `system-model.json` to the current directory (or wherever `--out` points), shaped like:

```json
{
  "journeys": [
    {
      "id": "user-checkout",
      "priority": "high",
      "steps": ["login", "select product", "add product to cart", "checkout", "verify order"],
      "services": ["frontend", "order-service", "payment-service"]
    }
  ]
}
```

## How `analyze` works

1. **Topology extraction** (`automated_e2e/topology/`) — finds and parses a `docker-compose.yml`
   to get services, ports, and dependencies: explicit `depends_on`, plus dependencies inferred
   from env vars that name another service (e.g. `ORDER_SERVICE_URL=http://order-service:8080`
   implies frontend depends on order-service, even with no `depends_on` entry).
2. **Journey inference** (`automated_e2e/inference/`) — sends the topology + repo README to
   Claude and asks it to propose journeys matching the schema above.
3. **Validation** (`automated_e2e/validation.py`) — strips any service the model hallucinated
   that doesn't actually exist in the topology, and drops journeys left with no valid services.

Topology extraction and validation are deterministic and fully tested. Journey inference quality
depends on the model and how much the README/topology actually reveals about the repo's purpose
— it's the weakest link right now, since it doesn't yet read any actual application code.

### Architecture

Both extension points in the pipeline are behind small `Protocol` abstractions rather than
hardcoded, so the next pieces (Kubernetes manifests, richer code-derived journey signal) can be
added without touching existing code:

- `topology.TopologySource` — `ComposeTopologySource` is the only implementation today;
  `discover_topology()` tries each registered source in turn.
- `inference.JourneyInferer` — `AnthropicJourneyInferer` (real inference) and
  `NullJourneyInferer` (used for `--no-llm`) are interchangeable; `cli.py` picks one.

`analyze.py` only depends on these two abstractions plus `validation.py` — it has no
knowledge of docker-compose or Anthropic specifically.

```
automated_e2e/
  models.py              Service, Topology, Journey, SystemModel (pydantic)
  topology/
    base.py               TopologySource protocol
    compose_parser.py      parse_compose_file() + ComposeTopologySource
    discover.py             discover_topology() — tries each registered source
  inference/
    base.py               JourneyInferer protocol
    anthropic_inferer.py    AnthropicJourneyInferer — Claude-backed
    null_inferer.py         NullJourneyInferer — for --no-llm
  validation.py           validate_journeys() — drops hallucinated services/journeys
  analyze.py             orchestrates: discover -> infer -> validate
  cli.py                  Typer CLI; composition root that wires concrete implementations
```

## Tests

```bash
.venv/bin/pytest -v
```

15 tests, all passing, no API key required (the Anthropic client is mocked). Covers the compose
parser, implicit-dependency inference, topology source extensibility, the validation guardrail,
and the inferer's JSON-response parsing (including markdown-fenced responses).

There's also a fixture repo at `tests/fixtures/sample-shop/` (a bare `docker-compose.yml` with
`frontend` → `order-service` → `payment-service`) used by the tests and handy for manual CLI
smoke-testing.

### Manually verified against a real repo

Ran `analyze --no-llm` against a real 11-service repo (`microsvc-master`, a banking app with
Spring Boot services, Postgres, Redis, a gRPC fraud-detection service, and an observability
stack). Correctly discovered all 11 services and their dependencies, including implicit ones
inferred purely from `*_SERVICE_URL` / `OTEL_EXPORTER_OTLP_ENDPOINT` env vars that had no
matching `depends_on` entry.

## What's not built yet

- **Kubernetes manifest support** — topology only comes from `docker-compose.yml` right now.
- **Code-derived journey signal** — journey inference currently only sees the topology and
  README, not actual routes/controllers/OpenAPI specs. This is the biggest gap in inference
  quality.
- **Selenium test generation** from `system-model.json`.
- **Change detection & auto-update** — re-running `analyze` after a repo changes, diffing
  against the previous `system-model.json`, regenerating affected tests, and documenting why.
