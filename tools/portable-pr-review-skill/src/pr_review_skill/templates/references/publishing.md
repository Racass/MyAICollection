# Publishing and external actions

Preview is the default. Publishing is a distinct, confirmed stage.

## Confirmation gate

Immediately before any side effect:

1. Name the destination, number of payloads, and action type.
2. Show the exact rendered payloads or a precise selectable list already previewed.
3. Ask for explicit confirmation.
4. Publish only the confirmed subset and only to the confirmed destination.

Comments, tracker updates, messages, email, CI runs, and schedules require separate
confirmation. A prior request to review is not permission to publish. A profile flag is not
confirmation. Never reinterpret silence as approval.

## Comment shape

Keep each comment self-contained:

```text
{optional message_prefix}
{severity}: {title}

Issue: {issue}
Impact: {impact}
Evidence: {evidence}
Suggested next step: {recommendation}

Confidence: {confidence}
Provenance: {provenance}
```

Omit the prefix line when `message_prefix` is empty. Avoid decorative identities or mandatory
personal headers. Preserve normalized severity and confidence without conflating them.

Prefer inline comments only with a verified changed-side anchor. Otherwise use a general review
comment that names the file and relevant location. Report partial publishing failures and do not
retry writes automatically when duplication is possible.

## Messages and schedules

Minimize private content in cross-channel summaries. Do not paste source code or conversations
unless necessary and approved. Creating reminders, polling loops, or monitoring schedules is
never part of publishing; it requires its own explicit request and confirmation.
