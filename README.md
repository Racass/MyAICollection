# MyAICollection

A public collection of portable AI agent skills for
[Claude Code](https://code.claude.com/docs/en/skills) and
[GitHub Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).

Skills live in `.claude/skills` as a single canonical copy. Both tools discover
project skills from this location, so fixes and improvements never need to be
synchronized across vendor-specific directories.

## Compatibility

| Surface | Skill location | Repository guidance |
| --- | --- | --- |
| Claude Code | `.claude/skills` | `CLAUDE.md` |
| GitHub Copilot | `.claude/skills` | `AGENTS.md`, `.github/copilot-instructions.md` |
| Other Agent Skills clients | Copy a skill directory to a supported skills path | `AGENTS.md` |

Every skill follows the open
[Agent Skills specification](https://github.com/agentskills/agentskills) and
contains a `SKILL.md` file with `name` and `description` frontmatter.

## Available skills

| Skill | Purpose |
| --- | --- |
| [`meeting-notes-organizer`](.claude/skills/meeting-notes-organizer/SKILL.md) | Turn raw meeting notes into a concise, structured summary without inventing facts. |
| [`pr-review`](.claude/skills/pr-review/SKILL.md) | Perform evidence-backed pull-request reviews with normalized findings, safe previews, and confirmed publishing. |

## Use a skill

### In this repository

Clone the repository and open it with Claude Code or GitHub Copilot. Project
skills are discovered automatically:

```shell
git clone https://github.com/racass/MyAICollection.git
cd MyAICollection
```

Ask the agent for a task matching a skill description, or explicitly name the
skill. In GitHub Copilot CLI, for example:

```text
Use /meeting-notes-organizer to clean up these notes.
```

### In another project

Copy the complete skill directory into the target project's
`.claude/skills` directory:

```text
your-project/
└── .claude/
    └── skills/
        └── meeting-notes-organizer/
            └── SKILL.md
```

Review every skill and bundled script before installing it. Agent skills can
instruct an agent to use tools with the same access as that agent.

The canonical [`pr-review`](.claude/skills/pr-review/SKILL.md) skill works
standalone from `.claude/skills/pr-review`; the generator is not required.

For a stack-optimized installation, the optional
[`portable-pr-review-skill`](tools/portable-pr-review-skill/README.md) tool
detects a consumer repository's stack and available integrations, shows the
evidence for review, and asks for confirmation before generating GitHub Copilot,
Claude Code, or both installations:

```powershell
python -m pip install -e .\tools\portable-pr-review-skill
Set-Location path\to\consumer-repository
python -m pr_review_skill setup
python -m pr_review_skill doctor --profile .pr-review-skill.json
```

## Create a skill

1. Create `.claude/skills/<skill-name>/SKILL.md`.
2. Use a lowercase, hyphen-separated name matching the directory.
3. Write a specific description that says what the skill does and when to use it.
4. Put detailed instructions in the Markdown body.
5. Keep optional scripts, examples, references, and assets inside the skill directory.
6. Run validation:

   ```shell
   python scripts/validate_skills.py
   python -m unittest discover -s tests -v
   ```

Start from this minimal shape:

```markdown
---
name: your-skill-name
description: Explain what this skill does and the situations in which an agent should use it.
license: MIT
---

# Your skill name

Write clear, testable instructions here.
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for authoring, licensing, and safety
requirements.

## Repository structure

```text
.claude/skills/                 Canonical skill directories
.github/copilot-instructions.md GitHub Copilot repository guidance
.github/workflows/              Automated validation
scripts/validate_skills.py      Dependency-free validator
tests/                          Validator tests
tools/portable-pr-review-skill/ Optional stack-aware pr-review generator
AGENTS.md                       Vendor-neutral agent guidance
CLAUDE.md                       Claude Code repository guidance
```

## Security

Treat skills like software. Inspect instructions, scripts, network access, and
file operations before use. Never commit credentials or private data. Report
security concerns according to [SECURITY.md](SECURITY.md).

## License

This repository is licensed under the [MIT License](LICENSE). Contributions
must be original or compatible with that license, with attribution retained
where required.
