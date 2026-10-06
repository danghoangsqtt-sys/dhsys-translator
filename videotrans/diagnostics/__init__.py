"""Side-effect-free diagnostics helpers for pyVideoTrans."""

from .system_readiness import (
    ProbeSnapshot,
    ReadinessPaths,
    ReadinessReport,
    collect_system_readiness,
    evaluate_readiness,
    probe_system,
)
from .remediation import (
    REMEDIATION_REGISTRY,
    RemediationAction,
    RemediationResult,
    action_public_details,
    execute_remediation,
    get_remediation,
)

__all__ = [
    "ProbeSnapshot",
    "ReadinessPaths",
    "ReadinessReport",
    "collect_system_readiness",
    "evaluate_readiness",
    "probe_system",
    "REMEDIATION_REGISTRY",
    "RemediationAction",
    "RemediationResult",
    "action_public_details",
    "execute_remediation",
    "get_remediation",
]
