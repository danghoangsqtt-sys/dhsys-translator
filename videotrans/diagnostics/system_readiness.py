"""Read-only machine readiness probes for the local Windows distribution.

The module deliberately does not import ``videotrans.configure`` because that
package initializes writable application directories at import time. Probe
results are reduced to non-sensitive facts before they become exportable.
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence

import psutil


GIB = 1024**3
MIB = 1024**2

WORKLOAD_BASIC = "basic"
WORKLOAD_LOCAL_MODELS = "local_models"
WORKLOAD_CUDA = "cuda_acceleration"
WORKLOADS = (WORKLOAD_BASIC, WORKLOAD_LOCAL_MODELS, WORKLOAD_CUDA)

REQUIRED = "required"
RECOMMENDED = "recommended"
OPTIONAL = "optional"
UNKNOWN = "unknown"

STATUS_OK = "ok"
STATUS_WARNING = "warning"
STATUS_BLOCKED = "blocked"
STATUS_UNKNOWN = "unknown"

RATING_READY = "ready"
RATING_DEGRADED = "degraded"
RATING_BLOCKED = "blocked"
RATING_UNKNOWN = "unknown"


@dataclass(frozen=True)
class ReadinessPaths:
    """Internal paths used for probes; these values are never exported."""

    resource_root: Path
    user_data_root: Path
    cache_root: Path


@dataclass(frozen=True)
class NvidiaProbe:
    state: str = STATUS_UNKNOWN
    gpu_count: int | None = None
    total_vram_mib: int | None = None
    cuda_driver_version: str | None = None


@dataclass(frozen=True)
class ProbeSnapshot:
    os_name: str = "unknown"
    os_release: str = "unknown"
    architecture: str = "unknown"
    cpu_logical_count: int | None = None
    ram_bytes: int | None = None
    disk_free_bytes: int | None = None
    ffmpeg_present: bool | None = None
    ffprobe_present: bool | None = None
    resources_present: bool | None = None
    user_data_writable: bool | None = None
    cache_writable: bool | None = None
    nvidia: NvidiaProbe = field(default_factory=NvidiaProbe)


@dataclass(frozen=True)
class Finding:
    code: str
    status: str
    action_code: str
    summary: str
    value: object | None
    requirements: Mapping[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "status": self.status,
            "action_code": self.action_code,
            "summary": self.summary,
            "value": self.value,
            "requirements": dict(self.requirements),
        }


@dataclass(frozen=True)
class WorkloadRating:
    workload: str
    rating: str
    blocking_codes: tuple[str, ...] = ()
    advisory_codes: tuple[str, ...] = ()
    unknown_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReadinessReport:
    system: Mapping[str, object]
    findings: tuple[Finding, ...]
    workloads: Mapping[str, WorkloadRating]

    def to_dict(self) -> dict[str, object]:
        """Return the sanitized diagnostic payload safe for export."""

        return {
            "schema_version": 1,
            "system": dict(self.system),
            "findings": [finding.to_dict() for finding in self.findings],
            "workloads": {
                name: rating.to_dict() for name, rating in self.workloads.items()
            },
        }


CommandRunner = Callable[[Sequence[str], float], subprocess.CompletedProcess[str]]


def _default_paths() -> ReadinessPaths:
    source_root = Path(__file__).resolve().parents[2]
    if bool(getattr(sys, "frozen", False)):
        resource_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent / "_internal"))
    else:
        resource_root = source_root

    if sys.platform == "win32":
        local_base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        user_data_root = local_base / "pyVideoTrans"
    elif sys.platform == "darwin":
        user_data_root = Path.home() / "Library" / "Application Support" / "pyVideoTrans"
    else:
        data_base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        user_data_root = data_base / "pyVideoTrans"
    return ReadinessPaths(
        resource_root=resource_root,
        user_data_root=user_data_root,
        cache_root=user_data_root / "tmp",
    )


def _safe_call(callable_: Callable[[], object]) -> object | None:
    try:
        return callable_()
    except (OSError, RuntimeError, ValueError):
        return None


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


def _probe_writable_target(path: Path) -> bool | None:
    """Verify write access with a transient file and leave no persistent artifact."""

    probe_dir = path
    while not probe_dir.exists() and probe_dir != probe_dir.parent:
        probe_dir = probe_dir.parent
    if not probe_dir.is_dir():
        # An existing file in the requested directory chain is a deterministic
        # blocker: the application cannot create the directory beneath it.
        return False
    try:
        with tempfile.NamedTemporaryFile(prefix=".pyvideotrans-readiness-", dir=probe_dir):
            pass
    except OSError:
        return False
    return True


def _probe_nvidia(command_runner: CommandRunner, timeout: float = 2.0) -> NvidiaProbe:
    query = [
        "nvidia-smi",
        "--query-gpu=name,memory.total",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = command_runner(query, timeout)
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return NvidiaProbe()
    if result.returncode != 0:
        return NvidiaProbe(state=STATUS_WARNING, gpu_count=0, total_vram_mib=0)

    rows = [row.strip() for row in result.stdout.splitlines() if row.strip()]
    if not rows:
        return NvidiaProbe(state=STATUS_WARNING, gpu_count=0, total_vram_mib=0)

    vram_values: list[int] = []
    for row in rows:
        parts = [part.strip() for part in row.rsplit(",", 1)]
        if len(parts) != 2:
            continue
        try:
            vram_values.append(int(float(parts[1])))
        except ValueError:
            continue

    cuda_version = None
    try:
        summary = command_runner(["nvidia-smi"], timeout)
        if summary.returncode == 0:
            match = re.search(r"CUDA Version:\s*([0-9.]+)", summary.stdout)
            if match:
                cuda_version = match.group(1)
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        pass

    return NvidiaProbe(
        state=STATUS_OK,
        gpu_count=len(rows),
        total_vram_mib=sum(vram_values) if vram_values else None,
        cuda_driver_version=cuda_version,
    )


def probe_system(
    paths: ReadinessPaths | None = None,
    *,
    command_runner: CommandRunner = _default_command_runner,
) -> ProbeSnapshot:
    """Capture a bounded, non-secret machine snapshot for readiness evaluation."""

    paths = paths or _default_paths()
    ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    ffprobe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    ffmpeg_dir = paths.resource_root / "ffmpeg"

    memory = _safe_call(lambda: psutil.virtual_memory().total)
    disk = _safe_call(lambda: psutil.disk_usage(str(paths.user_data_root.anchor or paths.user_data_root)).free)

    resource_markers = (
        paths.resource_root / "videotrans" / "styles",
        paths.resource_root / "videotrans" / "language",
    )
    return ProbeSnapshot(
        os_name=platform.system() or "unknown",
        os_release=platform.release() or "unknown",
        architecture=platform.machine() or "unknown",
        cpu_logical_count=_safe_call(lambda: psutil.cpu_count(logical=True)),
        ram_bytes=memory if isinstance(memory, int) else None,
        disk_free_bytes=disk if isinstance(disk, int) else None,
        ffmpeg_present=(ffmpeg_dir / ffmpeg_name).is_file(),
        ffprobe_present=(ffmpeg_dir / ffprobe_name).is_file(),
        resources_present=all(marker.exists() for marker in resource_markers),
        user_data_writable=_probe_writable_target(paths.user_data_root),
        cache_writable=_probe_writable_target(paths.cache_root),
        nvidia=_probe_nvidia(command_runner),
    )


def _requirements(*, basic: str, local: str, cuda: str) -> dict[str, str]:
    return {
        WORKLOAD_BASIC: basic,
        WORKLOAD_LOCAL_MODELS: local,
        WORKLOAD_CUDA: cuda,
    }


def _boolean_finding(
    *,
    code: str,
    value: bool | None,
    action_code: str,
    summary_ok: str,
    summary_fail: str,
    requirements: Mapping[str, str],
) -> Finding:
    if value is True:
        return Finding(code, STATUS_OK, "none", summary_ok, True, requirements)
    if value is False:
        required_somewhere = REQUIRED in requirements.values()
        status = STATUS_BLOCKED if required_somewhere else STATUS_WARNING
        return Finding(code, status, action_code, summary_fail, False, requirements)
    return Finding(code, STATUS_UNKNOWN, action_code, "Không xác định", None, requirements)


def _capacity_finding(
    *,
    code: str,
    value: int | None,
    unit: int,
    minimum: int,
    recommended: int,
    action_code: str,
    requirements: Mapping[str, str],
) -> Finding:
    normalized = None if value is None else round(value / unit, 1)
    if value is None:
        return Finding(code, STATUS_UNKNOWN, action_code, "Không xác định", None, requirements)
    if value < minimum * unit:
        return Finding(code, STATUS_BLOCKED, action_code, "Dưới mức tối thiểu", normalized, requirements)
    if value < recommended * unit:
        return Finding(code, STATUS_WARNING, action_code, "Đạt tối thiểu, dưới mức khuyến nghị", normalized, requirements)
    return Finding(code, STATUS_OK, "none", "Đạt mức khuyến nghị", normalized, requirements)


def _rate_workload(workload: str, findings: Sequence[Finding]) -> WorkloadRating:
    blocking: list[str] = []
    advisory: list[str] = []
    unknown: list[str] = []
    for finding in findings:
        requirement = finding.requirements.get(workload, UNKNOWN)
        if finding.status == STATUS_UNKNOWN:
            if requirement == REQUIRED:
                unknown.append(finding.code)
            elif requirement == RECOMMENDED:
                advisory.append(finding.code)
            continue
        if finding.status == STATUS_OK:
            continue
        if finding.status == STATUS_BLOCKED and requirement == REQUIRED:
            blocking.append(finding.code)
        elif requirement in {REQUIRED, RECOMMENDED}:
            advisory.append(finding.code)

    if blocking:
        rating = RATING_BLOCKED
    elif unknown:
        rating = RATING_UNKNOWN
    elif advisory:
        rating = RATING_DEGRADED
    else:
        rating = RATING_READY
    return WorkloadRating(
        workload=workload,
        rating=rating,
        blocking_codes=tuple(blocking),
        advisory_codes=tuple(advisory),
        unknown_codes=tuple(unknown),
    )


def evaluate_readiness(snapshot: ProbeSnapshot) -> ReadinessReport:
    """Convert factual probe data into workload-specific readiness ratings."""

    common_required = _requirements(basic=REQUIRED, local=REQUIRED, cuda=REQUIRED)
    findings: list[Finding] = [
        _boolean_finding(
            code="bundle.ffmpeg",
            value=snapshot.ffmpeg_present,
            action_code="repair_bundle_ffmpeg",
            summary_ok="FFmpeg đi kèm sẵn sàng",
            summary_fail="Thiếu FFmpeg đi kèm",
            requirements=common_required,
        ),
        _boolean_finding(
            code="bundle.ffprobe",
            value=snapshot.ffprobe_present,
            action_code="repair_bundle_ffprobe",
            summary_ok="ffprobe đi kèm sẵn sàng",
            summary_fail="Thiếu ffprobe đi kèm",
            requirements=common_required,
        ),
        _boolean_finding(
            code="bundle.resources",
            value=snapshot.resources_present,
            action_code="repair_bundle_resources",
            summary_ok="Tài nguyên ứng dụng sẵn sàng",
            summary_fail="Thiếu tài nguyên ứng dụng",
            requirements=common_required,
        ),
        _boolean_finding(
            code="storage.user_data_writable",
            value=snapshot.user_data_writable,
            action_code="fix_user_data_permissions",
            summary_ok="Thư mục dữ liệu người dùng có thể ghi",
            summary_fail="Không thể ghi dữ liệu người dùng",
            requirements=common_required,
        ),
        _boolean_finding(
            code="storage.cache_writable",
            value=snapshot.cache_writable,
            action_code="fix_cache_permissions",
            summary_ok="Vùng cache có thể ghi",
            summary_fail="Không thể ghi cache",
            requirements=common_required,
        ),
        _capacity_finding(
            code="memory.ram_gib",
            value=snapshot.ram_bytes,
            unit=GIB,
            minimum=4,
            recommended=8,
            action_code="close_apps_or_use_lighter_workload",
            requirements=_requirements(basic=REQUIRED, local=REQUIRED, cuda=RECOMMENDED),
        ),
        _capacity_finding(
            code="storage.free_gib",
            value=snapshot.disk_free_bytes,
            unit=GIB,
            minimum=4,
            recommended=12,
            action_code="free_disk_space",
            requirements=_requirements(basic=REQUIRED, local=REQUIRED, cuda=REQUIRED),
        ),
    ]

    cpu_value = snapshot.cpu_logical_count
    if cpu_value is None:
        cpu_finding = Finding(
            "cpu.logical_count",
            STATUS_UNKNOWN,
            "none",
            "Không xác định",
            None,
            _requirements(basic=RECOMMENDED, local=RECOMMENDED, cuda=OPTIONAL),
        )
    elif cpu_value < 4:
        cpu_finding = Finding(
            "cpu.logical_count",
            STATUS_WARNING,
            "expect_slower_processing",
            "CPU ít hơn 4 luồng; tác vụ có thể chậm",
            cpu_value,
            _requirements(basic=RECOMMENDED, local=RECOMMENDED, cuda=OPTIONAL),
        )
    else:
        cpu_finding = Finding(
            "cpu.logical_count",
            STATUS_OK,
            "none",
            "CPU đạt mức khuyến nghị cơ bản",
            cpu_value,
            _requirements(basic=RECOMMENDED, local=RECOMMENDED, cuda=OPTIONAL),
        )
    findings.append(cpu_finding)

    nvidia = snapshot.nvidia
    gpu_requirements = _requirements(basic=OPTIONAL, local=RECOMMENDED, cuda=REQUIRED)
    if nvidia.state == STATUS_OK and (nvidia.gpu_count or 0) > 0:
        findings.append(Finding(
            "gpu.nvidia",
            STATUS_OK,
            "none",
            "NVIDIA GPU khả dụng",
            {"count": nvidia.gpu_count, "vram_mib": nvidia.total_vram_mib},
            gpu_requirements,
        ))
        cuda_status = STATUS_OK if nvidia.cuda_driver_version else STATUS_UNKNOWN
        findings.append(Finding(
            "gpu.cuda_driver",
            cuda_status,
            "install_or_update_nvidia_driver",
            "CUDA driver hiển thị" if nvidia.cuda_driver_version else "Không xác định CUDA driver",
            nvidia.cuda_driver_version,
            gpu_requirements,
        ))
    elif nvidia.state == STATUS_WARNING:
        findings.append(Finding(
            "gpu.nvidia",
            STATUS_BLOCKED,
            "use_cpu_or_install_nvidia_driver",
            "Không phát hiện NVIDIA GPU khả dụng",
            {"count": nvidia.gpu_count or 0, "vram_mib": nvidia.total_vram_mib or 0},
            gpu_requirements,
        ))
        findings.append(Finding(
            "gpu.cuda_driver",
            STATUS_BLOCKED,
            "use_cpu_or_install_nvidia_driver",
            "CUDA không khả dụng",
            None,
            gpu_requirements,
        ))
    else:
        findings.append(Finding(
            "gpu.nvidia",
            STATUS_UNKNOWN,
            "retry_gpu_detection",
            "Không xác định NVIDIA GPU",
            None,
            gpu_requirements,
        ))
        findings.append(Finding(
            "gpu.cuda_driver",
            STATUS_UNKNOWN,
            "retry_gpu_detection",
            "Không xác định CUDA driver",
            None,
            gpu_requirements,
        ))

    system = {
        "os": snapshot.os_name,
        "os_release": snapshot.os_release,
        "architecture": snapshot.architecture,
    }
    workload_ratings = {
        workload: _rate_workload(workload, findings) for workload in WORKLOADS
    }
    return ReadinessReport(system=system, findings=tuple(findings), workloads=workload_ratings)


def collect_system_readiness(
    paths: ReadinessPaths | None = None,
    *,
    command_runner: CommandRunner = _default_command_runner,
) -> ReadinessReport:
    """Probe the current machine and return a sanitized readiness report."""

    return evaluate_readiness(probe_system(paths, command_runner=command_runner))
