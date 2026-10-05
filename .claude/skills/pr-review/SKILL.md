---
name: pr-review
description: Perform evidence-backed pull-request reviews with normalized findings, deduplication, safe previews, and confirmed publishing when a user asks to review a pull request, branch, patch, or proposed change.
license: MIT
---

# Pull-request review

Review a proposed change using the strongest evidence available at runtime. The
default result is a local preview. Do not publish, send a message, write to an
external system, start or rerun CI, or create a schedule without explicit
confirmation immediately before that specific action.

## Progressive references

Read only what the current stage needs:

1. [Runtime capability mapping](references/stack.md) before gathering evidence.
2. [Review rubric](references/review-rubric.md) before analysis.
3. [Finding schema](references/finding-schema.md) before recording findings.
4. [Publishing rules](references/publishing.md) only when previewing an external
   action or preparing to perform one.
5. [Iteration rules](references/iteration.md) only when the user explicitly
   requests another review pass or an ongoing loop.

## Operating contract

- Use only evidence supplied by the user, present in the local workspace, or
  exposed by capabilities verified during this run.
- Treat configured integrations and remembered tool names as hints, not proof
  that a capability or authorization is available now.
- Keep read capabilities separate from write capabilities. Successful reads
  never imply permission to write.
- Keep severity (`critical`, `high`, `medium`, `low`) separate from confidence.
- Attach provenance to every finding and distinguish observed, reproduced, and
  inferred facts.
- Merge overlapping findings structurally before comparing them with existing
  review threads.
- Continue with reduced evidence when optional sources are unavailable. State
  the omitted sources and affected review lenses.
- Never require a persona, codename, personal path, message prefix, vendor, or
  particular integration.
- Never discover integrations by sending network requests unless the user
  explicitly asked for that network access or the runtime clearly exposes a
  read capability appropriate to the review.
- Do not edit the proposed change while reviewing unless the user separately
  asks for a fix.

## Stage 1: identify the change

Resolve the repository, change identifier, base revision, and head revision.
Prefer, in order:

1. explicit user input;
2. user-supplied change metadata or patch;
3. verified runtime code-host metadata;
4. local repository metadata.

If ambiguity could select the wrong change, ask one focused question. State the
resolved review target before analysis.

## Stage 2: capability preflight

Read [Runtime capability mapping](references/stack.md). For every intended
evidence source, classify the runtime capability as:

- **available**: verified now;
- **unavailable**: attempted through an allowed read path but absent,
  unauthorized, or failed;
- **not configured**: no runtime evidence of a suitable capability;
- **not needed**: deliberately omitted for this review.

Record the evidence for each classification. A tool's presence does not prove
credentials, repository access, or write permission. If an optional source is
unavailable, continue unless it is essential to identify the change or support
a critical claim.

## Stage 3: gather evidence

Gather independent read-only sources in parallel when supported:

- change metadata, description, commits, changed files, and patch;
- surrounding repository code, repository guidance, ownership, history, and
  tests;
- existing review threads for deduplication;
- linked requirements and acceptance criteria;
- CI status, annotations, and relevant logs;
- communication context only when supplied or explicitly authorized and
  narrowly scoped.

Prefer the code host's changed-file list when available. Otherwise derive the
list from local revisions or the supplied patch and state that provenance.
Exclude generated, vendored, binary, minified, and lock files unless the change
makes them material. Do not expose unrelated private content.

## Stage 4: analyze

Apply [Review rubric](references/review-rubric.md) to changed behavior rather
than merely changed text. Findings must be actionable, material,
evidence-backed, and introduced or made materially worse by the change.

Do not report:

- style preferences without an objective repository rule;
- speculative risks that cannot be tied to a credible execution path;
- pre-existing defects unchanged by the proposal;
- broad redesign suggestions unrelated to a demonstrated defect.

When evidence is reduced:

- run every lens the remaining evidence supports;
- mark unsupported lenses as reduced or unavailable;
- lower confidence rather than severity when uncertainty is evidentiary;
- never invent requirements, runtime behavior, or team decisions.

## Stage 5: normalize and deduplicate

Represent findings with [Finding schema](references/finding-schema.md).
Normalize repository-relative paths, changed-side line ranges, categories, and
root-cause tokens before computing each structural key.

Merge candidates that describe the same root cause or inseparable behavior.
Preserve the clearest issue, strongest evidence, applicable lenses, and all
provenance. Compare remaining candidates with existing review threads by path,
overlapping changed-side lines, category or root cause, and semantic topic.
Record matched thread identifiers in `deduplicated_against` and do not propose a
duplicate comment.

## Stage 6: validate

For each surviving finding:

1. Re-read the exact changed code and enough surrounding context.
2. Verify the location points to the changed side or mark it as a general
   finding.
3. Run the smallest deterministic local or explicitly authorized read-only
   validation that can strengthen or disprove the claim.
4. Reassess severity independently from confidence.
5. Remove speculation, non-actionable advice, and findings outside the change.

If findings are stored as JSON, resolve the bundled validator relative to this
skill's `SKILL.md`, then run:

```text
python <skill-directory>/scripts/validate_findings.py FINDINGS.json
```

The command is local and does not publish anything.

## Stage 7: preview

Render a local review summary and proposed comments. Include:

- the reviewed target and revisions;
- evidence coverage, capability status, and reduced lenses;
- findings grouped by severity;
- repository-relative path and changed-side lines;
- issue, impact, evidence, and the smallest safe next step;
- confidence and provenance;
- deduplication results;
- validation performed.

If there are no findings, say so without claiming the change is defect-free.
Preview is complete work; publishing is optional and separate.

## Stage 8: optional external action

Stop after preview unless the user asks for an external action. Then read
[Publishing rules](references/publishing.md).

Immediately before every external write, comment, review submission, message,
tracker update, CI action, or schedule:

1. identify the exact destination and action;
2. show the exact payload or precise selected payload list;
3. state the number of writes or actions;
4. ask for explicit confirmation;
5. perform only the confirmed action.

A request to review, a configuration flag, earlier approval, or silence is not
confirmation. Confirmation is scoped to the displayed destination, payload,
and action. Ask again when any of them changes and before each additional
external action.

## Stage 9: optional iteration

Do not automatically watch, fix, re-review, reply, resolve threads, rerun CI,
or schedule another pass. If the user explicitly requests iteration, read
[Iteration rules](references/iteration.md), define the scope and stopping
condition, and preserve the confirmation gate for every side effect.
