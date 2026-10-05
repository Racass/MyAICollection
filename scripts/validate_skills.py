#!/usr/bin/env python3
"""Validate the repository's Agent Skills and obvious sensitive files."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
RESERVED_NAME_WORDS = {"anthropic", "claude"}
SENSITIVE_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json"}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}


@dataclass(frozen=True)
class ValidationError:
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[ValidationError]]:
    errors: list[ValidationError] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {}, [ValidationError(path, f"cannot read UTF-8 content: {exc}")]

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [ValidationError(path, "must start with YAML frontmatter")]

    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, [ValidationError(path, "frontmatter is missing its closing --- delimiter")]

    metadata: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(
                ValidationError(path, f"frontmatter line {line_number} must use key: value")
            )
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if not key or not value:
            errors.append(
                ValidationError(path, f"frontmatter line {line_number} has an empty key or value")
            )
            continue
        if key in metadata:
            errors.append(ValidationError(path, f"frontmatter key {key!r} is duplicated"))
            continue
        metadata[key] = value

    if not any(line.strip() for line in lines[end + 1 :]):
        errors.append(ValidationError(path, "must include instructions after frontmatter"))

    return metadata, errors


def validate_local_links(path: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    text = path.read_text(encoding="utf-8")
    for raw_target in MARKDOWN_LINK_PATTERN.findall(text):
        target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
        target = target.split("#", 1)[0]
        if (
            not target
            or target.startswith(("#", "/", "\\"))
            or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE)
        ):
            continue
        linked_path = (path.parent / target).resolve()
        if not linked_path.exists():
            errors.append(ValidationError(path, f"relative link target does not exist: {target}"))
    return errors


def validate_skill(skill_dir: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.is_file():
        errors.append(ValidationError(skill_dir, "must contain a file named exactly SKILL.md"))
        return errors

    metadata, frontmatter_errors = parse_frontmatter(skill_file)
    errors.extend(frontmatter_errors)

    name = metadata.get("name", "")
    description = metadata.get("description", "")

    if not name:
        errors.append(ValidationError(skill_file, "frontmatter requires a name"))
    else:
        if len(name) > 64:
            errors.append(ValidationError(skill_file, "name must be at most 64 characters"))
        if not NAME_PATTERN.fullmatch(name):
            errors.append(
                ValidationError(
                    skill_file,
                    "name must contain only lowercase letters, numbers, and single hyphens",
                )
            )
        if name != skill_dir.name:
            errors.append(
                ValidationError(
                    skill_file,
                    f"name {name!r} must match directory {skill_dir.name!r}",
                )
            )
        words = set(name.split("-"))
        reserved = sorted(words & RESERVED_NAME_WORDS)
        if reserved:
            errors.append(
                ValidationError(
                    skill_file,
                    f"name contains reserved word(s): {', '.join(reserved)}",
                )
            )

    if not description:
        errors.append(ValidationError(skill_file, "frontmatter requires a description"))
    elif len(description) > 1024:
        errors.append(ValidationError(skill_file, "description must be at most 1024 characters"))

    for markdown_file in skill_dir.rglob("*.md"):
        try:
            errors.extend(validate_local_links(markdown_file))
        except (OSError, UnicodeError) as exc:
            errors.append(
                ValidationError(markdown_file, f"cannot validate Markdown links: {exc}")
            )

    return errors


def validate_sensitive_files(root: Path) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        name = path.name.lower()
        if name in SENSITIVE_NAMES or path.suffix.lower() in SENSITIVE_SUFFIXES:
            errors.append(ValidationError(path, "potential secret or private-key file must not be committed"))
            continue
        if path.stat().st_size <= 1_000_000:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if PRIVATE_KEY_PATTERN.search(text):
                errors.append(ValidationError(path, "contains a private-key header"))
    return errors


def validate_repository(root: Path) -> list[ValidationError]:
    root = root.resolve()
    skills_dir = root / ".claude" / "skills"
    errors: list[ValidationError] = []

    if not skills_dir.is_dir():
        errors.append(ValidationError(skills_dir, "canonical skills directory does not exist"))
    else:
        skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
        if not skill_dirs:
            errors.append(ValidationError(skills_dir, "must contain at least one skill"))
        for skill_dir in skill_dirs:
            errors.extend(validate_skill(skill_dir))

        unexpected_files = sorted(path for path in skills_dir.iterdir() if path.is_file())
        for path in unexpected_files:
            errors.append(ValidationError(path, "skills root may contain only skill directories"))

    errors.extend(validate_sensitive_files(root))
    return sorted(errors, key=lambda error: (str(error.path), error.message))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of scripts/)",
    )
    args = parser.parse_args()

    errors = validate_repository(args.root)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Validated 1 or more Agent Skills successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
