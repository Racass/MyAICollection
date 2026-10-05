# Repository instructions for GitHub Copilot

This is a public collection of portable Agent Skills. Read `AGENTS.md` before
editing. The canonical skill tree is `.claude/skills`, which GitHub Copilot
supports directly; never create a duplicate `.github/skills` tree.

Each skill directory must contain `SKILL.md` with a matching lowercase,
hyphenated `name` and a description that states both capability and trigger.
Keep supporting files self-contained and use relative links.

Do not add credentials, private data, destructive defaults, hidden network
access, or unreviewed executable content. Preserve attribution and MIT license
compatibility.

After changes, run:

```shell
python scripts/validate_skills.py
python -m unittest discover -s tests -v
```
