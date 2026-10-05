#!/usr/bin/env python3
"""Deterministically validate a JSON array of normalized review findings."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


SEVERITIES = {"critical", "high", "medium", "low"}
PROVENANCE_STATUSES = {"observed", "reproduced", "inferred"}
REQUIRED = {
    "id",
    "title",
    "severity",
    "confidence",
    "category",
    "path",
    "start_line",
    "end_line",
    "side",
    "lenses",
    "issue",
    "impact",
    "evidence",
    "recommendation",
    "provenance",
    "validation",
    "structural_key",
    "deduplicated_against",
}


def validate_finding(value: Any, index: int) -> list[str]:
    prefix = f"[{index}]"
    if not isinstance(value, dict):
        return [f"{prefix} must be an object"]
    errors = [f"{prefix} missing {key}" for key in sorted(REQUIRED - value.keys())]
    if value.get("severity") not in SEVERITIES:
        errors.append(f"{prefix}.severity must be one of {sorted(SEVERITIES)}")
    confidence = value.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        errors.append(f"{prefix}.confidence must be numeric")
    elif not 0.0 <= confidence <= 1.0:
        errors.append(f"{prefix}.confidence must be between 0.0 and 1.0")
    start, end = value.get("start_line"), value.get("end_line")
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        errors.append(f"{prefix}.start_line must be a positive integer")
    if not isinstance(end, int) or isinstance(end, bool) or end < 1:
        errors.append(f"{prefix}.end_line must be a positive integer")
    if isinstance(start, int) and isinstance(end, int) and start > end:
        errors.append(f"{prefix}.start_line must not exceed end_line")
    if value.get("side") not in {"right", "general"}:
        errors.append(f"{prefix}.side must be right or general")
    for key in ("lenses", "evidence", "validation", "deduplicated_against"):
        if key in value and not isinstance(value[key], list):
            errors.append(f"{prefix}.{key} must be an array")
    provenance = value.get("provenance")
    if not isinstance(provenance, list) or not provenance:
        errors.append(f"{prefix}.provenance must be a non-empty array")
    else:
        for item_index, item in enumerate(provenance):
            if not isinstance(item, dict):
                errors.append(f"{prefix}.provenance[{item_index}] must be an object")
                continue
            missing = {"source", "locator", "status"} - item.keys()
            if missing:
                errors.append(
                    f"{prefix}.provenance[{item_index}] missing {', '.join(sorted(missing))}"
                )
            if item.get("status") not in PROVENANCE_STATUSES:
                errors.append(
                    f"{prefix}.provenance[{item_index}].status must be one of "
                    f"{sorted(PROVENANCE_STATUSES)}"
                )
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_findings.py FINDINGS.json", file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, list):
        print("error: document must be a JSON array", file=sys.stderr)
        return 1
    errors = [
        error
        for index, finding in enumerate(payload)
        for error in validate_finding(finding, index)
    ]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"valid: {len(payload)} finding(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
