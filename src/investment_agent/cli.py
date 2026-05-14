from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .config import get_settings
from .graph.build import Pipeline, RunOptions
from .llm import get_provider
from .storage.repository import RunRepository, list_run_ids

app = typer.Typer(help="Multi-agent AI Infrastructure Investment Agent")
console = Console()


@app.command()
def run(
    provider: str = typer.Option("mock", "--provider", help="LLM provider: anthropic, openai, gemini, mock"),
    model: str | None = typer.Option(None, "--model", help="Model name (provider-specific)"),
    mock: bool = typer.Option(False, "--mock", help="Force mock provider (overrides --provider)"),
    max_components: int | None = typer.Option(None, "--max-components", help="Limit components for smoke tests"),
    output_dir: Path | None = typer.Option(None, "--output-dir"),
):
    """Run the full pipeline: decompose -> research -> score -> synthesize."""
    settings = get_settings()

    def _llm_factory():
        return get_provider(provider, model=model, mock=mock)

    def _progress(node: str, msg: str) -> None:
        console.print(f"[dim]{node}[/dim] {msg}")

    pipeline = Pipeline(settings=settings, llm_factory=_llm_factory, progress_cb=_progress)
    opts = RunOptions(
        provider=("mock" if mock else provider),
        model=model,
        mock=mock or provider == "mock",
        max_components=max_components,
        output_dir=output_dir,
    )
    result = pipeline.run(opts)

    console.rule(f"Run {result.run_id} complete")
    console.print(f"DB:       {result.db_path}")
    console.print(f"JSON:     {result.json_path}")
    console.print(f"Markdown: {result.markdown_path}")
    console.print(f"Cost:     ${result.state.cost_usd:.4f}")
    console.print(f"Companies scored: {len(result.state.scored)}")
    if result.state.errors:
        console.print(f"[red]Errors:[/red] {result.state.errors}")
        raise typer.Exit(code=1)


@app.command(name="list")
def list_cmd(
    output_dir: Path | None = typer.Option(None, "--output-dir"),
):
    """List runs in the output directory."""
    settings = get_settings()
    odir = output_dir or settings.run_output_dir
    ids = list_run_ids(odir)
    if not ids:
        console.print(f"No runs in {odir}")
        return
    table = Table(title=f"Runs in {odir}")
    table.add_column("run_id")
    table.add_column("provider")
    table.add_column("status")
    table.add_column("cost")
    table.add_column("companies")
    for rid in ids:
        try:
            repo = RunRepository(odir / f"{rid}.db")
            view = repo.get_view(rid)
            table.add_row(
                rid,
                view.run.provider,
                view.run.status,
                f"${view.run.cost_usd:.2f}",
                str(len(view.companies)),
            )
        except Exception:
            table.add_row(rid, "?", "?", "?", "?")
    console.print(table)


@app.command()
def show(
    run_id: str,
    output_dir: Path | None = typer.Option(None, "--output-dir"),
):
    """Show the top scored companies for a run."""
    settings = get_settings()
    odir = output_dir or settings.run_output_dir
    repo = RunRepository(odir / f"{run_id}.db")
    view = repo.get_view(run_id)

    table = Table(title=f"{run_id} — top companies")
    table.add_column("rank")
    table.add_column("company")
    table.add_column("ticker")
    table.add_column("component")
    table.add_column("share")
    table.add_column("sole?")
    table.add_column("score")
    ranked = sorted(
        view.companies,
        key=lambda c: (c.score.composite if c.score and c.score.composite is not None else -1),
        reverse=True,
    )
    comp_by_id = {c.id: c.name for c in view.components}
    for i, c in enumerate(ranked[:20], start=1):
        table.add_row(
            str(i),
            c.name,
            c.ticker or "",
            comp_by_id.get(c.component_id, "?"),
            c.market_share_bucket or "",
            "yes" if c.single_source else "no",
            f"{c.score.composite:.0f}" if c.score and c.score.composite is not None else "-",
        )
    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(app())
