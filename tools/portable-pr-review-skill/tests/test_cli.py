from pathlib import Path

from pr_review_skill.cli import main
from pr_review_skill.models import Profile


def test_setup_confirms_profile_before_dry_run_install(
    tmp_path: Path,
    monkeypatch,
) -> None:
    profile_path = tmp_path / "confirmed-profile.json"
    monkeypatch.setattr("builtins.input", lambda _: "y")

    result = main(
        [
            "setup",
            "--repository",
            str(tmp_path),
            "--profile",
            str(profile_path),
            "--provider",
            "copilot",
            "--dry-run",
        ]
    )

    assert result == 0
    assert Profile.load(profile_path).confirmed
    assert not (tmp_path / ".github" / "skills" / "pr-review").exists()
