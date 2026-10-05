"""Render a portable, vendor-neutral pull-request review Agent Skill."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from .adapters import Adapter, profile_mapping, selected_adapters


TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"
SUPPORTED_PROVIDERS = frozenset({"portable", "copilot", "claude"})


@dataclass(frozen=True)
class RenderedPackage(Mapping[str, str]):
    files: Mapping[str, str]
    source_hash: str

    def __getitem__(self, key: str) -> str:
        return self.files[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.files)

    def __len__(self) -> int:
        return len(self.files)


def _profile_value(data: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return default


def _render_template(name: str, replacements: Mapping[str, str]) -> str:
    text = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    unresolved = [part.split("}}", 1)[0] for part in text.split("{{")[1:] if "}}" in part]
    if unresolved:
        raise ValueError(f"unresolved template variables in {name}: {', '.join(unresolved)}")
    return text.rstrip() + "\n"


def _frontmatter(provider: str) -> str:
    common = [
        "---",
        "name: pr-review",
        "description: >",
        "  Evidence-backed pull-request review with capability preflight, normalized findings,",
        "  structural deduplication, safe previews, and optional confirmed publishing.",
        "license: MIT",
    ]
    if provider == "claude":
        common.extend(
            (
                'argument-hint: "[pull-request-or-branch] [--publish] [--iterate]"',
                "user-invocable: true",
            )
        )
    common.append("---")
    return "\n".join(common)


def _adapter_reference(
    adapters: Iterable[Adapter],
    data: Mapping[str, Any],
) -> str:
    adapters = tuple(adapters)
    if not adapters:
        return (
            "# Stack and integration reference\n\n"
            "No integration adapter was confirmed. Work only with evidence explicitly supplied "
            "by the user, report unavailable evidence, and do not claim publishing capability.\n"
        )

    lines = [
        "# Stack and integration reference",
        "",
        "This file is generated from confirmed profile adapters. Re-run capability preflight",
        "at review time because credentials and tool availability can change.",
        "",
    ]
    raw_bindings = data.get("tool_bindings", {})
    tool_bindings = raw_bindings if isinstance(raw_bindings, Mapping) else {}
    for adapter in adapters:
        lines.extend((f"## {adapter.display_name}", "", f"- Adapter: `{adapter.identifier}`"))
        lines.append(f"- Family: `{adapter.family}`")
        bindings = tool_bindings.get(adapter.identifier, ())
        if isinstance(bindings, str):
            bindings = (bindings,)
        if isinstance(bindings, Iterable) and not isinstance(
            bindings, (Mapping, bytes, bytearray)
        ):
            names = tuple(str(item) for item in bindings)
            if names:
                lines.append(
                    "- Detected tool bindings: "
                    + ", ".join(f"`{name}`" for name in names)
                )
        lines.append("- Capabilities:")
        for capability in adapter.capabilities:
            mode = "write/side effect" if capability.mutating else "read/local"
            lines.append(f"  - `{capability.name}` ({mode}) — {capability.description}")
        lines.append("- Preflight:")
        lines.extend(f"  - {item}" for item in adapter.preflight)
        lines.append("- Evidence guidance:")
        lines.extend(f"  - {item}" for item in adapter.evidence)
        if adapter.publishing:
            lines.append("- Publishing guidance:")
            lines.extend(f"  - {item}" for item in adapter.publishing)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _profile_reference(data: Mapping[str, Any], adapters: Iterable[Adapter]) -> str:
    message_prefix = str(
        _profile_value(data, "message_prefix", "external_message_prefix", default="")
    ).strip()
    stack = _profile_value(data, "stack", "languages", "technology_stack", default=[])
    if isinstance(stack, str):
        stack_items = [stack]
    elif isinstance(stack, Iterable) and not isinstance(stack, (Mapping, bytes, bytearray)):
        stack_items = [str(item) for item in stack]
    else:
        stack_items = []

    lines = [
        "# Confirmed profile",
        "",
        f"- Message prefix: `{message_prefix}`" if message_prefix else "- Message prefix: empty",
        "- Adapters: "
        + (", ".join(f"`{item.identifier}`" for item in adapters) or "none confirmed"),
        "- Stack hints: " + (", ".join(stack_items) or "none"),
        "",
        "Profile values are hints, not evidence. Verify repository state and capabilities at runtime.",
    ]
    return "\n".join(lines) + "\n"


def _validate_script() -> str:
    return (TEMPLATE_ROOT / "scripts" / "validate_findings.py").read_text(encoding="utf-8")


def render_skill(profile: object, provider: str = "portable") -> RenderedPackage:
    """Render all files for one provider without writing to disk."""

    provider = provider.strip().lower()
    if provider in {"github-copilot", "github_copilot"}:
        provider = "copilot"
    if provider in {"claude-code", "claude_code"}:
        provider = "claude"
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"unsupported provider: {provider}")

    data = profile_mapping(profile)
    adapters = selected_adapters(data)
    files = {
        "SKILL.md": _render_template(
            "SKILL.md",
            {
                "FRONTMATTER": _frontmatter(provider),
                "PROFILE_SUMMARY": (
                    ", ".join(adapter.display_name for adapter in adapters)
                    or "No confirmed integrations"
                ),
            },
        ),
        "references/review-rubric.md": _render_template("references/review-rubric.md", {}),
        "references/finding-schema.md": _render_template("references/finding-schema.md", {}),
        "references/publishing.md": _render_template("references/publishing.md", {}),
        "references/iteration.md": _render_template("references/iteration.md", {}),
        "references/stack.md": _adapter_reference(adapters, data),
        "references/profile.md": _profile_reference(data, adapters),
        "scripts/validate_findings.py": _validate_script().rstrip() + "\n",
    }
    digest = sha256()
    for path, content in sorted(files.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content.encode("utf-8"))
        digest.update(b"\0")
    return RenderedPackage(files=files, source_hash=digest.hexdigest())


def render_package(profile: object, provider: str = "portable") -> dict[str, str]:
    """Compatibility API returning a plain path-to-content mapping."""

    return dict(render_skill(profile, provider).files)


def write_rendered_skill(
    profile: object,
    destination: str | Path,
    provider: str = "portable",
) -> RenderedPackage:
    """Write a rendered package below destination, rejecting path traversal."""

    package = render_skill(profile, provider)
    root = Path(destination)
    for relative, content in package.files.items():
        path = root / relative
        if root.resolve() not in path.resolve().parents:
            raise ValueError(f"rendered path escapes destination: {relative}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return package


def render_manifest(package: RenderedPackage) -> str:
    """Return deterministic metadata suitable for installer ownership tracking."""

    payload = {
        "source_hash": package.source_hash,
        "files": sorted(package.files),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
