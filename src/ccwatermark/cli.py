from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from ccwatermark.scanner import ScannerConfig, ScanReport, ScanStatus, scan


def run(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(help="Files or directories to scan. Defaults to common Claude paths."),
    ] = None,
    *,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON."),
    ] = False,
    include_logs: Annotated[
        bool,
        typer.Option(
            "--include-logs/--no-logs",
            help="Include ~/.claude and ~/Library/Logs/Claude in default discovery.",
        ),
    ] = True,
    max_file_mb: Annotated[
        int,
        typer.Option("--max-file-mb", min=1, help="Skip files larger than this size."),
    ] = 300,
    fail_on_detected: Annotated[
        bool,
        typer.Option("--fail-on-detected", help="Exit 2 when the health check detects markers."),
    ] = False,
) -> None:
    report = scan(
        tuple(paths or ()),
        include_logs=include_logs,
        config=ScannerConfig(max_file_bytes=max_file_mb * 1024 * 1024),
    )
    if json_output:
        typer.echo(json.dumps(report.to_json(), ensure_ascii=False, indent=2))
    else:
        _render_report(report)

    if fail_on_detected and report.status is ScanStatus.DETECTED:
        raise typer.Exit(code=2)


def main() -> None:
    typer.run(run)


def _render_report(report: ScanReport) -> None:
    console = Console()
    color = {
        ScanStatus.CLEAN: "green",
        ScanStatus.SUSPICIOUS: "yellow",
        ScanStatus.DETECTED: "red",
    }[report.status]
    console.print(f"[bold {color}]Claude Code watermark health check: {report.status.value}[/]")

    summary = Table(show_header=False, box=None)
    summary.add_column("key", style="bold")
    summary.add_column("value")
    summary.add_row("matched files", str(len(report.matched_files)))
    summary.add_row("first local version", report.first_seen_version or "not found")
    summary.add_row("first local mtime", report.first_seen_mtime or "not found")
    summary.add_row("public baseline", report.public_baseline)
    summary.add_row(
        "current env",
        _format_environment(report),
    )
    console.print(summary)

    if not report.matched_files:
        return

    table = Table(title="Evidence")
    table.add_column("file")
    table.add_column("version")
    table.add_column("kind")
    table.add_column("signature")
    table.add_column("snippet")
    for file in report.matched_files:
        for match in file.matches:
            table.add_row(
                str(file.path),
                file.version or "-",
                match.kind.value,
                match.signature_id,
                match.snippet[:160],
            )
    console.print(table)


def _format_environment(report: ScanReport) -> str:
    env = report.environment
    host = env.anthropic_base_url_host or "unset"
    tz = ", ".join(env.timezone_candidates) or "unknown"
    hint = "possible trigger" if env.trigger_hint else "no trigger hint"
    return f"host={host}; tz={tz}; {hint}"

