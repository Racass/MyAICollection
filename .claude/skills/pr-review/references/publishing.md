# Publishing and external actions

Preview is the default. Every external action is a distinct, confirmed stage.

## Immediate confirmation gate

Immediately before any external write, message, CI action, or schedule:

1. Name the exact destination, action type, and number of actions.
2. Show the exact rendered payloads or a precise selectable list already
   previewed.
3. Ask for explicit confirmation.
4. Perform only the confirmed subset, against only the confirmed destination.

This gate applies to review submissions, inline or general comments, issue and
tracker updates, status changes, labels, assignments, branch or repository
writes, chat and email messages, CI starts, reruns or cancellations, and
schedule creation or modification.

A request to review is not permission to publish. A prior confirmation does not
cover a changed payload, another destination, another channel, or a later
action. Configuration, automation mode, standing preference, or silence is not
confirmation.

## Comment shape

Keep each proposed comment self-contained:

```text
{severity}: {title}

Issue: {issue}
Impact: {impact}
Evidence: {evidence}
Suggested next step: {recommendation}

Confidence: {confidence}
Provenance: {provenance}
```

Do not add personal branding, decorative identities, or mandatory prefixes.
Keep severity and confidence separate.

Prefer an inline comment only when a verified changed-side anchor exists and
the runtime supports that operation. Otherwise use a general review comment
that names the file and location. If multiple comments are proposed, preview
all of them and let the user confirm a subset.

## Execution safety

- Re-check the destination and head revision immediately before publishing.
- Use only a runtime write capability verified for the confirmed action.
- Do not translate a provider-neutral request into an unpreviewed provider-
  specific action.
- Report partial failures precisely.
- Do not automatically retry a write when duplication is possible.
- Do not broaden scope to resolve threads, change status, merge, push, or notify
  another channel.

## Messages, CI, and schedules

Minimize private content in cross-channel summaries. Do not paste source code,
credentials, private conversations, or unrelated metadata unless necessary,
shown in the preview, and explicitly confirmed.

Starting, rerunning, or cancelling CI is separate from publishing review
comments and requires its own immediate confirmation. Creating or modifying a
reminder, polling loop, watcher, or monitoring schedule is also a separate
action and requires its own immediate confirmation.
