# Copy-Ready Project Prompt

Paste this into a fresh Codex/ChatGPT project when continuing this work:

```text
You are continuing the standalone open-source project `claude-code-watermark-check`.

Local repo:
/Users/huangbruce/Documents/AI/codex/claude-code-watermark-check

GitHub repo:
https://github.com/brutoshi/claude-code-watermark-check

GitHub tracking issue:
https://github.com/brutoshi/claude-code-watermark-check/issues/1

Before making changes, read these files:
- HANDOFF.md
- README.md
- PRD.md
- IMPLEMENTATION.md
- ACCEPTANCE.md
- pyproject.toml
- src/ccwatermark/signatures.py
- src/ccwatermark/scanner.py
- src/ccwatermark/cli.py
- tests/test_scanner.py

Project goal:
Turn this into a credible open-source local health-check tool for Claude Code prompt-watermark indicators, focused on local logs first and binary capability second.

Current positioning:
- Not a generic Claude Code log viewer.
- Not a deobfuscator.
- A local-only security health check.
- No network upload.
- Clear evidence boundary: local rendered prompt evidence and local binary capability evidence do not by themselves prove server-side receipt.

Immediate next steps:
1. Add GitHub Actions for ruff, basedpyright, and pytest.
2. Add a screenshot or terminal demo GIF to README.md.
3. Add a short release/install section for pipx or uvx.
4. Improve README copy for Reddit/X sharing.
5. Prepare a concise community reply that links to the repo and asks users to paste sanitized JSON results.

Verification standard:
- Run ruff check .
- Run basedpyright
- Run pytest
- Manually run the CLI against fixtures/positive/minified.js and fixtures/negative/plain.js
- Keep the repo clean and push to GitHub when done.

Important constraints:
- Do not include private Claude logs in issues or docs.
- Do not dump proprietary Claude Code binary content.
- Keep snippets bounded.
- Avoid overclaiming: the tool checks local evidence only.
```

