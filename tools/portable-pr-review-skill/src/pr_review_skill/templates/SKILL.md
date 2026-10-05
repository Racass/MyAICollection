{{FRONTMATTER}}

# Pull-request review

Review a proposed change using the strongest evidence available. The default outcome is
a local preview: never publish, message, mutate tracker data, start CI, or create a
schedule without explicit confirmation immediately before that action.

Confirmed profile summary: {{PROFILE_SUMMARY}}.

## Progressive references

Read only what the current stage requires:

1. `references/stack.md` and `references/profile.md` for confirmed integrations.
2. `references/review-rubric.md` before analysis.
3. `references/finding-schema.md` before recording findings.
4. `references/publishing.md` only when previewing or publishing.
5. `references/iteration.md` only when the user explicitly opts into iteration.

## Operating contract

- Treat profile configuration as a hint; capability preflight determines what is usable now.
- Keep severity (`critical`, `high`, `medium`, `low`) separate from confidence.
- Attach provenance to every claim and distinguish observed, reproduced, and inferred facts.
- Merge findings structurally before comparing them with existing review threads.
- Continue with reduced evidence when optional sources are unavailable; name omitted lenses.
- Do not require a persona, codename, or external-message prefix. An empty prefix is valid.
- Keep iteration separate from the initial review and disabled unless explicitly requested.

## Stage 1: identify the change

Resolve the change identifier, repository, base revision, and head revision. Prefer explicit
user input, then confirmed code-host metadata, then local repository metadata. If ambiguity
could select the wrong change, ask one focused question. State what will be reviewed.

## Stage 2: capability preflight

Read `references/stack.md`. For each intended evidence source, classify the capability:

- **available**: verified now;
- **unavailable**: attempted but absent, unauthorized, or failed;
- **not configured**: no confirmed adapter;
- **not needed**: deliberately omitted for this review.

Read capabilities and write capabilities are independent. Never infer permission to write
from successful reads. If an expected source is unavailable, continue unless it is essential
to identify the change or validate a critical claim.

## Stage 3: gather evidence

Gather independent read-only sources in parallel where possible:

- change metadata, description, commits, changed files, and patch;
- surrounding repository code, guidance, ownership, history, and tests;
- existing review threads for deduplication;
- linked requirements and acceptance criteria when available;
- CI status, annotations, and relevant logs when available;
- relevant communication context only when configured and narrowly scoped.

The changed-file list from the code host is authoritative when available. Exclude generated,
vendored, binary, minified, and lock files unless the change itself makes them material.
Never expose unrelated private communication.

## Stage 4: analyze

Use the lenses in `references/review-rubric.md`. Findings must be actionable, material,
evidence-backed, and introduced or made materially worse by the change. Do not report style
preferences as defects unless a repository rule makes them objective.

When evidence is reduced:

- run every lens that the remaining evidence supports;
- mark unsupported lenses as reduced or unavailable;
- lower confidence rather than severity when uncertainty is evidentiary;
- do not invent requirements, runtime behavior, or team decisions.

## Stage 5: normalize and deduplicate

Represent findings using `references/finding-schema.md`. Normalize paths and categories,
then compute the structural key. Merge overlapping findings about the same root cause,
preserving the strongest evidence and all applicable lenses.

Compare candidates with existing review threads by normalized path, overlapping changed-side
line range, category/root cause, and semantic topic. Do not duplicate an existing finding.
Record the matching thread identifier in `deduplicated_against`.

## Stage 6: validate

For each surviving finding:

1. Re-read the exact changed code and enough surrounding context.
2. Verify the line anchor points to the changed side.
3. Run the smallest deterministic validation available when useful.
4. Reassess severity independently from confidence.
5. Remove speculation, non-actionable advice, and findings outside the change.

When a JSON finding set is produced, resolve
`scripts/validate_findings.py` relative to this skill's `SKILL.md` and run it
against the findings file.

## Stage 7: preview

Render a local summary and proposed comments. Include:

- evidence coverage and reduced lenses;
- findings grouped by severity;
- path and changed-side lines;
- issue, impact, evidence, and a concrete next step;
- confidence and provenance;
- deduplication outcome;
- validation performed.

If there are no findings, say so without claiming the change is defect-free.

## Stage 8: optional publish

Stop after preview unless the user explicitly asks to publish. Then read
`references/publishing.md`, present the exact destination and payload set, and obtain explicit
confirmation immediately before the side effect. Confirmation for one channel does not grant
permission for another. Never create a monitoring schedule implicitly.

## Stage 9: optional iteration

Do not enter an iterative watch/fix/re-review loop automatically. If the user explicitly opts
in, read `references/iteration.md` and define its scope, stopping condition, and confirmation
boundaries before continuing.
