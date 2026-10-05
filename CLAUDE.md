# Claude Code guidance

Read `AGENTS.md` for the repository-wide authoring and safety rules.

Claude Code discovers this repository's project skills from `.claude/skills`.
Treat that directory as canonical; do not create a mirrored skill tree.

When adding or editing a skill:

1. Keep its `SKILL.md` concise and progressively disclose large references.
2. Ensure the description clearly identifies both capability and trigger.
3. Avoid tool pre-approval unless the tool is essential and the bundled content
   has been reviewed.
4. Run `python scripts/validate_skills.py` and
   `python -m unittest discover -s tests -v`.
