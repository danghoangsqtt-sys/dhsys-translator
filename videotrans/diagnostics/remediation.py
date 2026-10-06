"""Consent-gated remediation primitives for Windows readiness findings.

Only actions declared in :data:`REMEDIATION_REGISTRY` can create an external
effect.  Callers cannot append command-line arguments, replace package IDs or
substitute URLs.  The module intentionally keeps UI confirmation outside the
executor while still requiring an explicit ``confirmed=True`` token before any
effect can occur.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import webbrowser
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Callable, Mapping, Sequence
from urllib.parse import urlsplit


KIND_GUIDANCE = "guidance"
KIND_OPEN_URL = "open_url"
KIND_WINGET = "winget"

STATUS_CANCELLED = "cancelled"
STATUS_NOT_ALLOWED = "not_allowed"
STATUS_GUIDANCE = "guidance"
STATUS_LINK_OPENED = "link_opened"
STATUS_MISSING_WINGET = "missing_winget"
STATUS_UNAVAILABLE = "unavailable"
STATUS_UAC_DENIED = "uac_denied"
STATUS_REBOOT_REQUIRED = "reboot_required"
STATUS_INSTALLER_FAILED = "installer_failed"
STATUS_POST_CHECK_FAILED = "post_check_failed"
STATUS_SUCCESS = "success"

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemediationAction:
    code: str
    kind: str
    title: str
    description: str
    publisher: str
    source: str
    official_url: str | None = None
    package_id: str | None = None
    requires_elevation: bool = False
    restart_possible: bool = False
    post_check_code: str | None = None


@dataclass(frozen=True)
class RemediationResult:
    action_code: str
    status: str
    method: str
    message: str
    returncode: int | None = None

    def to_log_dict(self) -> dict[str, object]:
        """Return a deliberately small, path/secret-free audit payload."""

        return {
            "action_code": self.action_code,
            "status": self.status,
            "method": self.method,
            "returncode": self.returncode,
        }


def _guidance(
    code: str,
    title: str,
    description: str,
    *,
    publisher: str = "pyVideoTrans",
    source: str = "Built-in guidance",
) -> RemediationAction:
    return RemediationAction(
        code=code,
        kind=KIND_GUIDANCE,
        title=title,
        description=description,
        publisher=publisher,
        source=source,
    )


def _nvidia_link(code: str) -> RemediationAction:
    return RemediationAction(
        code=code,
        kind=KIND_OPEN_URL,
        title="Open official NVIDIA driver page",
        description=(
            "GPU drivers, CUDA and cuDNN are never installed automatically. "
            "Open NVIDIA's official driver page, choose the matching hardware, then run System check again."
        ),
        publisher="NVIDIA",
        source="Official NVIDIA website",
        official_url="https://www.nvidia.com/Download/index.aspx",
        requires_elevation=False,
        restart_possible=True,
    )


_REGISTRY = {
    "repair_bundle_ffmpeg": _guidance(
        "repair_bundle_ffmpeg",
        "Repair or reinstall pyVideoTrans",
        "FFmpeg is bundled with pyVideoTrans. Repair/reinstall the application package instead of installing a global FFmpeg copy.",
    ),
    "repair_bundle_ffprobe": _guidance(
        "repair_bundle_ffprobe",
        "Repair or reinstall pyVideoTrans",
        "ffprobe is bundled with pyVideoTrans. Repair/reinstall the application package instead of installing a global ffprobe copy.",
    ),
    "repair_bundle_resources": _guidance(
        "repair_bundle_resources",
        "Repair or reinstall pyVideoTrans",
        "Application resources are part of the packaged build. Repair/reinstall the same trusted package.",
    ),
    "fix_user_data_permissions": _guidance(
        "fix_user_data_permissions",
        "Check the user-data folder permissions",
        "Keep the app non-elevated. Check that your Windows account can write to the pyVideoTrans user-data folder, then scan again.",
    ),
    "fix_cache_permissions": _guidance(
        "fix_cache_permissions",
        "Check the cache folder permissions",
        "Keep the app non-elevated. Check that your Windows account can write to the pyVideoTrans cache folder, then scan again.",
    ),
    "close_apps_or_use_lighter_workload": _guidance(
        "close_apps_or_use_lighter_workload",
        "Reduce memory pressure",
        "Close other memory-heavy applications or choose a lighter local model before processing.",
    ),
    "free_disk_space": _guidance(
        "free_disk_space",
        "Free disk space",
        "Free enough local disk space for source media, temporary files and output, then run System check again.",
    ),
    "expect_slower_processing": _guidance(
        "expect_slower_processing",
        "Use a lighter workload",
        "This CPU can still work, but local processing may be slower. Prefer smaller models or cloud providers when appropriate.",
    ),
    "use_cpu_or_install_nvidia_driver": _nvidia_link("use_cpu_or_install_nvidia_driver"),
    "install_or_update_nvidia_driver": _nvidia_link("install_or_update_nvidia_driver"),
    "retry_gpu_detection": _nvidia_link("retry_gpu_detection"),
    # Reserved for a future readiness probe. Keeping the exact package identity
    # here makes the WinGet execution path testable without accepting arbitrary
    # package names from the UI or diagnostic payload.
    "install_vc_runtime": RemediationAction(
        code="install_vc_runtime",
        kind=KIND_WINGET,
        title="Install Microsoft Visual C++ Runtime",
        description=(
            "Install the Microsoft Visual C++ 2015-2022 x64 redistributable using the exact WinGet package ID. "
            "If WinGet is unavailable, open Microsoft's official installer URL instead."
        ),
        publisher="Microsoft",
        source="WinGet community source / Microsoft official fallback",
        official_url="https://aka.ms/vs/17/release/vc_redist.x64.exe",
        package_id="Microsoft.VCRedist.2015+.x64",
        requires_elevation=True,
        restart_possible=True,
        post_check_code="runtime.vc_redist",
    ),
}

REMEDIATION_REGISTRY: Mapping[str, RemediationAction] = MappingProxyType(_REGISTRY)

CommandRunner = Callable[[Sequence[str], float], subprocess.CompletedProcess[str]]
UrlOpener = Callable[[str], bool]
PostChecker = Callable[[str], bool]
ExecutableFinder = Callable[[str], str | None]


def get_remediation(action_code: str) -> RemediationAction | None:
    """Return an immutable allowlisted action, never a user-constructed action."""

    return REMEDIATION_REGISTRY.get(action_code)


def _default_command_runner(argv: Sequence[str], timeout: float) -> subprocess.CompletedProcess[str]:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    return subprocess.run(
        list(argv),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        creationflags=creationflags,
    )


def _default_url_opener(url: str) -> bool:
    return bool(webbrowser.open(url, new=2))


def _is_verified_https_url(url: str) -> bool:
    """Accept only credential-free HTTPS URLs with a concrete hostname."""

    try:
        parsed = urlsplit(url)
    except (TypeError, ValueError):
        return False
    return (
        parsed.scheme.lower() == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
    )


def _default_post_checker(_code: str) -> bool:
    # A WinGet action must provide a real post-condition probe before it can be
    # reported as successful.  Failing closed prevents "exit code 0" from being
    # treated as sufficient evidence.
    return False


def _log_result(result: RemediationResult) -> RemediationResult:
    _LOGGER.info(
        "system_remediation=%s",
        json.dumps(result.to_log_dict(), sort_keys=True, ensure_ascii=True),
    )
    return result


def _open_official_fallback(
    action: RemediationAction,
    *,
    url_opener: UrlOpener,
    missing_winget: bool,
) -> RemediationResult:
    if not action.official_url:
        status = STATUS_MISSING_WINGET if missing_winget else STATUS_UNAVAILABLE
        return _log_result(RemediationResult(
            action.code,
            status,
            "none",
            "No verified manual recovery link is available for this action.",
        ))
    if not _is_verified_https_url(action.official_url):
        return _log_result(RemediationResult(
            action.code,
            STATUS_NOT_ALLOWED,
            "none",
            "The allowlisted remediation URL is not a verified HTTPS address, so it will not be opened.",
        ))
    try:
        opened = bool(url_opener(action.official_url))
    except (OSError, RuntimeError, ValueError):
        opened = False
    if opened:
        return _log_result(RemediationResult(
            action.code,
            STATUS_LINK_OPENED,
            "official_url",
            "Opened the verified official recovery page. Complete the action there, then run System check again.",
        ))
    return _log_result(RemediationResult(
        action.code,
        STATUS_UNAVAILABLE,
        "official_url",
        "Could not open the verified official page. Check the network connection or copy the official URL from the confirmation details.",
    ))


def execute_remediation(
    action_code: str,
    *,
    confirmed: bool,
    command_runner: CommandRunner = _default_command_runner,
    url_opener: UrlOpener = _default_url_opener,
    post_checker: PostChecker = _default_post_checker,
    executable_finder: ExecutableFinder = shutil.which,
    timeout: float = 900.0,
) -> RemediationResult:
    """Execute one exact allowlisted action after explicit caller confirmation.

    The function accepts no free-form command, URL, package ID, file path or
    argument list.  This keeps hostile labels and diagnostic text out of the
    process boundary.
    """

    action = get_remediation(action_code)
    if action is None:
        return _log_result(RemediationResult(
            action_code,
            STATUS_NOT_ALLOWED,
            "none",
            "This remediation is not in the verified allowlist.",
        ))
    if not confirmed:
        return _log_result(RemediationResult(
            action.code,
            STATUS_CANCELLED,
            "none",
            "Cancelled. No system change was made.",
        ))

    if action.kind == KIND_GUIDANCE:
        return _log_result(RemediationResult(
            action.code,
            STATUS_GUIDANCE,
            "guidance",
            action.description,
        ))

    if action.kind == KIND_OPEN_URL:
        return _open_official_fallback(action, url_opener=url_opener, missing_winget=False)

    if action.kind != KIND_WINGET or not action.package_id:
        return _log_result(RemediationResult(
            action.code,
            STATUS_NOT_ALLOWED,
            "none",
            "The allowlisted remediation definition is incomplete.",
        ))

    winget = executable_finder("winget")
    if not winget:
        return _open_official_fallback(action, url_opener=url_opener, missing_winget=True)

    argv = [
        winget,
        "install",
        "--id",
        action.package_id,
        "--exact",
        "--source",
        "winget",
        "--disable-interactivity",
    ]
    try:
        completed = command_runner(argv, timeout)
    except FileNotFoundError:
        return _open_official_fallback(action, url_opener=url_opener, missing_winget=True)
    except subprocess.TimeoutExpired:
        return _log_result(RemediationResult(
            action.code,
            STATUS_UNAVAILABLE,
            KIND_WINGET,
            "The installer timed out. Check connectivity and retry, or use the verified official manual installer.",
        ))
    except OSError:
        return _log_result(RemediationResult(
            action.code,
            STATUS_UNAVAILABLE,
            KIND_WINGET,
            "Windows could not start WinGet. Retry or use the verified official manual installer.",
        ))

    returncode = int(completed.returncode)
    windows_code = returncode & 0xFFFFFFFF
    if windows_code == 1223:
        return _log_result(RemediationResult(
            action.code,
            STATUS_UAC_DENIED,
            KIND_WINGET,
            "Windows elevation was cancelled or denied. Nothing else will be installed automatically.",
            returncode,
        ))
    if windows_code in (1641, 3010):
        return _log_result(RemediationResult(
            action.code,
            STATUS_REBOOT_REQUIRED,
            KIND_WINGET,
            "The installer reports that Windows must restart before the prerequisite can be verified.",
            returncode,
        ))
    if returncode != 0:
        return _log_result(RemediationResult(
            action.code,
            STATUS_INSTALLER_FAILED,
            KIND_WINGET,
            "The installer failed. No other package will be attempted automatically; use the verified manual recovery path if needed.",
            returncode,
        ))

    if not action.post_check_code:
        return _log_result(RemediationResult(
            action.code,
            STATUS_POST_CHECK_FAILED,
            KIND_WINGET,
            "Install command finished, but this action has no verified post-condition probe.",
            returncode,
        ))
    try:
        verified = bool(post_checker(action.post_check_code))
    except (OSError, RuntimeError, ValueError):
        verified = False
    if not verified:
        return _log_result(RemediationResult(
            action.code,
            STATUS_POST_CHECK_FAILED,
            KIND_WINGET,
            "Install command finished, but the prerequisite is still not verified. Restart if requested, then run System check again.",
            returncode,
        ))
    return _log_result(RemediationResult(
        action.code,
        STATUS_SUCCESS,
        KIND_WINGET,
        "The allowlisted prerequisite was installed and its post-condition was verified.",
        returncode,
    ))


def action_public_details(action_code: str) -> dict[str, object] | None:
    """Expose only fixed allowlist metadata suitable for a confirmation dialog."""

    action = get_remediation(action_code)
    if action is None:
        return None
    details = asdict(action)
    # The package ID and official URL are intentionally visible so the user can
    # verify exactly what will run/open before granting consent.
    return details
