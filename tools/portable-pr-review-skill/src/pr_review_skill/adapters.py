"""Declarative integration adapters used by the skill renderer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable


@runtime_checkable
class ProfileLike(Protocol):
    """Minimum structural contract accepted by adapter selection."""

    def model_dump(self) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    mutating: bool = False


@dataclass(frozen=True)
class Adapter:
    identifier: str
    family: str
    display_name: str
    capabilities: tuple[Capability, ...]
    preflight: tuple[str, ...]
    evidence: tuple[str, ...]
    publishing: tuple[str, ...] = ()

    @property
    def capability_names(self) -> frozenset[str]:
        return frozenset(item.name for item in self.capabilities)


def _cap(name: str, description: str, *, mutating: bool = False) -> Capability:
    return Capability(name, description, mutating)


ADAPTERS: dict[str, Adapter] = {
    "github": Adapter(
        identifier="github",
        family="code-host",
        display_name="GitHub",
        capabilities=(
            _cap("code-host.metadata", "Read pull request metadata and changed files."),
            _cap("code-host.diff", "Read patch and file contents."),
            _cap("code-host.threads.read", "Read review comments and conversations."),
            _cap("code-host.threads.write", "Create review comments.", mutating=True),
            _cap("code-host.inline-comments", "Anchor comments to changed lines.", mutating=True),
        ),
        preflight=(
            "Confirm the GitHub repository and pull request are readable.",
            "Confirm review threads can be listed before deduplication.",
            "Treat comment-writing permission as separate from read access.",
        ),
        evidence=(
            "Use pull request metadata, changed files, patches, commits, and existing review threads.",
            "Use the repository checkout for surrounding context when available.",
        ),
        publishing=(
            "Preview every comment before using a GitHub review-comment or issue-comment write operation.",
            "Use inline review comments only when the changed-side line anchor is verified.",
        ),
    ),
    "azure-devops": Adapter(
        identifier="azure-devops",
        family="code-host",
        display_name="Azure DevOps",
        capabilities=(
            _cap("code-host.metadata", "Read pull request metadata and changed files."),
            _cap("code-host.diff", "Read pull request changes and repository content."),
            _cap("code-host.threads.read", "Read pull request threads."),
            _cap("code-host.threads.write", "Create pull request threads.", mutating=True),
            _cap("code-host.inline-comments", "Anchor threads to changed lines.", mutating=True),
        ),
        preflight=(
            "Confirm the Azure DevOps organization, project, repository, and pull request.",
            "Confirm pull request threads can be listed before deduplication.",
            "Treat thread-writing permission as separate from read access.",
        ),
        evidence=(
            "Use pull request metadata, iterations/changes, commits, and existing threads.",
            "Use the repository checkout for surrounding context when available.",
        ),
        publishing=(
            "Preview every thread before using an Azure DevOps pull-request thread write operation.",
            "Use an inline thread only when right-side line coordinates are verified.",
        ),
    ),
    "github-issues": Adapter(
        identifier="github-issues",
        family="tracker",
        display_name="GitHub Issues and Projects",
        capabilities=(
            _cap("tracker.items.read", "Read linked issues and project context."),
            _cap("tracker.items.write", "Create or update issue/project content.", mutating=True),
        ),
        preflight=(
            "Confirm linked GitHub issues or project items are readable.",
            "Do not infer acceptance criteria from labels alone.",
        ),
        evidence=(
            "Use linked issue bodies, checklists, project fields, and relevant discussion as requirement evidence.",
        ),
        publishing=(
            "Require explicit confirmation before creating or updating a GitHub issue or project item.",
        ),
    ),
    "azure-boards": Adapter(
        identifier="azure-boards",
        family="tracker",
        display_name="Azure Boards",
        capabilities=(
            _cap("tracker.items.read", "Read linked work items and relations."),
            _cap("tracker.items.write", "Create or update work items.", mutating=True),
        ),
        preflight=(
            "Confirm linked Azure Boards work items and relations are readable.",
            "Read the work item type before interpreting fields such as acceptance criteria.",
        ),
        evidence=(
            "Use descriptions, acceptance criteria, state, relations, and discussion as requirement evidence.",
        ),
        publishing=(
            "Require explicit confirmation before creating or updating an Azure Boards work item.",
        ),
    ),
    "jira": Adapter(
        identifier="jira",
        family="tracker",
        display_name="Jira",
        capabilities=(
            _cap("tracker.items.read", "Read linked Jira issues and relations."),
            _cap("tracker.items.write", "Create or update Jira issues.", mutating=True),
        ),
        preflight=(
            "Confirm the Jira site, project, and linked issue are readable.",
            "Inspect the issue type and field names before interpreting requirements.",
        ),
        evidence=(
            "Use the issue description, acceptance criteria, links, status, and comments as requirement evidence.",
        ),
        publishing=(
            "Require explicit confirmation before creating or updating a Jira issue.",
        ),
    ),
    "slack": Adapter(
        identifier="slack",
        family="communication",
        display_name="Slack",
        capabilities=(
            _cap("communication.search", "Search relevant Slack messages."),
            _cap("communication.send", "Send Slack messages.", mutating=True),
        ),
        preflight=(
            "Confirm Slack search is available and scoped to channels the user may access.",
            "Treat message sending as a separate capability.",
        ),
        evidence=(
            "Use directly relevant Slack decisions as secondary provenance; quote minimally and avoid unrelated private content.",
        ),
        publishing=(
            "Require explicit confirmation immediately before sending a Slack message.",
        ),
    ),
    "teams": Adapter(
        identifier="teams",
        family="communication",
        display_name="Teams",
        capabilities=(
            _cap("communication.search", "Search relevant Teams messages."),
            _cap("communication.send", "Send Teams messages.", mutating=True),
        ),
        preflight=(
            "Confirm Teams search is available and scoped to conversations the user may access.",
            "Treat message sending as a separate capability.",
        ),
        evidence=(
            "Use directly relevant Teams decisions as secondary provenance; quote minimally and avoid unrelated private content.",
        ),
        publishing=(
            "Require explicit confirmation immediately before sending a Teams message.",
        ),
    ),
    "gmail": Adapter(
        identifier="gmail",
        family="communication",
        display_name="Gmail",
        capabilities=(
            _cap("communication.search", "Search relevant Gmail messages."),
            _cap("communication.send", "Send Gmail messages.", mutating=True),
        ),
        preflight=(
            "Confirm Gmail search access and narrow searches to review-related subjects or identifiers.",
            "Treat email sending as a separate capability.",
        ),
        evidence=(
            "Use directly relevant email decisions as secondary provenance; do not expose unrelated recipients or content.",
        ),
        publishing=(
            "Require explicit confirmation immediately before sending a Gmail message.",
        ),
    ),
    "outlook": Adapter(
        identifier="outlook",
        family="communication",
        display_name="Outlook",
        capabilities=(
            _cap("communication.search", "Search relevant Outlook messages."),
            _cap("communication.send", "Send Outlook messages.", mutating=True),
        ),
        preflight=(
            "Confirm Outlook search access and narrow searches to review-related subjects or identifiers.",
            "Treat email sending as a separate capability.",
        ),
        evidence=(
            "Use directly relevant email decisions as secondary provenance; do not expose unrelated recipients or content.",
        ),
        publishing=(
            "Require explicit confirmation immediately before sending an Outlook message.",
        ),
    ),
    "ci": Adapter(
        identifier="ci",
        family="ci",
        display_name="Configured CI",
        capabilities=(
            _cap("ci.status.read", "Read build and check status."),
            _cap("ci.logs.read", "Read available job logs and annotations."),
            _cap("ci.run", "Start or rerun CI jobs.", mutating=True),
        ),
        preflight=(
            "Identify the configured CI system from repository metadata or the confirmed profile.",
            "Separate status/log access from run or rerun permission.",
        ),
        evidence=(
            "Use check status, annotations, and relevant failing log excerpts; distinguish observed failures from local reproduction.",
        ),
        publishing=(
            "Require explicit confirmation before starting, rerunning, or scheduling CI work.",
        ),
    ),
    "github-actions": Adapter(
        identifier="github-actions",
        family="ci",
        display_name="GitHub Actions",
        capabilities=(
            _cap("ci.status.read", "Read checks and workflow run status."),
            _cap("ci.logs.read", "Read workflow jobs, annotations, and logs."),
            _cap("ci.run", "Dispatch or rerun workflows.", mutating=True),
        ),
        preflight=(
            "Confirm GitHub Actions checks or workflow runs are readable for the pull request.",
            "Treat workflow dispatch and rerun permission as separate from log access.",
        ),
        evidence=(
            "Use check conclusions, annotations, and focused failing job excerpts; distinguish branch and pull-request runs.",
        ),
        publishing=(
            "Require explicit confirmation before dispatching or rerunning a GitHub Actions workflow.",
        ),
    ),
    "azure-pipelines": Adapter(
        identifier="azure-pipelines",
        family="ci",
        display_name="Azure Pipelines",
        capabilities=(
            _cap("ci.status.read", "Read build and pipeline status."),
            _cap("ci.logs.read", "Read pipeline timelines, issues, and logs."),
            _cap("ci.run", "Queue or retry pipeline runs.", mutating=True),
        ),
        preflight=(
            "Confirm Azure Pipelines builds for the pull request are readable.",
            "Treat queue and retry permission as separate from timeline/log access.",
        ),
        evidence=(
            "Use build results, timeline issues, and focused failing task excerpts; verify the source version.",
        ),
        publishing=(
            "Require explicit confirmation before queuing or retrying an Azure Pipelines run.",
        ),
    ),
    "local-git": Adapter(
        identifier="local-git",
        family="local",
        display_name="Local Git",
        capabilities=(
            _cap("local.git.metadata", "Read branches, remotes, and commit metadata."),
            _cap("local.git.diff", "Read local diffs and file history."),
            _cap("local.commands", "Run local validation commands.", mutating=False),
        ),
        preflight=(
            "Confirm the checkout and base/head revisions before interpreting a local diff.",
            "Report dirty working-tree changes separately from pull request changes.",
        ),
        evidence=(
            "Use merge-base diffs, blame/history when relevant, repository guidance, and reproducible local validation output.",
        ),
    ),
}


ALIASES = {
    "ado": "azure-devops",
    "azure": "azure-devops",
    "azure-repos": "azure-devops",
    "github-projects": "github-issues",
    "github-issues-projects": "github-issues",
    "boards": "azure-boards",
    "azureboards": "azure-boards",
    "ms-teams": "teams",
    "google-mail": "gmail",
    "local_git": "local-git",
    "git": "local-git",
    "continuous-integration": "ci",
    "github-workflows": "github-actions",
    "actions": "github-actions",
    "ado-pipelines": "azure-pipelines",
}


def profile_mapping(profile: object) -> Mapping[str, Any]:
    """Convert dataclasses, Pydantic models, mappings, or simple objects."""

    if isinstance(profile, Mapping):
        return profile
    for method_name in ("model_dump", "dict", "to_dict"):
        method = getattr(profile, method_name, None)
        if callable(method):
            value = method()
            if isinstance(value, Mapping):
                return value
    data = getattr(profile, "__dict__", None)
    if isinstance(data, Mapping):
        return data
    raise TypeError("profile must be a mapping or expose model_dump(), dict(), or to_dict()")


def normalize_adapter_id(value: str) -> str:
    identifier = value.strip().lower().replace("_", "-").replace(" ", "-")
    return ALIASES.get(identifier, identifier)


def _is_enabled(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"confirmed", "enabled", "available", "true", "yes"}
    if isinstance(value, Mapping):
        state = value.get("confirmed", value.get("enabled", value.get("available", True)))
        return _is_enabled(state) if state is not value else True
    return value is not None


def _collect_adapter_ids(value: object) -> Iterable[str]:
    if isinstance(value, Enum):
        yield from _collect_adapter_ids(value.value)
    elif isinstance(value, str):
        yield normalize_adapter_id(value)
    elif isinstance(value, Mapping):
        explicit = value.get("id", value.get("identifier", value.get("adapter")))
        if explicit is not None and _is_enabled(value):
            yield from _collect_adapter_ids(explicit)
        for key, nested in value.items():
            normalized = normalize_adapter_id(str(key))
            if normalized in ADAPTERS and _is_enabled(nested):
                yield normalized
            elif key in {"adapters", "integrations", "selected", "enabled"}:
                yield from _collect_adapter_ids(nested)
    elif isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            yield from _collect_adapter_ids(item)
    elif value is not None:
        try:
            yield from _collect_adapter_ids(profile_mapping(value))
        except TypeError:
            return


def selected_adapters(profile: object) -> tuple[Adapter, ...]:
    """Resolve confirmed adapters without depending on a concrete Profile model."""

    data = profile_mapping(profile)
    candidates: list[str] = []
    for key in (
        "adapter_ids",
        "adapters",
        "integrations",
        "selected_adapters",
        "capabilities",
        "code_host",
        "trackers",
        "tracker",
        "communication",
        "ci",
        "ci_provider",
        "local",
    ):
        if key in data:
            candidates.extend(_collect_adapter_ids(data[key]))

    seen: set[str] = set()
    resolved: list[Adapter] = []
    for identifier in candidates:
        if identifier in ADAPTERS and identifier not in seen:
            seen.add(identifier)
            resolved.append(ADAPTERS[identifier])
    return tuple(resolved)


def capability_names(adapters: Iterable[Adapter]) -> frozenset[str]:
    return frozenset(
        capability.name for adapter in adapters for capability in adapter.capabilities
    )
