import json
from pathlib import Path
import subprocess
import sys

from pr_review_skill.models import Profile
from pr_review_skill.rendering import render_skill


def test_generated_findings_validator_accepts_valid_payload(tmp_path: Path) -> None:
    package = render_skill(
        Profile(
            repository_root=tmp_path,
            capabilities={},
            confirmed=True,
            adapter_ids=("local-git",),
        ),
        "copilot",
    )
    script = tmp_path / "validate_findings.py"
    script.write_text(package["scripts/validate_findings.py"], encoding="utf-8")
    findings = tmp_path / "findings.json"
    findings.write_text(
        json.dumps(
            [
                {
                    "id": "f-1",
                    "title": "Guard the empty path",
                    "severity": "medium",
                    "confidence": 0.9,
                    "category": "correctness",
                    "path": "src/example.py",
                    "start_line": 10,
                    "end_line": 10,
                    "side": "right",
                    "lenses": ["correctness"],
                    "issue": "The empty path reaches an invalid operation.",
                    "impact": "The request fails.",
                    "evidence": ["The changed branch has no empty guard."],
                    "recommendation": "Return a validation error before the operation.",
                    "provenance": [
                        {
                            "source": "diff",
                            "locator": "src/example.py:10",
                            "status": "observed",
                        }
                    ],
                    "validation": ["Reviewed the changed branch."],
                    "structural_key": "src/example.py|10-10|correctness|empty-path",
                    "deduplicated_against": [],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(script), str(findings)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "valid: 1 finding(s)" in result.stdout
