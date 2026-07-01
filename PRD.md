# PRD: Claude Code Watermark Check

## One-Line Product

A trustworthy local health check that tells developers whether their installed
Claude Code contains the reported China/proxy prompt-watermark logic, where it
was found, and when it first appeared on their machine.

## User

Primary user: developers and technical founders who run Claude Code locally,
especially through API gateways or proxies.

Secondary user: security reviewers who need a quick local triage artifact before
doing deeper reverse engineering.

## Problem

Public reports allege that Claude Code added hidden prompt-marker logic around
`ANTHROPIC_BASE_URL`, China timezone detection, Chinese proxy/lab hostnames, and
Unicode/date-format changes inside the `Today's date is ...` system-prompt line.

Users need a quick way to answer three questions:

1. Is the marker implementation present in my local Claude Code install?
2. Did any local logs/history contain a rendered marker?
3. What is the earliest local version and modification time where this appears?

## CEO Review Framing

The "10-star" version is not a panic blog post generator. It is a precise,
zero-network, reproducible local diagnostic that users can run before arguing
about intent. The product should make the evidence boundary obvious:

- local binary capability is evidence of client-side code presence;
- rendered prompt evidence is stronger local evidence of execution;
- neither alone proves server receipt.

This keeps the tool credible enough for GitHub readers, security engineers, and
founders deciding whether to keep using a gateway setup.

## Goals

- Detect the reported marker families in local Claude Code binaries.
- Detect rendered non-ASCII `Today's date is ...` markers in logs/history.
- Report matched file, signature id, evidence type, offset, snippet, version, and
  modification time.
- Report earliest local matched version and earliest local matched mtime.
- Provide human-readable and JSON output.
- Run without network access and without modifying local files.

## Non-Goals

- Do not bypass Claude Code protections.
- Do not deobfuscate or dump proprietary code.
- Do not claim server-side receipt without captured request evidence.
- Do not classify user nationality, identity, or location beyond local trigger
  hints required for this check.

## MVP Requirements

- CLI command: `ccwatermark`
- Optional paths; default scan targets common macOS Claude Code locations.
- `--json` output for automation.
- `--no-logs` for binary-only scans.
- `--fail-on-detected` for CI/MDM checks.
- File size limit guard with `--max-file-mb`.

## Health Status Logic

`detected`
: Core binary families are present together, or rendered prompt marker evidence
is found.

`suspicious`
: Two or more core binary families are present, but the complete implementation
is not established.

`clean`
: No meaningful marker families are found.

## Launch Checklist

- README explains evidence boundaries.
- Fixtures include a positive minified sample and a negative sample.
- Tests pass locally.
- Lint and type checks pass.
- Local scan against the maintainer's installed Claude Code completes and prints
  the first local version/time.

