---
name: meeting-notes-organizer
description: Convert rough meeting notes into a concise, structured record with decisions, action items, owners, deadlines, and unresolved questions. Use when a user asks to clean up, organize, summarize, or extract follow-ups from meeting notes or a transcript.
license: MIT
---

# Meeting notes organizer

Transform the supplied notes into a faithful record that is easy to scan and
act on.

## Process

1. Read all supplied content before drafting.
2. Identify the meeting purpose and participants only when explicitly stated.
3. Separate confirmed decisions from proposals and unresolved discussion.
4. Extract action items with an owner and deadline only when the source provides
   them. Use `Unassigned` or `Not specified` rather than guessing.
5. Preserve material risks, blockers, disagreements, and open questions.
6. Remove repetition, filler, and conversational noise without changing meaning.
7. Flag ambiguous or contradictory statements in the open-questions section.

## Output

Use this structure, omitting empty optional sections:

```markdown
# Meeting summary

## Overview
One short paragraph describing the purpose and outcome.

## Decisions
- Confirmed decision

## Action items
| Action | Owner | Due |
| --- | --- | --- |
| Concrete next step | Name or Unassigned | Date or Not specified |

## Open questions
- Question that still needs an answer

## Risks and blockers
- Material risk or blocker

## Key discussion points
- Concise supporting context
```

## Accuracy rules

- Do not invent names, dates, decisions, consensus, or commitments.
- Distinguish facts from interpretations.
- Preserve uncertainty with language such as `proposed`, `tentative`, or
  `unclear from the notes`.
- If the source is too incomplete to summarize reliably, state what is missing
  and organize only the information that is present.
