#!/usr/bin/env python3
"""DFA-B3 static engagement-signal inventory; NO_DATA on consent and behavior."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re

SCHEMA = "preceptoros.lab.dfa-b3-static/1"
MAX_SOURCE_BYTES = 131072
MAX_FLAGS = 200

JS_RULES = {
    "notification_permission_call": re.compile(
        r"\b(?:window\s*\.\s*)?Notification\s*\.\s*requestPermission\s*\("),
    "notification_constructor": re.compile(r"\bnew\s+Notification\s*\("),
    "passive_reward_hook": re.compile(
        r"\brewardFor(?:Hover|Scroll|Dwell|Watch)\s*\("),
}


class MediaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines = []

    def handle_starttag(self, tag, attrs):
        if tag in ("audio", "video") and any(k == "autoplay" for k, _ in attrs):
            self.lines.append(self.getpos()[0])

    handle_startendtag = handle_starttag


def scan_text(source, source_type):
    if source_type not in ("html", "js", "mjs"):
        raise ValueError("unsupported_source_type")
    if not isinstance(source, str):
        raise ValueError("source_must_be_text")
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("source_byte_ceiling")
    flags = []
    if source_type == "html":
        parser = MediaParser()
        parser.feed(source)
        flags.extend({"rule": "media_autoplay", "line": i} for i in parser.lines)
    for rule, regex in JS_RULES.items():
        for match in regex.finditer(source):
            flags.append({"rule": rule, "line": source.count("\n", 0, match.start()) + 1})
    flags.sort(key=lambda row: (row["line"], row["rule"]))
    if len(flags) > MAX_FLAGS:
        return {"schema": SCHEMA, "state": "NO_DATA",
                "cause": "finding_count_exceeds_ceiling", "flags_count": len(flags),
                "flags": [], "scope": "STATIC_SIGNALS_ONLY"}
    return {"schema": SCHEMA,
            "state": "REVIEW_REQUIRED" if flags else "NO_DATA",
            "cause": "static_signals_need_consent_review" if flags
                     else "no_known_signals_consent_and_behavior_unverified",
            "flags_count": len(flags), "flags": flags,
            "engagement_restraint_score": None,
            "score_cause": "purpose_denominator_and_user_behavior_not_measured",
            "scope": "STATIC_SIGNALS_ONLY"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_file")
    args = parser.parse_args()
    path = Path(args.source_file)
    source_type = path.suffix.lower().lstrip(".")
    try:
        source = path.read_text(encoding="utf-8")
        result = scan_text(source, source_type)
        code = 0
    except (OSError, ValueError, UnicodeError) as exc:
        result = {"schema": SCHEMA, "state": "NO_DATA", "cause": type(exc).__name__,
                  "scope": "STATIC_SIGNALS_ONLY"}
        code = 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
