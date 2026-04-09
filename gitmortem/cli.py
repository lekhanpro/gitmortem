from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from gitmortem import __version__
from gitmortem.blast_radius import blast_radius_summary, find_dependents
from gitmortem.config import (
    ConfigError,
    build_llm_settings,
    resolve_output_directory,
    validate_llm_settings,
)
from gitmortem.diff_parser import parse_diff, summarize_diff_for_llm
from gitmortem.git_analyzer import (
    GitAnalyzerError,
    extract_commit,
    get_raw_diff,
    get_surrounding_commits,
)
from gitmortem.llm import LLMOrchestrationError, run_checklist, run_root_cause, run_timeline
from gitmortem.renderer import render_html, render_markdown, render_offline_markdown
from gitmortem.timeline import fallback_timeline

console = Console()
app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    help="Because someone has to explain what you broke.",
)
REPO_HELP = "Path to the git repository."
OUTPUT_HELP = "Write markdown report to this file."
HTML_HELP = "Also write a standalone HTML report."
HTML_OUTPUT_HELP = "Path for the HTML report."
NO_LLM_HELP = "Skip AI analysis and render a deterministic report."
PROVIDER_HELP = "LLM provider: groq, openai, anthropic, openrouter, ollama, compatible."
MODEL_HELP = "Override the provider default model."
BASE_URL_HELP = "Custom base URL for compatible providers."
WINDOW_HELP = "Commit history window for timeline reconstruction."


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"gitmortem {__version__}")
        raise typer.Exit()


@app.command()
def postmortem(
    commit_hash: str = typer.Argument(..., help="Commit hash to analyze."),
    repo: Path = typer.Option(Path("."), "--repo", "-r", help=REPO_HELP),
    output: Path | None = typer.Option(None, "--output", "-o", help=OUTPUT_HELP),
    html: bool = typer.Option(False, "--html", help=HTML_HELP),
    html_output: Path | None = typer.Option(None, "--html-output", help=HTML_OUTPUT_HELP),
    no_llm: bool = typer.Option(False, "--no-llm", help=NO_LLM_HELP),
    provider: str | None = typer.Option(None, "--provider", help=PROVIDER_HELP),
    model: str | None = typer.Option(None, "--model", help=MODEL_HELP),
    api_key: str | None = typer.Option(None, "--api-key", help="Inline API key override."),
    base_url: str | None = typer.Option(None, "--base-url", help=BASE_URL_HELP),
    window: int = typer.Option(10, "--window", help=WINDOW_HELP),
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True),
) -> None:
    del version

    try:
        repo_path = repo.expanduser().resolve()

        with Progress(
            SpinnerColumn(), TextColumn("{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Extracting commit facts...", total=None)
            commit_fact = extract_commit(str(repo_path), commit_hash)

            progress.update(task, description="Parsing diff...")
            raw_diff = get_raw_diff(str(repo_path), commit_hash)
            file_diffs = parse_diff(raw_diff)
            diff_summary = summarize_diff_for_llm(file_diffs)

            progress.update(task, description="Calculating blast radius...")
            dependents = find_dependents(commit_fact.repo_root, commit_fact.files_changed)
            blast_text = blast_radius_summary(dependents)

            progress.update(task, description="Reconstructing timeline...")
            surrounding = get_surrounding_commits(str(repo_path), commit_hash, window=window)
            fallback = fallback_timeline(commit_fact, surrounding)

            if no_llm:
                progress.update(task, description="Rendering offline report...")
                report = render_offline_markdown(commit_fact, diff_summary, blast_text, fallback)
            else:
                progress.update(task, description="Preparing LLM provider...")
                settings = build_llm_settings(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    base_url=base_url,
                )
                validate_llm_settings(settings)

                progress.update(task, description="Analyzing root cause...")
                root_cause = run_root_cause(settings, commit_fact, diff_summary, blast_text)

                progress.update(task, description="Reconstructing AI timeline...")
                llm_timeline = run_timeline(settings, commit_fact, surrounding)
                timeline = llm_timeline if llm_timeline.get("timeline") else fallback

                progress.update(task, description="Generating never-again checklist...")
                checklist = run_checklist(settings, root_cause, commit_fact)

                progress.update(task, description="Rendering postmortem...")
                report = render_markdown(
                    commit_fact=commit_fact,
                    diff_summary=diff_summary,
                    root_cause=root_cause,
                    timeline=timeline,
                    checklist=checklist,
                    blast_radius_text=blast_text,
                )

            progress.update(task, description="Done.", completed=True)

        markdown_output_path = _resolve_markdown_output_path(output)
        if markdown_output_path:
            markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
            markdown_output_path.write_text(report, encoding="utf-8")
            console.print(f"[green]Markdown report written to {markdown_output_path}[/green]")

        if html:
            html_report = render_html(report, f"gitmortem {commit_fact.short_hash}")
            resolved_html_output = _resolve_html_output_path(
                html_output, markdown_output_path, commit_fact.short_hash
            )
            resolved_html_output.parent.mkdir(parents=True, exist_ok=True)
            resolved_html_output.write_text(html_report, encoding="utf-8")
            console.print(f"[green]HTML report written to {resolved_html_output}[/green]")

        console.print(Markdown(report))
    except (ConfigError, GitAnalyzerError, LLMOrchestrationError, RuntimeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc


def _resolve_markdown_output_path(output: Path | None) -> Path | None:
    if output:
        return output.expanduser().resolve()
    return None


def _resolve_html_output_path(
    html_output: Path | None,
    markdown_output: Path | None,
    short_hash: str,
) -> Path:
    if html_output:
        return html_output.expanduser().resolve()
    if markdown_output:
        return markdown_output.with_suffix(".html")
    return resolve_output_directory() / f"gitmortem-{short_hash}.html"


def run() -> None:
    app()
