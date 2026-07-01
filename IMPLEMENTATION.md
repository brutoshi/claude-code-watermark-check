# Engineering Implementation

## Architecture

The project is a small Python CLI:

- `ccwatermark.signatures`: static signature definitions and trigger keywords.
- `ccwatermark.scanner`: file discovery, chunked binary scanning, classification,
  version extraction, and JSON report shape.
- `ccwatermark.cli`: Typer command and Rich table output.

## Scanner Design

The scanner reads files in chunks with overlap, so 200MB+ packaged Claude Code
binaries can be scanned without loading every byte into memory. Each signature is
defined as either `any` or `all` pattern matching:

- `any`: one matching pattern is enough for that signature.
- `all`: every pattern in the signature must appear somewhere in the file.

This keeps weak strings such as `Buffer.from(` from becoming standalone proof
while still allowing minified symbol names to change between releases.

For text evidence files such as `.jsonl`, `.log`, `.md`, and `.txt`, the scanner
only runs rendered-prompt signatures. This prevents normal documentation strings
or smart quotes in chat history from being misclassified as binary marker logic.

## Signature Families

Core binary families:

- `base_url`: `ANTHROPIC_BASE_URL`
- `china_timezone`: `Asia/Shanghai` plus `Asia/Urumqi`
- `apostrophe_selector`: `\u2019`, `\u02BC`, `\u02B9`, or their UTF-8 forms
- `date_renderer`: template/date separator rewrite indicators

Supporting families:

- `first_party_gate`: first-party API host/bypass indicators
- `xor_decoder`: base64 plus XOR decoder shape
- `classifier_fields`: `known`, `labKw`, `cnTZ`, `host:null`
- `rendered_marker`: non-ASCII prompt line found in logs/history

Rendered prompt regexes also detect ASCII apostrophe plus slash-form dates, such
as `Today's date is 2026/06/30.`, because that is the marker shape produced when
only the China timezone bit is active.

## Local Time/Version Reporting

Version is extracted from common local paths such as:

- `~/.local/share/claude/versions/2.1.197`
- `~/Library/Application Support/Claude/claude-code-vm/2.1.149/claude`

The report includes:

- earliest matched semantic version, when available;
- earliest matched file modification time;
- source-level public baseline that external reports place introduction at
  Claude Code `2.1.91`.

## Privacy

The tool performs no network I/O. It reads local files and environment variables
only. For `ANTHROPIC_BASE_URL`, it reports the hostname, not the full URL.

## Known Limits

- Minified code changes can break literal signatures. The scanner therefore
  matches behavioral families rather than function names like `Vla` or `Zup`.
- Rendered prompt detection depends on local logs retaining system prompt text.
- The default domain list is not reimplemented because binary detection does not
  require deobfuscating Anthropic's full embedded list.
- Server receipt requires packet capture or server logs, which are outside this
  tool's scope.
