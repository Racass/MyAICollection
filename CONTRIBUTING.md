# Contributing

Contributions that improve existing skills or add focused, reusable skills are
welcome.

## Before contributing

- Search existing skills to avoid overlapping capabilities.
- Use only content you created or have the right to redistribute under terms
  compatible with the MIT License.
- Retain required copyright notices and attribution for adapted material.
- Remove credentials, private data, customer data, and machine-specific paths.
- Review every instruction, script, dependency, URL, and bundled asset.
- Do not make destructive actions, external uploads, or network access the
  default behavior.

## Add a skill

Create `.claude/skills/<skill-name>/SKILL.md` with this minimum frontmatter:

```yaml
---
name: skill-name
description: Explain what the skill does and when an agent should use it.
license: MIT
---
```

Skill names must use lowercase letters, numbers, and hyphens, and must match
their directory. The words `anthropic` and `claude` are reserved in skill
names. Descriptions must be specific and no longer than 1024 characters.

Keep related scripts, examples, references, and assets inside the skill
directory. Use relative links so an installed skill remains self-contained.
Document any runtime, platform, package, network, or permission requirement.

## Validate changes

Requires Python 3.10 or later and no third-party packages:

```shell
python scripts/validate_skills.py
python -m unittest discover -s tests -v
```

## Pull requests

Use a focused title and explain the use case, trigger behavior, validation
performed, source/provenance, and security implications. By contributing, you
agree that your contribution is available under this repository's MIT License.
