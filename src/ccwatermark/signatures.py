from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final


@unique
class EvidenceKind(StrEnum):
    BINARY_CAPABILITY = "binary_capability"
    RENDERED_PROMPT = "rendered_prompt"


@unique
class MatchMode(StrEnum):
    ANY = "any"
    ALL = "all"


@unique
class SignatureFamily(StrEnum):
    BASE_URL = "base_url"
    FIRST_PARTY_GATE = "first_party_gate"
    CHINA_TIMEZONE = "china_timezone"
    APOSTROPHE_SELECTOR = "apostrophe_selector"
    DATE_RENDERER = "date_renderer"
    XOR_DECODER = "xor_decoder"
    CLASSIFIER_FIELDS = "classifier_fields"
    RENDERED_MARKER = "rendered_marker"


@dataclass(frozen=True, slots=True)
class Signature:
    id: str
    family: SignatureFamily
    kind: EvidenceKind
    description: str
    patterns: tuple[bytes, ...]
    mode: MatchMode = MatchMode.ANY


@dataclass(frozen=True, slots=True)
class RegexSignature:
    id: str
    family: SignatureFamily
    kind: EvidenceKind
    description: str
    pattern: re.Pattern[bytes]


SIGNATURES: Final[tuple[Signature, ...]] = (
    Signature(
        id="env-anthropic-base-url",
        family=SignatureFamily.BASE_URL,
        kind=EvidenceKind.BINARY_CAPABILITY,
        description="References ANTHROPIC_BASE_URL gateway/proxy routing.",
        patterns=(b"ANTHROPIC_BASE_URL",),
    ),
    Signature(
        id="first-party-base-url-gate",
        family=SignatureFamily.FIRST_PARTY_GATE,
        kind=EvidenceKind.BINARY_CAPABILITY,
        description="Contains first-party base URL bypass/gate logic.",
        patterns=(
            b"api.anthropic.com",
            b"_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL",
        ),
        mode=MatchMode.ANY,
    ),
    Signature(
        id="china-timezone-pair",
        family=SignatureFamily.CHINA_TIMEZONE,
        kind=EvidenceKind.BINARY_CAPABILITY,
        description="Checks Asia/Shanghai and Asia/Urumqi timezones.",
        patterns=(b"Asia/Shanghai", b"Asia/Urumqi"),
        mode=MatchMode.ALL,
    ),
    Signature(
        id="unicode-apostrophe-selector",
        family=SignatureFamily.APOSTROPHE_SELECTOR,
        kind=EvidenceKind.BINARY_CAPABILITY,
        description="Contains Unicode apostrophe variants used as marker bits.",
        patterns=(
            b"\\u2019",
            b"\\u02BC",
            b"\\u02B9",
            "\u2019".encode(),
            "\u02bc".encode(),
            "\u02b9".encode(),
        ),
        mode=MatchMode.ANY,
    ),
    Signature(
        id="today-date-template",
        family=SignatureFamily.DATE_RENDERER,
        kind=EvidenceKind.BINARY_CAPABILITY,
        description="Builds the Today[apostrophe]s date system-prompt line.",
        patterns=(b"Today${", b"s date is ${"),
        mode=MatchMode.ALL,
    ),
    Signature(
        id="date-slash-rewriter",
        family=SignatureFamily.DATE_RENDERER,
        kind=EvidenceKind.BINARY_CAPABILITY,
        description="Rewrites date separators from hyphen to slash.",
        patterns=(b'replaceAll("-","/")', b"replaceAll('-', '/')", b'replaceAll("-","/")'),
        mode=MatchMode.ANY,
    ),
    Signature(
        id="xor-base64-domain-decoder",
        family=SignatureFamily.XOR_DECODER,
        kind=EvidenceKind.BINARY_CAPABILITY,
        description="Contains base64 plus XOR decoder shape used for obfuscated lists.",
        patterns=(b"Buffer.from(", b'"base64"', b"String.fromCharCode", b"^"),
        mode=MatchMode.ALL,
    ),
    Signature(
        id="classifier-result-fields",
        family=SignatureFamily.CLASSIFIER_FIELDS,
        kind=EvidenceKind.BINARY_CAPABILITY,
        description="Contains known/labKw/cnTZ classifier result fields.",
        patterns=(b"known", b"labKw", b"cnTZ", b"host:null"),
        mode=MatchMode.ALL,
    ),
    Signature(
        id="rendered-marker-right-single-quote",
        family=SignatureFamily.RENDERED_MARKER,
        kind=EvidenceKind.RENDERED_PROMPT,
        description="Rendered prompt contains Today\u2019s date marker.",
        patterns=("Today\u2019s date is ".encode(),),
    ),
    Signature(
        id="rendered-marker-modifier-letter-apostrophe",
        family=SignatureFamily.RENDERED_MARKER,
        kind=EvidenceKind.RENDERED_PROMPT,
        description="Rendered prompt contains Today\u02bcs date marker.",
        patterns=("Today\u02bcs date is ".encode(),),
    ),
    Signature(
        id="rendered-marker-modifier-letter-prime",
        family=SignatureFamily.RENDERED_MARKER,
        kind=EvidenceKind.RENDERED_PROMPT,
        description="Rendered prompt contains Today\u02b9s date marker.",
        patterns=("Today\u02b9s date is ".encode(),),
    ),
)

REGEX_SIGNATURES: Final[tuple[RegexSignature, ...]] = (
    RegexSignature(
        id="rendered-marker-ascii-slash-date",
        family=SignatureFamily.RENDERED_MARKER,
        kind=EvidenceKind.RENDERED_PROMPT,
        description="Rendered prompt contains ASCII apostrophe with slash-form date.",
        pattern=re.compile(rb"Today's date is \d{4}/\d{2}/\d{2}\."),
    ),
    RegexSignature(
        id="rendered-marker-nonascii-date",
        family=SignatureFamily.RENDERED_MARKER,
        kind=EvidenceKind.RENDERED_PROMPT,
        description="Rendered prompt contains non-ASCII apostrophe date marker.",
        pattern=re.compile(
            "Today[\u2019\u02bc\u02b9]s date is \\d{4}[-/]\\d{2}[-/]\\d{2}\\.".encode()
        ),
    ),
)

CORE_BINARY_FAMILIES: Final[frozenset[SignatureFamily]] = frozenset(
    {
        SignatureFamily.BASE_URL,
        SignatureFamily.CHINA_TIMEZONE,
        SignatureFamily.APOSTROPHE_SELECTOR,
        SignatureFamily.DATE_RENDERER,
    }
)

LAB_KEYWORDS: Final[tuple[str, ...]] = (
    "deepseek",
    "moonshot",
    "minimax",
    "xaminim",
    "zhipu",
    "bigmodel",
    "baichuan",
    "stepfun",
    "01ai",
    "dashscope",
    "volces",
)
