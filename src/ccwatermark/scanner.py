from __future__ import annotations

import os
import re
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, unique
from pathlib import Path
from urllib.parse import urlparse

from ccwatermark.signatures import (
    CORE_BINARY_FAMILIES,
    LAB_KEYWORDS,
    REGEX_SIGNATURES,
    SIGNATURES,
    EvidenceKind,
    MatchMode,
    RegexSignature,
    Signature,
    SignatureFamily,
)

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]

VERSION_RE = re.compile(
    r"(?:versions|claude-code|claude-code-vm)/(?P<version>\d+\.\d+\.\d+)"
)
SUSPICIOUS_CORE_FAMILY_THRESHOLD = 2
TEXT_EVIDENCE_ONLY_SUFFIXES = frozenset(
    {".json", ".jsonl", ".log", ".md", ".markdown", ".txt", ".yaml", ".yml"}
)


@unique
class ScanStatus(StrEnum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    DETECTED = "detected"


@dataclass(frozen=True, slots=True)
class SignatureMatch:
    signature_id: str
    family: SignatureFamily
    kind: EvidenceKind
    description: str
    offset: int
    snippet: str

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "signature_id": self.signature_id,
            "family": self.family.value,
            "kind": self.kind.value,
            "description": self.description,
            "offset": self.offset,
            "snippet": self.snippet,
        }


@dataclass(frozen=True, slots=True)
class FileReport:
    path: Path
    size_bytes: int
    mtime_epoch: float
    version: str | None
    matches: tuple[SignatureMatch, ...]
    skipped_reason: str | None = None

    @property
    def mtime_iso(self) -> str:
        return datetime.fromtimestamp(self.mtime_epoch, tz=UTC).astimezone().isoformat(
            timespec="seconds"
        )

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "mtime": self.mtime_iso,
            "version": self.version,
            "skipped_reason": self.skipped_reason,
            "matches": [match.to_json() for match in self.matches],
        }


@dataclass(frozen=True, slots=True)
class EnvironmentReport:
    anthropic_base_url_host: str | None
    custom_gateway_active: bool
    timezone_candidates: tuple[str, ...]
    china_timezone_active: bool
    host_contains_lab_keyword: bool

    @property
    def trigger_hint(self) -> bool:
        return self.custom_gateway_active and (
            self.china_timezone_active or self.host_contains_lab_keyword
        )

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "anthropic_base_url_host": self.anthropic_base_url_host,
            "custom_gateway_active": self.custom_gateway_active,
            "timezone_candidates": list(self.timezone_candidates),
            "china_timezone_active": self.china_timezone_active,
            "host_contains_lab_keyword": self.host_contains_lab_keyword,
            "trigger_hint": self.trigger_hint,
        }


@dataclass(frozen=True, slots=True)
class ScanReport:
    status: ScanStatus
    files: tuple[FileReport, ...]
    environment: EnvironmentReport
    public_baseline: str

    @property
    def matched_files(self) -> tuple[FileReport, ...]:
        return tuple(file for file in self.files if file.matches)

    @property
    def first_seen_version(self) -> str | None:
        versions = [file.version for file in self.matched_files if file.version is not None]
        if not versions:
            return None
        return min(versions, key=_semver_key)

    @property
    def first_seen_mtime(self) -> str | None:
        if not self.matched_files:
            return None
        file = min(self.matched_files, key=lambda item: item.mtime_epoch)
        return file.mtime_iso

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "status": self.status.value,
            "first_seen_version": self.first_seen_version,
            "first_seen_mtime": self.first_seen_mtime,
            "public_baseline": self.public_baseline,
            "environment": self.environment.to_json(),
            "files": [file.to_json() for file in self.files],
        }


@dataclass(frozen=True, slots=True)
class ScannerConfig:
    max_file_bytes: int = 300 * 1024 * 1024
    chunk_bytes: int = 1024 * 1024
    context_bytes: int = 72


@dataclass(slots=True)
class _FoundPattern:
    offset: int
    snippet: str


@dataclass(slots=True)
class _ScanState:
    literal_signatures: tuple[Signature, ...]
    regex_signatures: tuple[RegexSignature, ...]
    literal_found: dict[str, dict[bytes, _FoundPattern]]
    regex_found: dict[str, _FoundPattern]


def discover_default_paths(*, include_logs: bool) -> tuple[Path, ...]:
    home = Path.home()
    roots: list[Path] = [
        home / ".local" / "share" / "claude" / "versions",
        home / "Library" / "Application Support" / "Claude" / "claude-code",
        home / "Library" / "Application Support" / "Claude" / "claude-code-vm",
    ]
    if include_logs:
        roots.extend(
            [
                home / ".claude" / "history.jsonl",
                home / ".claude" / "projects",
                home / "Library" / "Logs" / "Claude",
            ]
        )
    return tuple(path for root in roots for path in _expand_root(root))


def scan(paths: Sequence[Path], *, include_logs: bool, config: ScannerConfig) -> ScanReport:
    target_paths = tuple(paths) if paths else discover_default_paths(include_logs=include_logs)
    files = tuple(scan_file(path, config=config) for path in _iter_files(target_paths))
    matched_families = _matched_families(files)
    return ScanReport(
        status=_classify(matched_families),
        files=files,
        environment=inspect_environment(),
        public_baseline=(
            "Public reverse-engineering reports place first observed introduction at "
            "Claude Code 2.1.91; this tool only reports local evidence."
        ),
    )


def scan_file(path: Path, *, config: ScannerConfig) -> FileReport:
    try:
        stat = path.stat()
    except OSError as error:
        return FileReport(
            path=path,
            size_bytes=0,
            mtime_epoch=0,
            version=extract_version(path),
            matches=(),
            skipped_reason=f"stat failed: {error}",
        )

    if not path.is_file():
        return FileReport(
            path=path,
            size_bytes=stat.st_size,
            mtime_epoch=stat.st_mtime,
            version=extract_version(path),
            matches=(),
            skipped_reason="not a regular file",
        )

    if stat.st_size > config.max_file_bytes:
        return FileReport(
            path=path,
            size_bytes=stat.st_size,
            mtime_epoch=stat.st_mtime,
            version=extract_version(path),
            matches=(),
            skipped_reason=f"larger than max_file_bytes={config.max_file_bytes}",
        )

    try:
        matches = _scan_bytes(path, config=config)
    except OSError as error:
        return FileReport(
            path=path,
            size_bytes=stat.st_size,
            mtime_epoch=stat.st_mtime,
            version=extract_version(path),
            matches=(),
            skipped_reason=f"read failed: {error}",
        )

    return FileReport(
        path=path,
        size_bytes=stat.st_size,
        mtime_epoch=stat.st_mtime,
        version=extract_version(path),
        matches=matches,
    )


def extract_version(path: Path) -> str | None:
    normalized = path.as_posix()
    match = VERSION_RE.search(normalized)
    if match is None:
        return None
    return match.group("version")


def inspect_environment() -> EnvironmentReport:
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    parsed_host = urlparse(base_url).hostname if base_url else None
    host = parsed_host.lower() if parsed_host is not None else None
    custom_gateway = host is not None and host != "api.anthropic.com"
    timezones = _timezone_candidates()
    china_tz = any(value in {"Asia/Shanghai", "Asia/Urumqi"} for value in timezones)
    lab_keyword = host is not None and any(keyword in host for keyword in LAB_KEYWORDS)
    return EnvironmentReport(
        anthropic_base_url_host=host,
        custom_gateway_active=custom_gateway,
        timezone_candidates=timezones,
        china_timezone_active=china_tz,
        host_contains_lab_keyword=lab_keyword,
    )


def _scan_bytes(path: Path, *, config: ScannerConfig) -> tuple[SignatureMatch, ...]:
    literal_signatures, regex_signatures = _signatures_for_path(path)
    state = _ScanState(
        literal_signatures=literal_signatures,
        regex_signatures=regex_signatures,
        literal_found={signature.id: {} for signature in literal_signatures},
        regex_found={},
    )
    pattern_lengths = [
        len(pattern) for signature in literal_signatures for pattern in signature.patterns
    ]
    max_pattern = max([*pattern_lengths, 128])
    tail_keep = max(max_pattern + config.context_bytes, max_pattern)
    offset = 0
    tail = b""

    with path.open("rb") as file:
        while chunk := file.read(config.chunk_bytes):
            data = tail + chunk
            base_offset = offset - len(tail)
            _record_matches(
                data,
                base_offset,
                state,
                config.context_bytes,
            )
            offset += len(chunk)
            tail = data[-tail_keep:]

    matches: list[SignatureMatch] = []
    for signature in literal_signatures:
        pattern_hits = state.literal_found[signature.id]
        if not _signature_matched(signature, pattern_hits):
            continue
        first_hit = min(pattern_hits.values(), key=lambda hit: hit.offset)
        matches.append(
            SignatureMatch(
                signature_id=signature.id,
                family=signature.family,
                kind=signature.kind,
                description=signature.description,
                offset=first_hit.offset,
                snippet=first_hit.snippet,
            )
        )
    for signature in regex_signatures:
        first_hit = state.regex_found.get(signature.id)
        if first_hit is None:
            continue
        matches.append(
            SignatureMatch(
                signature_id=signature.id,
                family=signature.family,
                kind=signature.kind,
                description=signature.description,
                offset=first_hit.offset,
                snippet=first_hit.snippet,
            )
        )
    return tuple(matches)


def _record_matches(
    data: bytes,
    base_offset: int,
    state: _ScanState,
    context_bytes: int,
) -> None:
    for signature in state.literal_signatures:
        signature_hits = state.literal_found[signature.id]
        for pattern in signature.patterns:
            if pattern in signature_hits:
                continue
            index = data.find(pattern)
            if index < 0:
                continue
            signature_hits[pattern] = _FoundPattern(
                offset=base_offset + index,
                snippet=_snippet(data, index, len(pattern), context_bytes),
            )
    for signature in state.regex_signatures:
        if signature.id in state.regex_found:
            continue
        match = signature.pattern.search(data)
        if match is None:
            continue
        state.regex_found[signature.id] = _FoundPattern(
            offset=base_offset + match.start(),
            snippet=_snippet(data, match.start(), match.end() - match.start(), context_bytes),
        )


def _signature_matched(signature: Signature, hits: dict[bytes, _FoundPattern]) -> bool:
    match signature.mode:
        case MatchMode.ANY:
            return bool(hits)
        case MatchMode.ALL:
            return len(hits) == len(signature.patterns)


def _signatures_for_path(path: Path) -> tuple[tuple[Signature, ...], tuple[RegexSignature, ...]]:
    rendered_literals = tuple(
        signature for signature in SIGNATURES if signature.kind is EvidenceKind.RENDERED_PROMPT
    )
    if _is_text_evidence_path(path):
        return rendered_literals, REGEX_SIGNATURES
    return SIGNATURES, REGEX_SIGNATURES


def _is_text_evidence_path(path: Path) -> bool:
    normalized = path.expanduser().as_posix()
    return (
        path.suffix.lower() in TEXT_EVIDENCE_ONLY_SUFFIXES
        or "/.claude/" in normalized
        or "/Library/Logs/Claude/" in normalized
    )


def _snippet(data: bytes, index: int, pattern_len: int, context_bytes: int) -> str:
    start = max(0, index - context_bytes)
    end = min(len(data), index + pattern_len + context_bytes)
    text = data[start:end].decode("utf-8", errors="replace")
    return " ".join(text.replace("\x00", " ").split())


def _iter_files(paths: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for path in paths:
        expanded = path.expanduser()
        candidates = expanded.rglob("*") if expanded.is_dir() else (expanded,)
        for candidate in candidates:
            try:
                identity = candidate.resolve(strict=False)
            except OSError:
                identity = candidate
            if identity in seen:
                continue
            seen.add(identity)
            yield candidate


def _expand_root(root: Path) -> Iterable[Path]:
    if not root.exists():
        return ()
    if root.is_file():
        return (root,)
    return tuple(root.rglob("*"))


def _matched_families(files: Iterable[FileReport]) -> frozenset[SignatureFamily]:
    return frozenset(match.family for file in files for match in file.matches)


def _classify(families: frozenset[SignatureFamily]) -> ScanStatus:
    if SignatureFamily.RENDERED_MARKER in families:
        return ScanStatus.DETECTED
    if families >= CORE_BINARY_FAMILIES:
        return ScanStatus.DETECTED
    if len(CORE_BINARY_FAMILIES & families) >= SUSPICIOUS_CORE_FAMILY_THRESHOLD:
        return ScanStatus.SUSPICIOUS
    return ScanStatus.CLEAN


def _semver_key(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def _timezone_candidates() -> tuple[str, ...]:
    values: list[str] = []
    tz_env = os.environ.get("TZ")
    if tz_env:
        values.append(tz_env)

    try:
        link = str(Path("/etc/localtime").readlink())
    except OSError:
        link = ""
    marker = "zoneinfo/"
    if marker in link:
        values.append(link.split(marker, maxsplit=1)[1])

    values.extend(value for value in time.tzname if value)
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return tuple(deduped)
