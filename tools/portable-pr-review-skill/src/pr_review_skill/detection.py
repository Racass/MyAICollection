"""Read-only, local-only repository and capability detection."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any
from urllib.parse import unquote, urlsplit

from .models import (
    Capability,
    CapabilityState,
    DetectionEvidence,
    Profile,
    ProviderChoice,
)


@dataclass(frozen=True, slots=True)
class DetectionReport:
    profile: Profile

    def format_text(self) -> str:
        lines = [
            "Portable PR review detection report",
            f"Repository: {self.profile.repository_root}",
            f"Remote: {self.profile.repository.get('remote', 'not detected')}",
            f"Confirmed: {'yes' if self.profile.confirmed else 'no'}",
            "",
            "Capabilities:",
        ]
        for name, capability in sorted(self.profile.capabilities.items()):
            lines.append(f"- {name}: {capability.state.value}")
            for evidence in capability.evidence:
                location = f" [{evidence.path}]" if evidence.path else ""
                lines.append(f"    {evidence.kind}: {evidence.summary}{location}")
            if capability.details:
                lines.append(f"    note: {capability.details}")
        return "\n".join(lines)


def detect_profile(
    repository_root: Path | str = Path.cwd(),
    *,
    provider_choice: ProviderChoice | str = ProviderChoice.ASK,
    confirmed: bool = False,
) -> Profile:
    """Inspect local metadata without reading configuration contents."""

    root = Path(repository_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Repository root is not a directory: {root}")

    capabilities: dict[str, Capability] = {}
    repository: dict[str, str] = {"name": root.name}

    git_dir = root / ".git"
    _add_path_capability(
        capabilities,
        "repository.git",
        [(git_dir, "Git repository metadata exists")],
    )

    remote = _git_remote(root)
    if remote:
        repository.update(remote)
        host = remote.get("host", "")
        evidence = (
            DetectionEvidence(
                kind="git-remote",
                summary=f"Sanitized remote host is {host}",
            ),
        )
        capabilities["repository.remote"] = Capability(
            "repository.remote", CapabilityState.AVAILABLE, evidence
        )
        github_state = (
            CapabilityState.AVAILABLE
            if host.lower() == "github.com"
            else CapabilityState.UNAVAILABLE
        )
        capabilities["code-host.github"] = Capability(
            "code-host.github",
            github_state,
            evidence,
        )
        azure_state = (
            CapabilityState.AVAILABLE
            if host.lower() in {"dev.azure.com", "ssh.dev.azure.com"}
            else CapabilityState.UNAVAILABLE
        )
        capabilities["code-host.azure-devops"] = Capability(
            "code-host.azure-devops",
            azure_state,
            evidence,
        )
    else:
        capabilities["repository.remote"] = Capability(
            "repository.remote",
            CapabilityState.UNVERIFIED,
            details="No origin remote could be read from local Git metadata.",
        )
        for name in ("code-host.github", "code-host.azure-devops"):
            capabilities[name] = Capability(name, CapabilityState.UNVERIFIED)

    markers = {
        "stack.python": ("pyproject.toml", "requirements.txt", "setup.py"),
        "stack.javascript": ("package.json", "pnpm-lock.yaml", "yarn.lock"),
        "stack.dotnet": ("*.sln", "**/*.csproj"),
        "stack.go": ("go.mod",),
        "ci.github-actions": (".github/workflows",),
        "ci.azure-pipelines": ("azure-pipelines.yml",),
    }
    for name, patterns in markers.items():
        matches = _marker_matches(root, patterns)
        _add_path_capability(
            capabilities,
            name,
            [(path, f"Repository marker {path.name} exists") for path in matches],
        )

    _detect_provider(
        capabilities,
        root,
        name="copilot",
        cli_names=("copilot", "github-copilot-cli"),
        paths=(
            ".github/copilot-instructions.md",
            ".github/skills",
            ".agents/skills",
        ),
    )
    _detect_provider(
        capabilities,
        root,
        name="claude",
        cli_names=("claude",),
        paths=("CLAUDE.md", ".claude", ".claude/skills"),
    )

    config_markers = (
        ".mcp.json",
        "mcp.json",
        ".vscode/mcp.json",
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".github/copilot-instructions.md",
        "CLAUDE.md",
    )
    config_evidence = [
        DetectionEvidence(
            kind="config-marker",
            summary=f"Configuration marker {marker} exists; contents were not read",
            path=marker,
        )
        for marker in config_markers
        if (root / marker).exists()
    ]
    capabilities["integration.config-evidence"] = Capability(
        "integration.config-evidence",
        CapabilityState.AMBIGUOUS if config_evidence else CapabilityState.UNVERIFIED,
        tuple(config_evidence),
        "Configuration presence does not prove an authenticated integration.",
    )

    integration_capabilities = (
        "tracker.github",
        "tracker.azure-boards",
        "tracker.jira",
        "chat.slack",
        "chat.teams",
        "mail.gmail",
        "mail.outlook",
    )
    inferred_integrations, tool_bindings = _detect_configured_integrations(
        root, config_markers
    )
    for name in integration_capabilities:
        adapter_id, evidence = inferred_integrations.get(name, ("", ()))
        capabilities[name] = Capability(
            name,
            CapabilityState.AMBIGUOUS if evidence else CapabilityState.UNVERIFIED,
            evidence,
            (
                "A local integration marker was detected, but authentication and runtime "
                "tool availability remain unverified."
                if evidence
                else "Authentication and external service content were not inspected."
            ),
        )

    adapter_ids = ["local-git"] if capabilities["repository.git"].available else []
    for capability_name, adapter_id in (
        ("code-host.github", "github"),
        ("code-host.azure-devops", "azure-devops"),
        ("ci.github-actions", "github-actions"),
        ("ci.azure-pipelines", "azure-pipelines"),
    ):
        if capabilities[capability_name].available:
            adapter_ids.append(adapter_id)
    for capability_name in integration_capabilities:
        adapter_id, evidence = inferred_integrations.get(capability_name, ("", ()))
        if adapter_id and evidence:
            adapter_ids.append(adapter_id)

    return Profile(
        repository_root=root,
        repository=repository,
        capabilities=capabilities,
        adapter_ids=tuple(dict.fromkeys(adapter_ids)),
        tool_bindings=tool_bindings,
        provider_choice=ProviderChoice(provider_choice),
        confirmed=confirmed,
    )


def detect_report(
    repository_root: Path | str = Path.cwd(),
    **kwargs: object,
) -> DetectionReport:
    return DetectionReport(detect_profile(repository_root, **kwargs))


def _detect_provider(
    capabilities: dict[str, Capability],
    root: Path,
    *,
    name: str,
    cli_names: tuple[str, ...],
    paths: tuple[str, ...],
) -> None:
    evidence: list[DetectionEvidence] = []
    for cli_name in cli_names:
        executable = shutil.which(cli_name)
        if executable:
            evidence.append(
                DetectionEvidence(
                    kind="cli",
                    summary=f"{cli_name} executable is available on PATH",
                )
            )
    for relative in paths:
        if (root / relative).exists():
            evidence.append(
                DetectionEvidence(
                    kind="provider-marker",
                    summary=f"Provider marker {relative} exists",
                    path=relative,
                )
            )
    state = CapabilityState.AVAILABLE if evidence else CapabilityState.UNAVAILABLE
    capabilities[f"provider.{name}"] = Capability(
        f"provider.{name}", state, tuple(evidence)
    )


def _add_path_capability(
    capabilities: dict[str, Capability],
    name: str,
    matches: list[tuple[Path, str]],
) -> None:
    evidence = tuple(
        DetectionEvidence(
            kind="repository-marker",
            summary=summary,
            path=_safe_relative(path),
        )
        for path, summary in matches
    )
    capabilities[name] = Capability(
        name,
        CapabilityState.AVAILABLE if evidence else CapabilityState.UNAVAILABLE,
        evidence,
    )


def _marker_matches(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    matches: list[Path] = []
    for pattern in patterns:
        if "*" in pattern:
            matches.extend(path for path in root.glob(pattern) if path.exists())
        else:
            path = root / pattern
            if path.exists():
                matches.append(path)
    return matches


def _detect_configured_integrations(
    root: Path,
    markers: tuple[str, ...],
) -> tuple[
    dict[str, tuple[str, tuple[DetectionEvidence, ...]]],
    dict[str, tuple[str, ...]],
]:
    keyword_map = {
        "github": ("tracker.github", "github-issues"),
        "azure-boards": ("tracker.azure-boards", "azure-boards"),
        "boards": ("tracker.azure-boards", "azure-boards"),
        "jira": ("tracker.jira", "jira"),
        "slack": ("chat.slack", "slack"),
        "teams": ("chat.teams", "teams"),
        "gmail": ("mail.gmail", "gmail"),
        "google-mail": ("mail.gmail", "gmail"),
        "outlook": ("mail.outlook", "outlook"),
    }
    detected: dict[str, tuple[str, list[DetectionEvidence]]] = {}
    bindings: dict[str, list[str]] = {}
    for marker in markers:
        path = root / marker
        if not path.is_file() or path.suffix.lower() != ".json":
            continue
        terms = _safe_config_terms(path)
        server_names = _safe_config_server_names(path)
        for keyword, (capability_name, adapter_id) in keyword_map.items():
            if not any(keyword in term for term in terms):
                continue
            evidence = DetectionEvidence(
                kind="integration-marker",
                summary=f"Configuration contains a {adapter_id} integration identifier",
                path=marker,
            )
            current_adapter, current_evidence = detected.get(
                capability_name, (adapter_id, [])
            )
            if evidence not in current_evidence:
                current_evidence.append(evidence)
            detected[capability_name] = (current_adapter, current_evidence)
            for server_name in server_names:
                if keyword in server_name.lower():
                    bindings.setdefault(adapter_id, []).append(server_name)
    return (
        {
            name: (adapter_id, tuple(evidence))
            for name, (adapter_id, evidence) in detected.items()
        },
        {
            adapter_id: tuple(dict.fromkeys(names))
            for adapter_id, names in bindings.items()
        },
    )


def _safe_config_terms(path: Path) -> set[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    terms: set[str] = set()
    sensitive_keys = {
        "env",
        "environment",
        "token",
        "secret",
        "password",
        "authorization",
        "headers",
        "api-key",
        "apikey",
    }

    def visit(value: Any, *, parent_key: str = "") -> None:
        if parent_key.lower() in sensitive_keys:
            return
        if isinstance(value, dict):
            for key, item in value.items():
                normalized_key = str(key).strip().lower()
                terms.add(normalized_key)
                visit(item, parent_key=normalized_key)
        elif isinstance(value, list):
            for item in value:
                visit(item, parent_key=parent_key)
        elif isinstance(value, str) and parent_key in {
            "command",
            "args",
            "name",
            "server",
            "url",
        }:
            terms.add(value.strip().lower())

    visit(payload)
    return terms


def _safe_config_server_names(path: Path) -> tuple[str, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, dict):
        return ()
    servers = payload.get("mcpServers", payload.get("servers", {}))
    if not isinstance(servers, dict):
        return ()
    return tuple(str(name) for name in servers)


def _git_remote(root: Path) -> dict[str, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if result.returncode != 0:
        return {}
    return _sanitize_remote(result.stdout.strip())


def _sanitize_remote(remote: str) -> dict[str, str]:
    if not remote:
        return {}
    host = ""
    path = ""
    scp_match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", remote)
    if scp_match and "://" not in remote:
        host, path = scp_match.groups()
    else:
        parsed = urlsplit(remote)
        host = parsed.hostname or ""
        path = parsed.path
    if not host:
        return {}
    path = unquote(path).strip("/").removesuffix(".git")
    safe_path = "/".join(
        segment for segment in path.split("/") if segment not in {".", ".."}
    )
    result = {"host": host.lower(), "remote": host.lower()}
    if safe_path:
        result["slug"] = safe_path
        result["remote"] = f"{host.lower()}/{safe_path}"
    return result


def _safe_relative(path: Path) -> str:
    # Evidence paths are deliberately reduced to repository-local marker names.
    return path.name
