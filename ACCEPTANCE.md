# Factory Acceptance Checklist

## Build and Static Checks

```bash
uv sync
uv run ruff check .
uv run basedpyright
uv run pytest
```

Without `uv`:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e . ruff basedpyright pytest
ruff check .
basedpyright
pytest
```

Acceptance:

- all commands exit 0;
- no type errors in changed source files;
- fixtures behave as expected.

## Positive Fixture

```bash
uv run ccwatermark fixtures/positive/minified.js
uv run ccwatermark --json fixtures/positive/minified.js
```

Acceptance:

- status is `detected`;
- output includes `env-anthropic-base-url`;
- output includes `china-timezone-pair`;
- output includes `today-date-template`;
- JSON is valid and contains `files[0].matches`.

## Negative Fixture

```bash
uv run ccwatermark fixtures/negative/plain.js
```

Acceptance:

- status is `clean`;
- no matched files are listed.

## Real Local Scan

```bash
uv run ccwatermark --no-logs ~/.local/share/claude/versions
```

Acceptance:

- command completes without crashing on 200MB+ binaries;
- matched files show version and modification time when path contains a version;
- output distinguishes `binary_capability` from `rendered_prompt`.

## CI/Automation Behavior

```bash
uv run ccwatermark --fail-on-detected fixtures/positive/minified.js
echo $?
```

Acceptance:

- exit code is `2` on detected marker evidence.

## Safety

Acceptance:

- no network calls;
- no file writes except normal Python cache/test artifacts;
- no modification of Claude Code installation;
- no proprietary code dumping beyond short bounded snippets.
