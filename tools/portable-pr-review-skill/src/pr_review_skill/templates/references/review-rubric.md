# Review rubric

Apply each supported lens to changed behavior, not merely changed text.

## Correctness and reliability

- Broken invariants, wrong branching, boundary errors, partial failure, retries, idempotency.
- Resource lifetime, concurrency, ordering, consistency, and error propagation.
- Compatibility with callers, persisted data, protocols, and supported environments.

## Security and privacy

- Trust boundaries, authorization, validation, injection, unsafe deserialization, secrets.
- Information exposure in logs, comments, telemetry, errors, or generated artifacts.
- Unsafe defaults and bypasses introduced by fallback behavior.

## Tests and quality

- Untested changed branches and failure modes with credible regression risk.
- Assertions that cannot detect the regression, flaky timing, shared state, unrealistic data.
- Missing integration or migration validation when unit coverage cannot prove behavior.

## Product and requirements

- Observable mismatch with explicit description or linked acceptance criteria.
- Incomplete workflows, inaccessible states, destructive behavior, or misleading output.
- Documentation gaps only when users or operators would otherwise be harmed.

## Architecture and maintainability

- Contract violations, misplaced responsibility, dependency direction, duplicated policy.
- Changes that make safe extension or operation materially harder.
- Avoid speculative redesign and preference-only refactoring.

## Operations and delivery

- Deployment ordering, migration safety, rollback, configuration, monitoring, and alerting.
- CI failures or missing checks that directly weaken confidence in the changed behavior.

## Evidence matrix

| Evidence unavailable | Continue with | Mark reduced |
|---|---|---|
| Linked requirements | Code, description, tests | Product/requirements |
| Communication context | Recorded artifacts | Stakeholder intent |
| CI logs/status | Static review, local deterministic checks | Delivery/runtime |
| Local checkout | Host patch and file content | History/deep context |
| Existing threads | Review findings | Deduplication confidence |

An unavailable optional source is not a failure. State the reduction and avoid claims that
depend on it.
