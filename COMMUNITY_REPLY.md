# Community Reply

Short version for Reddit/X:

```text
I put together a small local-only checker for the Claude Code prompt-watermark indicators being discussed:

https://github.com/brutoshi/claude-code-watermark-check

It scans local Claude Code logs/history first, and can also scan installed binaries for the reported marker-capability families. It does not upload logs, does not call Anthropic, and does not prove server-side receipt by itself.

If you run it, please share sanitized JSON results only:

ccwatermark --json

Before posting, redact private file paths, project names, hostnames, API gateway domains, and any prompt/log snippets that contain private data. Please do not paste private Claude logs or binary dumps.
```

When space is tight:

```text
Local-only checker for the Claude Code prompt-watermark indicators:
https://github.com/brutoshi/claude-code-watermark-check

If you try it, paste sanitized `ccwatermark --json` output only. Please redact paths, hostnames, project names, and private snippets. Local evidence does not by itself prove server-side receipt.
```
