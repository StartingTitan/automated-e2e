# automated-e2e

Point it at a repo; it figures out what the repo does and produces a `system-model.json`
describing the user journeys the repo supports (steps + which services each hops through).
Selenium test generation and change-tracking build on top of this model — not implemented yet.

## Usage

```
pip install -e ".[dev]"

# requires ANTHROPIC_API_KEY for journey inference
automated-e2e analyze ./my-repository

# topology only, no LLM call / no API key needed
automated-e2e analyze ./my-repository --no-llm
```

## How `analyze` works

1. **Topology extraction** (`automated_e2e/topology/`) — parses `docker-compose.yml` to find
   services, ports, and dependencies (explicit `depends_on`, plus dependencies inferred from
   env vars like `ORDER_SERVICE_URL` that name another service).
2. **Journey inference** (`automated_e2e/llm.py`) — sends the topology + README to Claude and
   asks it to propose journeys matching the `system-model.json` schema.
3. **Validation** (`automated_e2e/analyze.py`) — strips any service the model hallucinated that
   doesn't actually exist in the topology; drops journeys left with no valid services.

Kubernetes manifest support and richer per-service code mapping (route/controller extraction)
are the next pieces — currently topology comes from `docker-compose.yml` only.

## Tests

```
pytest
```
