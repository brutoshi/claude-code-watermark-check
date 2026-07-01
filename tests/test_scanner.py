from __future__ import annotations

from pathlib import Path

from ccwatermark.scanner import ScannerConfig, ScanStatus, extract_version, scan

ROOT = Path(__file__).resolve().parents[1]


def test_positive_fixture_is_detected() -> None:
    report = scan(
        [ROOT / "fixtures" / "positive" / "minified.js"],
        include_logs=False,
        config=ScannerConfig(),
    )

    assert report.status is ScanStatus.DETECTED
    assert report.matched_files[0].matches


def test_negative_fixture_is_clean() -> None:
    report = scan(
        [ROOT / "fixtures" / "negative" / "plain.js"],
        include_logs=False,
        config=ScannerConfig(),
    )

    assert report.status is ScanStatus.CLEAN
    assert not report.matched_files


def test_text_logs_only_match_rendered_markers(tmp_path: Path) -> None:
    log_file = tmp_path / "history.jsonl"
    log_file.write_text(
        "ANTHROPIC_BASE_URL appeared in docs, and someone\u2019s quote is normal text.",
        encoding="utf-8",
    )

    report = scan([log_file], include_logs=False, config=ScannerConfig())

    assert report.status is ScanStatus.CLEAN
    assert not report.matched_files


def test_claude_cache_paths_do_not_run_binary_signatures(tmp_path: Path) -> None:
    cache_file = tmp_path / ".claude" / "plugins" / "sample.ts"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("ANTHROPIC_BASE_URL and someone\u2019s quote", encoding="utf-8")

    report = scan([cache_file], include_logs=False, config=ScannerConfig())

    assert report.status is ScanStatus.CLEAN
    assert not report.matched_files


def test_rendered_ascii_slash_date_marker_is_detected(tmp_path: Path) -> None:
    log_file = tmp_path / "history.jsonl"
    log_file.write_text("system: Today's date is 2026/06/30.", encoding="utf-8")

    report = scan([log_file], include_logs=False, config=ScannerConfig())

    assert report.status is ScanStatus.DETECTED
    assert report.matched_files[0].matches[0].signature_id == "rendered-marker-ascii-slash-date"


def test_extracts_claude_version_from_common_paths() -> None:
    path = Path("/Users/example/.local/share/claude/versions/2.1.197")

    assert extract_version(path) == "2.1.197"


def test_json_report_is_serializable_shape() -> None:
    report = scan(
        [ROOT / "fixtures" / "positive" / "minified.js"],
        include_logs=False,
        config=ScannerConfig(),
    )

    data = report.to_json()
    assert data["status"] == "detected"
    assert data["files"]
