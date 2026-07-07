#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate markdown summary report from research-modern-ui results."""

import json
import re
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).parent
FIELDS_PATH = BASE / "fields.yaml"
RESULTS_DIR = BASE / "results"
REPORT_PATH = BASE / "report.md"

INTERNAL_FIELDS = {"_source_file", "uncertain"}

# Bidirectional category mapping (yaml name -> possible JSON nested keys)
CATEGORY_MAPPING = {
    "basic_info": ["basic_info", "Basic Info"],
    "code": ["code", "Code"],
    "design": ["design", "Design"],
    "applicability": ["applicability", "Applicability"],
}
NESTED_KEYS = {k for keys in CATEGORY_MAPPING.values() for k in keys}


def load_fields():
    data = yaml.safe_load(FIELDS_PATH.read_text(encoding="utf-8"))
    categories = []  # [(category_name, [field_names])]
    for cat in data.get("field_categories", []):
        names = [f["name"] for f in cat.get("fields", [])]
        categories.append((cat["category"], names))
    return categories


def flatten(data):
    """Support flat and nested JSON structures. Lookup: top level -> category keys -> any nested dict."""
    flat = {}
    for k, v in data.items():
        if k in INTERNAL_FIELDS:
            continue
        if k in NESTED_KEYS and isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 not in INTERNAL_FIELDS:
                    flat.setdefault(k2, v2)
        else:
            flat.setdefault(k, v)
    # traverse remaining nested dicts for any missed defined fields
    for v in data.values():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 not in INTERNAL_FIELDS:
                    flat.setdefault(k2, v2)
    return flat


def is_uncertain(name, value, uncertain_list):
    if name in uncertain_list:
        return True
    if value is None:
        return True
    if isinstance(value, str) and ("[uncertain]" in value or value.strip() == ""):
        return True
    return False


def fmt(value):
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(x, dict) for x in value):
            return "<br>".join(" | ".join(f"{k}: {v}" for k, v in d.items()) for d in value)
        if sum(len(str(x)) for x in value) < 100:
            return ", ".join(str(x) for x in value)
        return "<br>".join(f"- {x}" for x in value)
    if isinstance(value, dict):
        return "<br>".join(f"{k}: {fmt(v)}" for k, v in value.items())
    text = str(value).strip()
    if len(text) > 100:
        # blockquote-style: keep readable, preserve internal newlines
        text = text.replace("\r\n", "\n")
        return "\n\n> " + text.replace("\n", "\n> ")
    return text


def slugify_anchor(name):
    s = name.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s.strip())
    return s


def first_word(value, allowed):
    if not isinstance(value, str):
        return "?"
    m = re.match(r"\s*(\w+)", value)
    w = m.group(1).lower() if m else "?"
    return w if w in allowed else (value[:20] + "...") if len(value) > 20 else value


def main():
    categories = load_fields()
    defined_fields = {n for _, names in categories for n in names}

    items = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        flat = flatten(data)
        uncertain_list = data.get("uncertain", []) or []
        items.append((path.name, flat, uncertain_list))

    topic = yaml.safe_load((BASE / "outline.yaml").read_text(encoding="utf-8"))["topic"]

    lines = [f"# Research Report: {topic}", "", f"Items: {len(items)}  |  Generated from `results/` (uncertain values skipped)", "", "## Table of Contents", ""]

    for i, (fname, flat, unc) in enumerate(items, 1):
        name = str(flat.get("name", fname))
        short = name if len(name) <= 60 else name[:57] + "..."
        verdict = first_word(flat.get("recommended_action", ""), {"adopt", "adapt", "skip"})
        effort = first_word(flat.get("integration_effort", ""), {"low", "medium", "high"})
        lines.append(f"{i}. [{short}](#{slugify_anchor(short)}) - Verdict: **{verdict}** | Effort: {effort}")

    for fname, flat, unc in items:
        name = str(flat.get("name", fname))
        short = name if len(name) <= 60 else name[:57] + "..."
        lines += ["", "---", "", f"## {short}", ""]
        covered = set()
        for cat_name, field_names in categories:
            body = []
            for fn in field_names:
                covered.add(fn)
                if fn == "name":
                    continue
                v = flat.get(fn)
                if fn not in flat or is_uncertain(fn, v, unc):
                    continue
                body.append(f"**{fn}**: {fmt(v)}")
                body.append("")
            if body:
                lines.append(f"### {cat_name.replace('_', ' ').title()}")
                lines.append("")
                lines += body
        # extra fields
        extra = []
        for k, v in flat.items():
            if k in covered or k in INTERNAL_FIELDS or k in NESTED_KEYS:
                continue
            if is_uncertain(k, v, unc):
                continue
            extra.append(f"**{k}**: {fmt(v)}")
            extra.append("")
        if extra:
            lines.append("### Other Info")
            lines.append("")
            lines += extra
        if unc:
            lines.append("### Uncertain Fields (skipped)")
            lines.append("")
            for u in unc:
                lines.append(f"- {u}")
            lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH} ({len(items)} items)")


if __name__ == "__main__":
    main()
