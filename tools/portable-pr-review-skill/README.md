# Portable PR Review Skill Generator

This optional MyAICollection tool generates a pull-request review skill tailored
to a consumer repository, its detected stack and integrations, and the selected
agent provider.

The canonical static skill shipped by MyAICollection lives at
[`../../.claude/skills/pr-review`](../../.claude/skills/pr-review). Use that
version when a general-purpose portable skill is sufficient. Use this generator
when a consumer repository should receive optimized GitHub Copilot, Claude Code,
or dual-provider variants based on a reviewed local detection profile.

The generator source is vendor-neutral. Product-specific instructions are
emitted only after a read-only detection report is reviewed and confirmed.

## Safety model

- Detection reads local configuration and repository metadata only.
- Detection does not open pull requests, issues, mail, or chat messages.
- Installation requires a confirmed profile.
- Generated skills preview findings by default.
- Posting comments, sending messages, or creating monitoring schedules requires
  explicit confirmation.
- Profiles store capabilities and tool names, never tokens or external content.

## Supported targets

Agent providers:

- GitHub Copilot
- Claude Code
- Both providers from one confirmed profile

Integration families:

- Code hosts: GitHub, Azure DevOps
- Trackers: GitHub Issues/Projects, Azure Boards, Jira
- Chat: Slack, Teams
- Mail: Gmail, Outlook
- Local repository and CI evidence

An integration is included in generated instructions only when its capability is
confirmed. Unknown integrations can be represented explicitly in a profile, but
are not advertised as automatically detected.

## Intended workflow

From this tool directory:

```powershell
python -m pip install -e .
Set-Location path\to\consumer-repository
python -m pr_review_skill setup
python -m pr_review_skill doctor --profile .pr-review-skill.json
```

`setup` detects the stack, prints the evidence, asks for confirmation, asks
whether to target Copilot, Claude Code, or both when necessary, saves the
confirmed profile in the consumer repository, and only then writes the generated
skill there.

For automation, run `detect` first and pass the reviewed, confirmed profile to
`install`. Non-interactive installation requires an already confirmed profile.

Use `python -m pr_review_skill --help` for the exact command options.

## Generated layout

Each provider receives a normal Agent Skills directory containing:

```text
pr-review/
├── SKILL.md
├── references/
│   ├── finding-schema.md
│   ├── iteration.md
│   ├── publishing.md
│   ├── profile.md
│   ├── review-rubric.md
│   └── stack.md
└── scripts/
    └── validate_findings.py
```

The main skill stays compact. Detailed rules and stack-specific instructions are
loaded progressively from `references/`.

Project-scoped output is installed in the consumer repository:

- GitHub Copilot: `.github/skills/pr-review/`
- Claude Code: `.claude/skills/pr-review/`

Personal scope remains available through the CLI and uses each provider's
standard user-level skill directory.

## Updating and removing

Installation records a source hash and creates a backup before replacing a
different generated skill. Reinstalling identical output is a no-op.

`doctor` checks profile validity, provider destinations, generated hashes, and
required capabilities. `uninstall` removes only files owned by the generator and
does not delete unrelated skills.

## Adding an adapter

An adapter declares:

1. The integration family and identifier.
2. The capabilities it can provide.
3. Detection evidence it recognizes.
4. The concrete commands or tool names selected during generation.
5. Stack-specific instructions rendered into `references/stack.md`.

Do not add product-specific behavior to the canonical skill template. If a
behavior depends on an integration, gate it on a capability and keep its
concrete details in the adapter.

## Development

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Validation includes unit tests, generated-file snapshots, idempotent install
checks, forbidden-brand scans, and representative stack profiles.

## License

This tool and its generated templates are distributed under the MIT License.
See [`LICENSE`](LICENSE).
