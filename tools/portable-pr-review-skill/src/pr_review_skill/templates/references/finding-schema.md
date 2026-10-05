# Finding schema

Use one normalized object per finding.

```json
{
  "id": "stable-local-id",
  "title": "Imperative, specific title",
  "severity": "critical",
  "confidence": 0.0,
  "category": "correctness",
  "path": "normalized/repository/path.ext",
  "start_line": 1,
  "end_line": 1,
  "side": "right",
  "lenses": ["correctness"],
  "issue": "What is wrong",
  "impact": "Concrete failure or risk",
  "evidence": ["Observed fact with source"],
  "recommendation": "Smallest safe next step",
  "provenance": [
    {"source": "diff", "locator": "path:line", "status": "observed"}
  ],
  "validation": ["Command, check, or reasoning performed"],
  "structural_key": "path|start-end|category|root-cause",
  "deduplicated_against": []
}
```

## Severity

- `critical`: likely immediate compromise, irreversible loss, or broad production outage.
- `high`: likely major correctness, security, data, or availability failure.
- `medium`: material defect or regression with bounded impact or workaround.
- `low`: real, actionable defect with limited impact.

Severity measures impact and likelihood, not certainty. Do not add informational or nit
severities; omit non-material advice from findings.

## Confidence

Use a number from `0.0` through `1.0`.

- `0.90–1.00`: directly observed or deterministically reproduced.
- `0.70–0.89`: strong code evidence with limited assumptions.
- `0.50–0.69`: plausible and material but dependent on an unverified condition.
- Below `0.50`: do not publish as a finding; gather evidence or omit it.

## Provenance

Each item has `source`, `locator`, and `status`. Status is one of:

- `observed`: directly present in a source;
- `reproduced`: demonstrated by a deterministic check;
- `inferred`: reasoned from stated assumptions.

Never describe inferred evidence as observed.

## Structural deduplication

Normalize path separators, line ranges, category, and a short root-cause token. Findings are
duplicates when they concern the same root cause and their locations overlap or are inseparable.
Merge lenses and provenance; keep the clearest issue and recommendation. Existing-thread
deduplication additionally records the matched remote thread identifier.
