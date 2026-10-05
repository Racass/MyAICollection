"""Idempotent installation, diagnostics, and conservative removal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import difflib
import hashlib
import importlib
import json
from pathlib import Path
import shutil
from typing import Callable, Mapping

from .models import Profile, Provider, ProviderChoice, Scope
from .providers import destinations, resolve_providers

METADATA_FILE = ".pr-review-skill-meta.json"
METADATA_SCHEMA_VERSION = 1


class InstallError(RuntimeError):
    """Raised when an install operation cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class InstallResult:
    provider: Provider
    destination: Path
    status: str
    source_hash: str
    backup: Path | None = None
    diff: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "destination": str(self.destination),
            "status": self.status,
            "source_hash": self.source_hash,
            "backup": str(self.backup) if self.backup else None,
            "diff": self.diff,
        }


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    ok: bool
    message: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "ok": self.ok, "message": self.message}


@dataclass(slots=True)
class DoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {"ok": self.ok, "checks": [check.to_dict() for check in self.checks]}

    def format_text(self) -> str:
        return "\n".join(
            f"{'OK' if item.ok else 'ERROR'} {item.name}: {item.message}"
            for item in self.checks
        )


def install(
    profile: Profile,
    *,
    provider_choice: ProviderChoice | str | None = None,
    scope: Scope | str = Scope.PROJECT,
    interactive: bool = False,
    prompt: Callable[[str], str] = input,
    home: Path | None = None,
    renderer: Callable[[Profile, Provider], Mapping[str, str | bytes]] | None = None,
    dry_run: bool = False,
) -> tuple[InstallResult, ...]:
    profile.validate()
    _validate_adapters(profile)
    if not profile.confirmed:
        raise InstallError(
            "Profile is not confirmed. Review detection evidence and confirm it first."
        )
    providers = resolve_providers(
        profile,
        provider_choice,
        interactive=interactive,
        prompt=prompt,
    )
    render = renderer or _load_renderer()
    targets = destinations(
        providers,
        Scope(scope),
        profile.repository_root,
        home=home,
    )
    rendered = {
        target.provider: _normalize_rendered_files(render(profile, target.provider))
        for target in targets
    }
    for target in targets:
        _validate_destination(target.skill_directory)

    results: list[InstallResult] = []
    for target in targets:
        results.append(
            _install_one(
                target.provider,
                target.skill_directory,
                rendered[target.provider],
                profile,
                dry_run=dry_run,
            )
        )
    return tuple(results)


def doctor(
    profile: Profile,
    *,
    provider_choice: ProviderChoice | str | None = None,
    scope: Scope | str = Scope.PROJECT,
    home: Path | None = None,
) -> DoctorReport:
    report = DoctorReport()
    try:
        profile.validate()
        _validate_adapters(profile)
        report.checks.append(DoctorCheck("profile", True, "Schema is valid."))
    except (ValueError, InstallError) as exc:
        report.checks.append(DoctorCheck("profile", False, str(exc)))
        return report
    report.checks.append(
        DoctorCheck(
            "confirmation",
            profile.confirmed,
            "Profile is confirmed." if profile.confirmed else "Profile is not confirmed.",
        )
    )
    try:
        selected = resolve_providers(profile, provider_choice, interactive=False)
    except ValueError as exc:
        report.checks.append(DoctorCheck("providers", False, str(exc)))
        return report

    for target in destinations(
        selected, Scope(scope), profile.repository_root, home=home
    ):
        skill_dir = target.skill_directory
        metadata_path = skill_dir / METADATA_FILE
        if not skill_dir.is_dir():
            report.checks.append(
                DoctorCheck(
                    f"{target.provider.value}.destination",
                    False,
                    f"Skill directory is missing: {skill_dir}",
                )
            )
            continue
        metadata = _read_metadata(metadata_path)
        if metadata is None:
            report.checks.append(
                DoctorCheck(
                    f"{target.provider.value}.metadata",
                    False,
                    f"Ownership metadata is missing or invalid: {metadata_path}",
                )
            )
            continue
        expected = metadata.get("source_hash")
        actual = _hash_owned_files(skill_dir, metadata)
        report.checks.append(
            DoctorCheck(
                f"{target.provider.value}.hash",
                isinstance(expected, str) and expected == actual,
                "Installed files match metadata."
                if expected == actual
                else "Installed files differ from recorded generated content.",
            )
        )
    return report


def uninstall(
    profile: Profile,
    *,
    provider_choice: ProviderChoice | str | None = None,
    scope: Scope | str = Scope.PROJECT,
    home: Path | None = None,
    dry_run: bool = False,
) -> tuple[InstallResult, ...]:
    selected = resolve_providers(profile, provider_choice, interactive=False)
    results: list[InstallResult] = []
    for target in destinations(
        selected, Scope(scope), profile.repository_root, home=home
    ):
        skill_dir = target.skill_directory
        metadata = _read_metadata(skill_dir / METADATA_FILE)
        if metadata is None:
            status = "not-installed" if not skill_dir.exists() else "refused-unowned"
            results.append(
                InstallResult(target.provider, skill_dir, status, source_hash="")
            )
            continue
        owned_files = _owned_files(metadata)
        modified = [
            relative
            for relative in owned_files
            if (skill_dir / relative).is_file()
            and _file_hash(skill_dir / relative)
            != _metadata_file_hash(metadata, relative)
        ]
        if modified:
            results.append(
                InstallResult(
                    target.provider,
                    skill_dir,
                    "refused-modified",
                    source_hash=str(metadata.get("source_hash", "")),
                    diff=", ".join(modified),
                )
            )
            continue
        if not dry_run:
            for relative in owned_files:
                (skill_dir / relative).unlink(missing_ok=True)
            (skill_dir / METADATA_FILE).unlink(missing_ok=True)
            _remove_empty_directories(skill_dir)
        results.append(
            InstallResult(
                target.provider,
                skill_dir,
                "would-remove" if dry_run else "removed",
                source_hash=str(metadata.get("source_hash", "")),
            )
        )
    return tuple(results)


def _install_one(
    provider: Provider,
    destination: Path,
    files: dict[str, bytes],
    profile: Profile,
    *,
    dry_run: bool,
) -> InstallResult:
    source_hash = _hash_files(files)
    old_metadata = _read_metadata(destination / METADATA_FILE)
    if (
        old_metadata
        and old_metadata.get("source_hash") == source_hash
        and _hash_owned_files(destination, old_metadata) == source_hash
    ):
        return InstallResult(provider, destination, "unchanged", source_hash)

    if destination.exists() and any(destination.iterdir()) and old_metadata is None:
        raise InstallError(
            f"Refusing to replace unowned non-empty directory: {destination}"
        )

    diff = _directory_diff(destination, files, old_metadata)
    backup: Path | None = None
    if destination.exists() and any(destination.iterdir()):
        backup = _backup_path(destination)
        if not dry_run:
            shutil.copytree(destination, backup)

    if dry_run:
        return InstallResult(
            provider,
            destination,
            "would-update" if old_metadata else "would-install",
            source_hash,
            backup=backup,
            diff=diff,
        )

    if destination.exists():
        if old_metadata:
            for relative in _owned_files(old_metadata):
                (destination / relative).unlink(missing_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    for relative, content in files.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    metadata = {
        "schema_version": METADATA_SCHEMA_VERSION,
        "generator": "portable-pr-review-skill",
        "provider": provider.value,
        "installed_at": datetime.now(UTC).isoformat(),
        "profile_schema_version": profile.schema_version,
        "profile_repository": profile.repository.get("remote", profile.repository_root.name),
        "source_hash": source_hash,
        "files": {
            relative: hashlib.sha256(content).hexdigest()
            for relative, content in sorted(files.items())
        },
        "backup": str(backup) if backup else None,
    }
    (destination / METADATA_FILE).write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return InstallResult(
        provider,
        destination,
        "installed" if old_metadata is None else "updated",
        source_hash,
        backup=backup,
        diff=diff,
    )


def _validate_adapters(profile: Profile) -> None:
    from .adapters import ADAPTERS

    unknown = sorted(set(profile.adapter_ids) - set(ADAPTERS))
    if unknown:
        raise InstallError(f"Unknown adapter identifiers: {', '.join(unknown)}")


def _validate_destination(destination: Path) -> None:
    if (
        destination.exists()
        and any(destination.iterdir())
        and _read_metadata(destination / METADATA_FILE) is None
    ):
        raise InstallError(
            f"Refusing to replace unowned non-empty directory: {destination}"
        )


def _load_renderer() -> Callable[[Profile, Provider], Mapping[str, str | bytes]]:
    try:
        module = importlib.import_module(".rendering", package=__package__)
        renderer = getattr(module, "render_skill")
    except (ImportError, AttributeError) as exc:
        raise InstallError(
            "Rendering module is unavailable; expected "
            "pr_review_skill.rendering.render_skill(profile, provider)."
        ) from exc
    return renderer


def _normalize_rendered_files(
    rendered: Mapping[str, str | bytes],
) -> dict[str, bytes]:
    if not isinstance(rendered, Mapping) or not rendered:
        raise InstallError("Renderer must return a non-empty mapping of relative paths.")
    files: dict[str, bytes] = {}
    for raw_path, raw_content in rendered.items():
        relative = Path(raw_path)
        if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
            raise InstallError(f"Renderer returned unsafe path: {raw_path!r}")
        if isinstance(raw_content, str):
            content = raw_content.encode("utf-8")
        elif isinstance(raw_content, bytes):
            content = raw_content
        else:
            raise InstallError(f"Renderer content for {raw_path!r} is not text or bytes.")
        files[relative.as_posix()] = content
    return files


def _hash_files(files: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative, content in sorted(files.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_metadata(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        not isinstance(value, dict)
        or value.get("generator") != "portable-pr-review-skill"
        or value.get("schema_version") != METADATA_SCHEMA_VERSION
        or not isinstance(value.get("files"), dict)
    ):
        return None
    return value


def _owned_files(metadata: Mapping[str, object]) -> tuple[str, ...]:
    files = metadata.get("files", {})
    if not isinstance(files, Mapping):
        return ()
    return tuple(str(path) for path in files)


def _metadata_file_hash(metadata: Mapping[str, object], relative: str) -> str:
    files = metadata.get("files", {})
    if not isinstance(files, Mapping):
        return ""
    value = files.get(relative)
    return value if isinstance(value, str) else ""


def _hash_owned_files(directory: Path, metadata: Mapping[str, object]) -> str:
    files: dict[str, bytes] = {}
    for relative in _owned_files(metadata):
        path = directory / relative
        if not path.is_file():
            return ""
        files[relative] = path.read_bytes()
    return _hash_files(files)


def _directory_diff(
    destination: Path,
    files: Mapping[str, bytes],
    metadata: Mapping[str, object] | None,
) -> str:
    previous = set(_owned_files(metadata or {}))
    lines: list[str] = []
    for relative in sorted(previous | set(files)):
        old_path = destination / relative
        old = (
            old_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if old_path.is_file()
            else []
        )
        new = files.get(relative, b"").decode("utf-8", errors="replace").splitlines()
        if old != new:
            lines.extend(
                difflib.unified_diff(
                    old,
                    new,
                    fromfile=f"installed/{relative}",
                    tofile=f"generated/{relative}",
                    lineterm="",
                )
            )
    return "\n".join(lines)


def _backup_path(destination: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    candidate = destination.with_name(f"{destination.name}.backup.{timestamp}")
    counter = 1
    while candidate.exists():
        candidate = destination.with_name(
            f"{destination.name}.backup.{timestamp}.{counter}"
        )
        counter += 1
    return candidate


def _remove_empty_directories(root: Path) -> None:
    if not root.exists():
        return
    for path in sorted(
        (item for item in root.rglob("*") if item.is_dir()),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        try:
            path.rmdir()
        except OSError:
            pass
    try:
        root.rmdir()
    except OSError:
        pass
