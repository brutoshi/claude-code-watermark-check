# Handoff: Claude Code Watermark Check

## Project

- Local directory: `/Users/huangbruce/Documents/AI/codex/claude-code-watermark-check`
- GitHub repo: https://github.com/brutoshi/claude-code-watermark-check
- GitHub tracking issue: https://github.com/brutoshi/claude-code-watermark-check/issues/1

This repository is a standalone open-source project for checking local Claude
Code prompt-watermark indicators.

## Current Status

- Public GitHub repo exists under `brutoshi/claude-code-watermark-check`.
- The first implementation has been committed and pushed to `main`.
- README has been rewritten for open-source release.
- Repo topics are set:
  `ai-agents`, `anthropic`, `claude-code`, `developer-tools`, `privacy`,
  `security`, `watermark`, `prompt-steganography`.
- GitHub Projects v2 board was not created because the current `gh` token lacks
  `read:project/project` scope.
- GitHub issue `#1` was created as the project tracking entry.

## What The Tool Does

The tool performs a local, read-only health check for Claude Code prompt-marker
evidence.

Primary evidence types:

- `rendered_prompt`: local Claude Code logs/history contain an already-rendered
  marker, such as a non-ASCII apostrophe in `Today's date is ...` or slash-form
  dates like `YYYY/MM/DD`.
- `binary_capability`: installed Claude Code binaries contain marker-generation
  code patterns associated with public reverse-engineering reports.

Important boundary:

- The tool can prove local evidence.
- It cannot prove Anthropic server receipt without captured network traffic or
  server-side records.

## Key Files

- `README.md`: public user-facing help file.
- `PRD.md`: product requirements and CEO/product framing.
- `IMPLEMENTATION.md`: scanner architecture and signature design.
- `ACCEPTANCE.md`: verification checklist.
- `src/ccwatermark/`: Python CLI implementation.
- `tests/test_scanner.py`: behavior coverage.
- `PROJECT_PROMPT.md`: copy-ready prompt for starting a fresh project/session.

## Verification Already Done

Earlier local verification passed:

- `ruff check .`
- `basedpyright`
- `pytest`
- positive fixture returns `detected`
- negative fixture returns `clean`
- `--fail-on-detected` exits with code `2`

Real local scan on this Mac previously found:

- `~/.local/share/claude/versions`: `detected`
- matched local versions: 5
- first local matched version: `2.1.138`
- first local matched mtime: `2026-05-09T15:02:52+08:00`
- `~/.claude` plus `~/Library/Logs/Claude`: `clean`

## Community/Launch Context

The README references current public discussion from:

- Reddit r/ClaudeCode
- Reddit r/ClaudeAI
- International Cyber Digest
- Techmeme
- TechNews
- Thereallo
- Vincent Schmalbach
- Anthropic docs

No mature open-source tool was found that specifically checks local Claude Code
logs for the reported prompt-watermark markers. Adjacent tools are mostly Claude
Code log viewers or usage dashboards.

## Recommended Next Steps

1. Add GitHub Actions for `ruff`, `basedpyright`, and `pytest`.
2. Add a screenshot or short terminal demo GIF to `README.md`.
3. Add simple install paths such as `pipx`, `uvx`, or PyPI after package naming
   is final.
4. Prepare Reddit/X reply text and ask users to share sanitized JSON output.
5. Collect false positives/false negatives from real-world scans.
6. If GitHub token Project scope is granted, create a GitHub Projects v2 board
   and add issue `#1`.

## Safety Notes

- Do not ask users to upload private Claude Code logs.
- Do not paste full binary dumps.
- Keep snippets bounded.
- Keep evidence language precise: local binary capability is not proof of
  server-side receipt.

