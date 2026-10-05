from pathlib import Path

import pytest

from pr_review_skill.installer import InstallError, doctor, install, uninstall
from pr_review_skill.models import Profile, ProviderChoice, Scope


def _profile(tmp_path: Path, *, confirmed: bool = True) -> Profile:
    return Profile(
        repository_root=tmp_path,
        capabilities={},
        provider_choice=ProviderChoice.BOTH,
        confirmed=confirmed,
        adapter_ids=("local-git",),
    )


def test_install_requires_confirmed_profile(tmp_path: Path) -> None:
    with pytest.raises(InstallError, match="not confirmed"):
        install(_profile(tmp_path, confirmed=False))


def test_install_rejects_unknown_adapter(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    profile.adapter_ids = ("unknown-system",)

    with pytest.raises(InstallError, match="Unknown adapter"):
        install(profile, provider_choice=ProviderChoice.COPILOT)


def test_install_both_is_idempotent_and_doctor_verifies_hashes(
    tmp_path: Path,
) -> None:
    profile = _profile(tmp_path)

    installed = install(profile, scope=Scope.PROJECT)
    repeated = install(profile, scope=Scope.PROJECT)
    report = doctor(profile, scope=Scope.PROJECT)

    assert {item.status for item in installed} == {"installed"}
    assert {item.status for item in repeated} == {"unchanged"}
    assert (tmp_path / ".github" / "skills" / "pr-review" / "SKILL.md").is_file()
    assert (tmp_path / ".claude" / "skills" / "pr-review" / "SKILL.md").is_file()
    assert report.ok


def test_uninstall_refuses_modified_owned_file(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    install(profile, provider_choice=ProviderChoice.COPILOT)
    skill = tmp_path / ".github" / "skills" / "pr-review" / "SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nmanual edit\n", encoding="utf-8")

    result = uninstall(profile, provider_choice=ProviderChoice.COPILOT)

    assert result[0].status == "refused-modified"
    assert skill.exists()


def test_uninstall_removes_only_generated_skill(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    install(profile, provider_choice=ProviderChoice.COPILOT)
    unrelated = tmp_path / ".github" / "skills" / "other" / "SKILL.md"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("other", encoding="utf-8")

    result = uninstall(profile, provider_choice=ProviderChoice.COPILOT)

    assert result[0].status == "removed"
    assert unrelated.read_text(encoding="utf-8") == "other"


def test_multi_provider_preflight_avoids_partial_install(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    unowned = tmp_path / ".claude" / "skills" / "pr-review"
    unowned.mkdir(parents=True)
    (unowned / "manual.txt").write_text("manual", encoding="utf-8")

    with pytest.raises(InstallError, match="unowned"):
        install(profile)

    assert not (tmp_path / ".github" / "skills" / "pr-review").exists()
