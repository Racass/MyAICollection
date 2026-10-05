# Security policy

## Supported content

Security fixes are applied to the current default branch. Because skills run
through external agent products, also follow the security guidance and update
policy of the product in which a skill is installed.

## Report a vulnerability

Use this repository's **Report a vulnerability** option under the GitHub
Security tab. Do not disclose exploitable details in a public issue.

Include the affected skill or file, impact, reproduction steps, and any
suggested mitigation. Reports involving leaked credentials should identify the
kind of credential without including the credential itself.

## Safe use

Agent skills can influence tool use and execute bundled code. Before installing
a skill:

- review every file and referenced URL;
- inspect file, network, shell, and credential access;
- use least-privilege credentials and an isolated environment;
- require confirmation for destructive or external side effects;
- pin and audit dependencies where practical.

The repository validator catches structural mistakes and obvious risky files;
it is not a security sandbox or a substitute for human review.
