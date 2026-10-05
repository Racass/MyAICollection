import json
from pathlib import Path
import subprocess

from pr_review_skill.detection import detect_profile
from pr_review_skill.models import CapabilityState, ProviderChoice


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def test_detects_repository_stack_provider_and_integrations(tmp_path: Path) -> None:
    _git("init", cwd=tmp_path)
    _git(
        "remote",
        "add",
        "origin",
        "https://user:should-not-leak@github.com/example/project.git",
        cwd=tmp_path,
    )
    (tmp_path / "src" / "App").mkdir(parents=True)
    (tmp_path / "src" / "App" / "App.csproj").write_text(
        "<Project />", encoding="utf-8"
    )
    (tmp_path / ".agents" / "skills").mkdir(parents=True)
    (tmp_path / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "jira": {
                        "command": "jira-mcp",
                        "env": {"TOKEN": "do-not-record"},
                    },
                    "slack": {"command": "slack-mcp"},
                }
            }
        ),
        encoding="utf-8",
    )

    profile = detect_profile(
        tmp_path,
        provider_choice=ProviderChoice.BOTH,
        confirmed=False,
    )

    assert profile.repository["remote"] == "github.com/example/project"
    assert "should-not-leak" not in profile.to_json()
    assert profile.available("stack.dotnet")
    assert profile.available("provider.copilot")
    assert profile.capability("tracker.jira").state is CapabilityState.AMBIGUOUS
    assert profile.capability("chat.slack").state is CapabilityState.AMBIGUOUS
    assert {"github", "jira", "slack", "local-git"} <= set(profile.adapter_ids)
    assert profile.tool_bindings["jira"] == ("jira",)
    assert profile.tool_bindings["slack"] == ("slack",)
    assert "do-not-record" not in profile.to_json()


def test_detection_leaves_external_services_unverified_without_markers(
    tmp_path: Path,
) -> None:
    profile = detect_profile(tmp_path)

    assert profile.capability("tracker.jira").state is CapabilityState.UNVERIFIED
    assert profile.capability("mail.gmail").state is CapabilityState.UNVERIFIED
