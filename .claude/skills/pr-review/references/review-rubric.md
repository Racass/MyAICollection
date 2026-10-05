# Review rubric

Apply each supported lens to changed behavior, not merely changed text.

## Correctness and reliability

- Broken invariants, wrong branching, boundary errors, partial failure,
  retries, and idempotency.
- Resource lifetime, concurrency, ordering, consistency, and error propagation.
- Compatibility with callers, persisted data, protocols, and supported
  environments.

## Security and privacy

- Trust boundaries, authorization, validation, injection, unsafe
  deserialization, and secret handling.
- Information exposure in logs, comments, telemetry, errors, or generated
  artifacts.
- Unsafe defaults and bypasses introduced by fallback behavior.

## Tests and quality

- Untested changed branches and failure modes with credible regression risk.
- Assertions that cannot detect the regression, flaky timing, shared state, or
  unrealistic data.
- Missing integration or migration validation when unit coverage cannot prove
  behavior.

## Product and requirements

- Observable mismatch with the supplied description, requirements, or linked
  acceptance criteria.
- Incomplete workflows, inaccessible states, destructive behavior, or
  misleading output.
- Documentation gaps only when users or operators would otherwise be harmed.

## Architecture and maintainability

- Contract violations, misplaced responsibility, dependency direction,
  duplicated policy, or incompatible extension points.
- Changes that make safe extension or operation materially harder.
- Avoid speculative redesign and preference-only refactoring.

## Operations and delivery

- Deployment ordering, migration safety, rollback, configuration, monitoring,
  and alerting.
- CI failures or missing checks that directly weaken confidence in changed
  behavior.

## Evidence matrix

| Evidence unavailable | Continue with | Mark reduced |
| --- | --- | --- |
| Linked requirements | Code, description, tests | Product and requirements |
| Communication context | Supplied or recorded artifacts | Stakeholder intent |
| CI logs or status | Static review, local deterministic checks | Delivery and runtime |
| Local checkout | Supplied patch and file content | History and deep context |
| Existing threads | Review findings | Deduplication confidence |

An unavailable optional source is not a failure. State the reduction and avoid
claims that depend on it.
