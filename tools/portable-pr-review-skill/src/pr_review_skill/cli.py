"""Command-line interface for detection and lifecycle operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .detection import DetectionReport, detect_profile
from .installer import InstallError, doctor, install, uninstall
from .models import Profile, ProfileError, ProviderChoice, Scope


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr-review-skill",
        description="Generate and manage a portable PR review skill.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser(
        "detect", help="Inspect local repository evidence without network access."
    )
    detect.add_argument("--repository", type=Path, default=Path.cwd())
    detect.add_argument("--output", type=Path)
    detect.add_argument(
        "--provider",
        choices=[item.value for item in ProviderChoice],
        default=ProviderChoice.ASK.value,
    )
    detect.add_argument(
        "--confirm",
        action="store_true",
        help="Mark the saved profile confirmed after reviewing this run's report.",
    )
    detect.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt to confirm the displayed report.",
    )
    detect.add_argument("--json", action="store_true", help="Print JSON report.")

    setup = subparsers.add_parser(
        "setup",
        help="Detect, confirm, save, and install in one interactive flow.",
    )
    setup.add_argument("--repository", type=Path, default=Path.cwd())
    setup.add_argument("--profile", type=Path)
    setup.add_argument(
        "--provider",
        choices=[item.value for item in ProviderChoice],
        default=ProviderChoice.ASK.value,
    )
    setup.add_argument(
        "--scope",
        choices=[item.value for item in Scope],
        default=Scope.PROJECT.value,
    )
    setup.add_argument("--dry-run", action="store_true")
    setup.add_argument("--json", action="store_true")

    for name, help_text in (
        ("install", "Render and install a skill from a confirmed profile."),
        ("doctor", "Validate a profile and installed generated files."),
        ("uninstall", "Remove only files owned by this generator."),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--profile", type=Path, required=True)
        command.add_argument(
            "--provider",
            choices=[item.value for item in ProviderChoice],
            help="Override provider choice stored in the profile.",
        )
        command.add_argument(
            "--scope",
            choices=[item.value for item in Scope],
            default=Scope.PROJECT.value,
        )
        command.add_argument("--json", action="store_true")
        if name in {"install", "uninstall"}:
            command.add_argument("--dry-run", action="store_true")
        if name == "install":
            command.add_argument(
                "--interactive",
                action="store_true",
                help="Prompt when the profile provider choice is 'ask'.",
            )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "detect":
            return _detect(args)
        if args.command == "setup":
            return _setup(args)
        profile = Profile.load(args.profile)
        provider = args.provider
        scope = Scope(args.scope)
        if args.command == "install":
            results = install(
                profile,
                provider_choice=provider,
                scope=scope,
                interactive=args.interactive,
                dry_run=args.dry_run,
            )
            return _print_results(results, args.json)
        if args.command == "doctor":
            report = doctor(profile, provider_choice=provider, scope=scope)
            print(
                json.dumps(report.to_dict(), indent=2)
                if args.json
                else report.format_text()
            )
            return 0 if report.ok else 1
        if args.command == "uninstall":
            results = uninstall(
                profile,
                provider_choice=provider,
                scope=scope,
                dry_run=args.dry_run,
            )
            code = _print_results(results, args.json)
            unsafe = {"refused-unowned", "refused-modified"}
            return 1 if any(item.status in unsafe for item in results) else code
        parser.error(f"Unknown command: {args.command}")
    except (ProfileError, InstallError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def _detect(args: argparse.Namespace) -> int:
    profile = detect_profile(
        args.repository,
        provider_choice=args.provider,
        confirmed=args.confirm,
    )
    report = DetectionReport(profile)
    if args.interactive:
        print(report.format_text())
        answer = input("Confirm this profile? [y/N]: ").strip().lower()
        profile.confirmed = answer in {"y", "yes"}
    elif not args.json:
        print(report.format_text())
    if args.output:
        profile.save(args.output)
        if not args.json:
            print(f"\nProfile written to {args.output}")
    if args.json:
        print(profile.to_json(), end="")
    return 0


def _setup(args: argparse.Namespace) -> int:
    profile = detect_profile(
        args.repository,
        provider_choice=args.provider,
        confirmed=False,
    )
    report = DetectionReport(profile)
    print(report.format_text())
    answer = input(
        "\nConfirm this detected stack and continue with skill generation? [y/N]: "
    ).strip().lower()
    if answer not in {"y", "yes"}:
        print("Setup cancelled; no skill files were changed.", file=sys.stderr)
        return 1

    profile.confirmed = True
    profile_path = args.profile or profile.repository_root / ".pr-review-skill.json"
    profile.save(profile_path)
    results = install(
        profile,
        scope=Scope(args.scope),
        interactive=True,
        dry_run=args.dry_run,
    )
    if not args.json:
        print(f"\nConfirmed profile written to {profile_path}")
    return _print_results(results, args.json)


def _print_results(results: object, as_json: bool) -> int:
    items = tuple(results)  # type: ignore[arg-type]
    if as_json:
        print(json.dumps([item.to_dict() for item in items], indent=2))
    else:
        for item in items:
            print(f"{item.provider.value}: {item.status} — {item.destination}")
            if item.backup:
                print(f"  backup: {item.backup}")
            if item.diff:
                print(item.diff)
    return 0
