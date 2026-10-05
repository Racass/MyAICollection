# Agent guidance

## Repository purpose

This repository contains portable Agent Skills for Claude Code and GitHub
Copilot. The canonical skills directory is `.claude/skills`.

## Working rules

- Never duplicate skill content into another vendor-specific skills tree.
- Each skill must have a `.claude/skills/<name>/SKILL.md` file.
- Keep the directory name and the frontmatter `name` identical.
- Use lowercase letters, numbers, and hyphens for skill names.
- Make each description state both what the skill does and when to use it.
- Keep optional scripts and references inside their owning skill directory.
- Do not add secrets, personal data, hidden network calls, destructive defaults,
  or unreviewed executable content.
- Prefer platform-neutral instructions. Clearly document unavoidable runtime
  or tool requirements.
- Preserve attribution and verify license compatibility for adapted material.

## Validation

Run these commands after changing skills or validation logic:

```shell
python scripts/validate_skills.py
python -m unittest discover -s tests -v
```

Do not publish or merge changes while either command fails.
