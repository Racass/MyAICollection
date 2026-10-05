"""Serializable domain models for detection, rendering, and installation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import json
from pathlib import Path
from typing import Any, Mapping

PROFILE_SCHEMA = "pr-review-skill/profile"
PROFILE_SCHEMA_VERSION = 1


class ProfileError(ValueError):
    """Raised when a profile is invalid or incompatible."""


class CapabilityState(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    AMBIGUOUS = "ambiguous"
    UNVERIFIED = "unverified"


class Provider(StrEnum):
    COPILOT = "copilot"
    CLAUDE = "claude"


class ProviderChoice(StrEnum):
    COPILOT = "copilot"
    CLAUDE = "claude"
    BOTH = "both"
    ASK = "ask"

    def providers(self) -> tuple[Provider, ...]:
        if self is ProviderChoice.COPILOT:
            return (Provider.COPILOT,)
        if self is ProviderChoice.CLAUDE:
            return (Provider.CLAUDE,)
        if self is ProviderChoice.BOTH:
            return (Provider.COPILOT, Provider.CLAUDE)
        return ()


class Scope(StrEnum):
    PROJECT = "project"
    PERSONAL = "personal"


@dataclass(frozen=True, slots=True)
class DetectionEvidence:
    """A credential-free fact supporting a capability state."""

    kind: str
    summary: str
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"kind": self.kind, "summary": self.summary}
        if self.path is not None:
            result["path"] = self.path
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> DetectionEvidence:
        return cls(
            kind=_required_str(value, "kind"),
            summary=_required_str(value, "summary"),
            path=_optional_str(value.get("path")),
        )


@dataclass(frozen=True, slots=True)
class Capability:
    """A named capability and the local evidence used to classify it."""

    name: str
    state: CapabilityState
    evidence: tuple[DetectionEvidence, ...] = ()
    details: str | None = None

    @property
    def available(self) -> bool:
        return self.state is CapabilityState.AVAILABLE

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "state": self.state.value,
            "evidence": [item.to_dict() for item in self.evidence],
        }
        if self.details is not None:
            result["details"] = self.details
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Capability:
        try:
            state = CapabilityState(_required_str(value, "state"))
        except ValueError as exc:
            raise ProfileError(f"Unknown capability state: {value.get('state')!r}") from exc
        raw_evidence = value.get("evidence", [])
        if not isinstance(raw_evidence, list):
            raise ProfileError("Capability evidence must be a list.")
        return cls(
            name=_required_str(value, "name"),
            state=state,
            evidence=tuple(DetectionEvidence.from_dict(item) for item in raw_evidence),
            details=_optional_str(value.get("details")),
        )


@dataclass(slots=True)
class Profile:
    """Versioned, portable input consumed by a rendering implementation."""

    repository_root: Path
    capabilities: dict[str, Capability]
    provider_choice: ProviderChoice = ProviderChoice.ASK
    confirmed: bool = False
    detected_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    repository: dict[str, str] = field(default_factory=dict)
    adapter_ids: tuple[str, ...] = ()
    tool_bindings: dict[str, tuple[str, ...]] = field(default_factory=dict)
    schema: str = PROFILE_SCHEMA
    schema_version: int = PROFILE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.expanduser().resolve()
        self.validate()

    def validate(self) -> None:
        if self.schema != PROFILE_SCHEMA:
            raise ProfileError(
                f"Unsupported profile schema {self.schema!r}; expected {PROFILE_SCHEMA!r}."
            )
        if self.schema_version != PROFILE_SCHEMA_VERSION:
            raise ProfileError(
                f"Unsupported profile schema version {self.schema_version}; "
                f"expected {PROFILE_SCHEMA_VERSION}."
            )
        if not isinstance(self.confirmed, bool):
            raise ProfileError("'confirmed' must be a boolean.")
        for key, capability in self.capabilities.items():
            if key != capability.name:
                raise ProfileError(
                    f"Capability key {key!r} does not match name {capability.name!r}."
                )

    def capability(self, name: str) -> Capability:
        return self.capabilities.get(
            name,
            Capability(name=name, state=CapabilityState.UNVERIFIED),
        )

    def available(self, name: str) -> bool:
        return self.capability(name).available

    def to_dict(self) -> dict[str, Any]:
        return {
            "$schema": self.schema,
            "schema_version": self.schema_version,
            "detected_at": self.detected_at,
            "repository_root": str(self.repository_root),
            "repository": dict(sorted(self.repository.items())),
            "adapter_ids": list(self.adapter_ids),
            "tool_bindings": {
                name: list(bindings)
                for name, bindings in sorted(self.tool_bindings.items())
            },
            "provider_choice": self.provider_choice.value,
            "confirmed": self.confirmed,
            "capabilities": {
                name: capability.to_dict()
                for name, capability in sorted(self.capabilities.items())
            },
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False) + "\n"

    def save(self, path: Path) -> None:
        path = path.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Profile:
        raw_capabilities = value.get("capabilities")
        if not isinstance(raw_capabilities, Mapping):
            raise ProfileError("'capabilities' must be an object.")
        capabilities = {
            str(name): Capability.from_dict(item)
            for name, item in raw_capabilities.items()
            if isinstance(item, Mapping)
        }
        if len(capabilities) != len(raw_capabilities):
            raise ProfileError("Every capability must be an object.")
        try:
            provider_choice = ProviderChoice(
                _required_str(value, "provider_choice", default=ProviderChoice.ASK.value)
            )
        except ValueError as exc:
            raise ProfileError(
                f"Unknown provider choice: {value.get('provider_choice')!r}"
            ) from exc
        schema = value.get("$schema", value.get("schema", PROFILE_SCHEMA))
        return cls(
            schema=_required_str({"schema": schema}, "schema"),
            schema_version=_required_int(
                value, "schema_version", default=PROFILE_SCHEMA_VERSION
            ),
            detected_at=_required_str(
                value, "detected_at", default=datetime.now(UTC).isoformat()
            ),
            repository_root=Path(_required_str(value, "repository_root")),
            repository={
                str(key): str(item)
                for key, item in _mapping(value.get("repository", {}), "repository").items()
            },
            adapter_ids=tuple(
                str(item)
                for item in _list(value.get("adapter_ids", []), "adapter_ids")
            ),
            tool_bindings={
                str(name): tuple(str(item) for item in _list(bindings, str(name)))
                for name, bindings in _mapping(
                    value.get("tool_bindings", {}), "tool_bindings"
                ).items()
            },
            provider_choice=provider_choice,
            confirmed=value.get("confirmed", False),
            capabilities=capabilities,
        )

    @classmethod
    def load(cls, path: Path) -> Profile:
        try:
            raw = json.loads(path.expanduser().read_text(encoding="utf-8"))
        except OSError as exc:
            raise ProfileError(f"Cannot read profile {path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ProfileError(f"Invalid JSON in profile {path}: {exc}") from exc
        if not isinstance(raw, Mapping):
            raise ProfileError("Profile root must be a JSON object.")
        return cls.from_dict(raw)


def _required_str(
    value: Mapping[str, Any], key: str, *, default: str | None = None
) -> str:
    item = value.get(key, default)
    if not isinstance(item, str) or not item:
        raise ProfileError(f"'{key}' must be a non-empty string.")
    return item


def _required_int(
    value: Mapping[str, Any], key: str, *, default: int | None = None
) -> int:
    item = value.get(key, default)
    if not isinstance(item, int) or isinstance(item, bool):
        raise ProfileError(f"'{key}' must be an integer.")
    return item


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProfileError("Optional text fields must be strings.")
    return value


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProfileError(f"'{field_name}' must be an object.")
    return value


def _list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ProfileError(f"'{field_name}' must be a list.")
    return value
