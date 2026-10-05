from pathlib import Path

import pytest

from pr_review_skill.models import (
    Capability,
    CapabilityState,
    DetectionEvidence,
    Profile,
    ProfileError,
    ProviderChoice,
)


def test_profile_round_trip(tmp_path: Path) -> None:
    profile = Profile(
        repository_root=tmp_path,
        capabilities={
            "provider.copilot": Capability(
                "provider.copilot",
                CapabilityState.AVAILABLE,
                (DetectionEvidence("cli", "copilot is available"),),
            )
        },
        provider_choice=ProviderChoice.COPILOT,
        confirmed=True,
        adapter_ids=("github", "local-git"),
    )

    restored = Profile.from_dict(profile.to_dict())

    assert restored.to_dict() == profile.to_dict()
    assert restored.available("provider.copilot")
    assert restored.capability("missing").state is CapabilityState.UNVERIFIED


def test_profile_rejects_mismatched_capability_key(tmp_path: Path) -> None:
    with pytest.raises(ProfileError, match="does not match"):
        Profile(
            repository_root=tmp_path,
            capabilities={
                "provider.copilot": Capability(
                    "provider.claude", CapabilityState.AVAILABLE
                )
            },
        )
