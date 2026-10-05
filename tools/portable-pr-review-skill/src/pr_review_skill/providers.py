"""Provider selection and destination conventions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from .models import CapabilityState, Profile, Provider, ProviderChoice, Scope


class ProviderSelectionError(ValueError):
    """Raised when provider selection cannot be resolved safely."""


@dataclass(frozen=True, slots=True)
class ProviderDestination:
    provider: Provider
    scope: Scope
    root: Path

    @property
    def skill_directory(self) -> Path:
        return self.root / "pr-review"


def destination_for(
    provider: Provider,
    scope: Scope,
    repository_root: Path,
    *,
    home: Path | None = None,
) -> ProviderDestination:
    home = (home or Path.home()).expanduser()
    repository_root = repository_root.expanduser().resolve()
    if provider is Provider.COPILOT:
        root = (
            repository_root / ".github" / "skills"
            if scope is Scope.PROJECT
            else home / ".copilot" / "skills"
        )
    else:
        root = (
            repository_root / ".claude" / "skills"
            if scope is Scope.PROJECT
            else home / ".claude" / "skills"
        )
    return ProviderDestination(provider=provider, scope=scope, root=root)


def detected_providers(profile: Profile) -> tuple[Provider, ...]:
    result: list[Provider] = []
    for provider in Provider:
        capability = profile.capability(f"provider.{provider.value}")
        if capability.state in {
            CapabilityState.AVAILABLE,
            CapabilityState.AMBIGUOUS,
        }:
            result.append(provider)
    return tuple(result)


def resolve_providers(
    profile: Profile,
    choice: ProviderChoice | str | None = None,
    *,
    interactive: bool = False,
    prompt: Callable[[str], str] = input,
) -> tuple[Provider, ...]:
    selected = ProviderChoice(choice or profile.provider_choice)
    explicit = selected.providers()
    if explicit:
        return explicit
    if not interactive:
        raise ProviderSelectionError(
            "Provider choice is 'ask'. Pass --provider copilot, claude, or both."
        )

    candidates = detected_providers(profile)
    hint = ", ".join(item.value for item in candidates) or "none detected"
    answer = prompt(
        "Install for [copilot/claude/both] "
        f"(local evidence: {hint}): "
    ).strip().lower()
    try:
        selected = ProviderChoice(answer)
    except ValueError as exc:
        raise ProviderSelectionError(
            "Expected one of: copilot, claude, both."
        ) from exc
    if selected is ProviderChoice.ASK:
        raise ProviderSelectionError("A concrete provider choice is required.")
    return selected.providers()


def destinations(
    providers: Iterable[Provider],
    scope: Scope,
    repository_root: Path,
    *,
    home: Path | None = None,
) -> tuple[ProviderDestination, ...]:
    return tuple(
        destination_for(provider, scope, repository_root, home=home)
        for provider in providers
    )
