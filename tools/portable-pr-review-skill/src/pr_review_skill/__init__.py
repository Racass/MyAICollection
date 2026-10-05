"""Portable PR review skill generator."""

from .detection import detect_profile
from .installer import doctor, install, uninstall
from .models import (
    Capability,
    CapabilityState,
    DetectionEvidence,
    Profile,
    Provider,
    ProviderChoice,
    Scope,
)

__all__ = [
    "Capability",
    "CapabilityState",
    "DetectionEvidence",
    "Profile",
    "Provider",
    "ProviderChoice",
    "Scope",
    "detect_profile",
    "doctor",
    "install",
    "uninstall",
]

__version__ = "0.1.0"
