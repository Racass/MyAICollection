# Opt-in iteration

Iteration is disabled by default and separate from the initial review.

Enter iteration only after the user explicitly requests it. Define:

- the change and findings in scope;
- whether fixes are user-authored or agent-authored;
- evidence to refresh on each pass;
- maximum passes or another stopping condition;
- side effects that still require confirmation.

For each pass:

1. Refresh the head revision and changed-file list.
2. Re-run capability preflight for evidence being refreshed.
3. Revalidate unresolved findings against the new code.
4. Close findings only with evidence; preserve superseded finding identifiers.
5. Detect newly introduced defects without reopening unrelated review scope.
6. Preview the iteration result locally.

Do not post replies, resolve threads, send status messages, rerun CI, or schedule another pass
without the corresponding explicit confirmation. Stop on scope drift, repeated inconclusive
evidence, a reached pass limit, or a user request.
