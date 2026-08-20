from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from automated_e2e.analyze import analyze_repo
from automated_e2e.inference import DEFAULT_MODEL, AnthropicJourneyInferer, NullJourneyInferer
from automated_e2e.topology import TopologyNotFoundError

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.callback()
def _callback() -> None:
    """automated-e2e: analyze a repo and generate/maintain Selenium E2E tests."""


@app.command()
def analyze(
    repo_path: Annotated[Path, typer.Argument(help="Path to the repository to analyze.")],
    out: Annotated[
        Path, typer.Option("--out", "-o", help="Where to write the system model.")
    ] = Path("system-model.json"),
    no_llm: Annotated[
        bool,
        typer.Option("--no-llm", help="Skip LLM journey inference; emit topology only."),
    ] = False,
    model: Annotated[str, typer.Option(help="Anthropic model to use for inference.")] = DEFAULT_MODEL,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Analyze a repository and produce a system-model.json of its user journeys."""
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, format="%(message)s")

    repo_path = repo_path.resolve()
    if not repo_path.is_dir():
        console.print(f"[red]Not a directory:[/red] {repo_path}")
        raise typer.Exit(code=1)

    journey_inferer = NullJourneyInferer() if no_llm else AnthropicJourneyInferer(model=model)
    try:
        system_model = analyze_repo(repo_path, journey_inferer)
    except TopologyNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None

    out.write_text(json.dumps(system_model.model_dump(), indent=2) + "\n")
    console.print(f"[green]Wrote {len(system_model.journeys)} journey(s) to {out}[/green]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
