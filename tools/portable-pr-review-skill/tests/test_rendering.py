from pathlib import Path

from pr_review_skill.models import Profile, ProviderChoice
from pr_review_skill.rendering import render_skill


def _profile(tmp_path: Path) -> Profile:
    return Profile(
        repository_root=tmp_path,
        capabilities={},
        provider_choice=ProviderChoice.BOTH,
        confirmed=True,
        adapter_ids=("github", "jira", "slack", "local-git"),
    )


def test_renders_portable_and_provider_specific_frontmatter(tmp_path: Path) -> None:
    profile = _profile(tmp_path)

    copilot = render_skill(profile, "copilot")
    claude = render_skill(profile, "claude")

    assert "argument-hint:" not in copilot["SKILL.md"]
    assert "user-invocable:" not in copilot["SKILL.md"]
    assert "license: MIT" in copilot["SKILL.md"]
    assert "argument-hint:" in claude["SKILL.md"]
    assert "user-invocable: true" in claude["SKILL.md"]
    assert "license: MIT" in claude["SKILL.md"]
    assert copilot.source_hash != claude.source_hash


def test_generated_skill_is_progressive_safe_and_unbranded(tmp_path: Path) -> None:
    package = render_skill(_profile(tmp_path), "copilot")
    combined = "\n".join(package.values()).lower()

    assert len(package["SKILL.md"].splitlines()) < 500
    assert "preview is the default" in combined
    assert "explicit confirmation" in combined
    assert "iteration is disabled by default" in combined
    assert "rafa" + "elfel" not in combined
    assert "micro" + "soft" not in combined
    assert "poke" + "mon" not in combined
    assert "pok" + "émon" not in combined
    assert "github" in package["references/stack.md"].lower()
    assert "jira" in package["references/stack.md"].lower()
    assert "slack" in package["references/stack.md"].lower()
    assert "outlook" not in package["references/stack.md"].lower()


def test_render_is_deterministic(tmp_path: Path) -> None:
    profile = _profile(tmp_path)

    first = render_skill(profile, "copilot")
    second = render_skill(profile, "copilot")

    assert first.files == second.files
    assert first.source_hash == second.source_hash
