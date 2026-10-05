# Runtime capability mapping

This skill is provider-neutral. Map the runtime's actual capabilities to the
roles below instead of assuming fixed tool names, vendors, credentials, or
integrations.

## Evidence sources

| Capability role | Evidence that makes it available | Safe use |
| --- | --- | --- |
| Local repository read | A readable checkout, supplied files, or local version-control metadata | Inspect revisions, diffs, guidance, history, and tests without modifying the repository |
| User-supplied evidence | A patch, archive, pasted metadata, requirements, logs, or thread export | Review only the supplied scope and record its provenance |
| Code-host read | A runtime capability demonstrates access to change metadata, files, patches, commits, or threads | Gather read-only change evidence and deduplicate findings |
| Requirements or tracker read | A runtime capability can read the explicitly linked item | Validate stated acceptance criteria without browsing unrelated records |
| CI read | A runtime capability can read status, annotations, artifacts, or logs | Use existing results as evidence; do not start, rerun, or cancel jobs |
| Communication read | The user supplied the content or explicitly authorized a narrowly scoped read capability | Use only material relevant to the change and avoid exposing unrelated private content |
| Local execution | The runtime can run a deterministic command in the workspace | Run the smallest non-destructive check needed to validate a claim |

Classify each role as `available`, `unavailable`, `not configured`, or `not
needed`, and cite the local, user-supplied, or runtime evidence for that
classification.

## Write capabilities

Treat every write capability independently from reads and from other writes.
Examples include submitting a review, posting a comment, updating a tracker,
sending a message, pushing a branch, starting or rerunning CI, and creating a
schedule.

Even when a write capability is present and authenticated:

1. keep preview as the default;
2. render the exact destination and payload;
3. obtain explicit confirmation immediately before the action;
4. perform only the confirmed action;
5. do not reuse confirmation for another destination, payload, or action type.

## Generic runtime mapping

At runtime, choose whichever verified mechanism satisfies a capability role:

- local filesystem or version-control commands for repository evidence;
- a host-provided API or integration for code-host metadata;
- a user-supplied export when no integration exists;
- a local test, build, linter, or focused reproduction for validation.

Do not probe the network merely to discover integrations. Do not infer
authorization from environment variables, configuration filenames, installed
clients, remembered sessions, or successful access to a different system.
Never include secrets or raw credentials in findings or previews.

## Optional repository-local companion

This repository may include an
[optional portable review tool](../../../../tools/portable-pr-review-skill/README.md)
that can detect and render integration-specific packages. It is not required by
this skill. After copying the skill elsewhere, use the runtime mapping above
and ignore the companion link if that separate tool was not copied.
