import json
import subprocess
from pathlib import Path

from videotrans.diagnostics.system_readiness import (
    GIB,
    NvidiaProbe,
    ProbeSnapshot,
    ReadinessPaths,
    STATUS_OK,
    STATUS_UNKNOWN,
    STATUS_WARNING,
    WORKLOAD_BASIC,
    WORKLOAD_CUDA,
    WORKLOAD_LOCAL_MODELS,
    evaluate_readiness,
    probe_system,
)


def _snapshot(**overrides):
    values = {
        "os_name": "Windows",
        "os_release": "11",
        "architecture": "AMD64",
        "cpu_logical_count": 12,
        "ram_bytes": 16 * GIB,
        "disk_free_bytes": 64 * GIB,
        "ffmpeg_present": True,
        "ffprobe_present": True,
        "resources_present": True,
        "user_data_writable": True,
        "cache_writable": True,
        "nvidia": NvidiaProbe(
            state=STATUS_OK,
            gpu_count=1,
            total_vram_mib=8192,
            cuda_driver_version="12.8",
        ),
    }
    values.update(overrides)
    return ProbeSnapshot(**values)


def _finding(report, code):
    return next(item for item in report.findings if item.code == code)


def test_capable_machine_is_ready_for_all_workloads():
    report = evaluate_readiness(_snapshot())

    assert report.workloads[WORKLOAD_BASIC].rating == "ready"
    assert report.workloads[WORKLOAD_LOCAL_MODELS].rating == "ready"
    assert report.workloads[WORKLOAD_CUDA].rating == "ready"


def test_cpu_only_machine_keeps_basic_workflow_ready():
    report = evaluate_readiness(
        _snapshot(nvidia=NvidiaProbe(state=STATUS_WARNING, gpu_count=0, total_vram_mib=0))
    )

    assert report.workloads[WORKLOAD_BASIC].rating == "ready"
    assert report.workloads[WORKLOAD_LOCAL_MODELS].rating == "degraded"
    assert report.workloads[WORKLOAD_CUDA].rating == "blocked"
    assert _finding(report, "gpu.nvidia").requirements[WORKLOAD_BASIC] == "optional"


def test_low_ram_and_disk_are_factual_blockers():
    report = evaluate_readiness(_snapshot(ram_bytes=3 * GIB, disk_free_bytes=2 * GIB))

    assert report.workloads[WORKLOAD_BASIC].rating == "blocked"
    assert "memory.ram_gib" in report.workloads[WORKLOAD_BASIC].blocking_codes
    assert "storage.free_gib" in report.workloads[WORKLOAD_BASIC].blocking_codes


def test_minimum_capacity_below_recommendation_is_degraded_not_blocked():
    report = evaluate_readiness(_snapshot(ram_bytes=6 * GIB, disk_free_bytes=8 * GIB))

    basic = report.workloads[WORKLOAD_BASIC]
    assert basic.rating == "degraded"
    assert set(basic.advisory_codes) >= {"memory.ram_gib", "storage.free_gib"}
    assert not basic.blocking_codes


def test_missing_bundled_media_and_resources_block_basic_workflow():
    report = evaluate_readiness(
        _snapshot(ffmpeg_present=False, ffprobe_present=False, resources_present=False)
    )

    rating = report.workloads[WORKLOAD_BASIC]
    assert rating.rating == "blocked"
    assert set(rating.blocking_codes) >= {
        "bundle.ffmpeg",
        "bundle.ffprobe",
        "bundle.resources",
    }


def test_unknown_gpu_does_not_block_basic_but_keeps_cuda_unknown():
    report = evaluate_readiness(_snapshot(nvidia=NvidiaProbe(state=STATUS_UNKNOWN)))

    assert report.workloads[WORKLOAD_BASIC].rating == "ready"
    assert report.workloads[WORKLOAD_LOCAL_MODELS].rating == "degraded"
    assert report.workloads[WORKLOAD_CUDA].rating == "unknown"


def test_unknown_required_hardware_facts_remain_unknown():
    report = evaluate_readiness(
        _snapshot(ram_bytes=None, disk_free_bytes=None, user_data_writable=None)
    )

    assert report.workloads[WORKLOAD_BASIC].rating == "unknown"
    assert set(report.workloads[WORKLOAD_BASIC].unknown_codes) >= {
        "memory.ram_gib",
        "storage.free_gib",
        "storage.user_data_writable",
    }


def test_export_is_sanitized_and_contains_no_internal_paths_or_secrets(tmp_path):
    private_root = tmp_path / "Alice" / "Secret Project" / "holiday-video.mp4"
    report = evaluate_readiness(_snapshot())
    payload = json.dumps(report.to_dict(), ensure_ascii=False)

    assert str(private_root) not in payload
    assert "holiday-video.mp4" not in payload
    assert "api_key" not in payload.lower()
    assert "token" not in payload.lower()
    assert "LOCALAPPDATA" not in payload


def test_probe_detects_bundle_and_leaves_no_writability_probe_files(tmp_path, monkeypatch):
    resources = tmp_path / "bundle"
    ffmpeg_dir = resources / "ffmpeg"
    ffmpeg_dir.mkdir(parents=True)
    (ffmpeg_dir / "ffmpeg.exe").write_bytes(b"ffmpeg")
    (ffmpeg_dir / "ffprobe.exe").write_bytes(b"ffprobe")
    (resources / "videotrans" / "styles").mkdir(parents=True)
    (resources / "videotrans" / "language").mkdir(parents=True)
    user_data = tmp_path / "userdata"
    user_data.mkdir()
    cache = user_data / "tmp"
    cache.mkdir()
    paths = ReadinessPaths(resources, user_data, cache)
    before = set(tmp_path.rglob("*"))
    monkeypatch.setattr("videotrans.diagnostics.system_readiness.sys.platform", "win32")

    def no_gpu(argv, timeout):
        raise FileNotFoundError(argv[0])

    snapshot = probe_system(paths, command_runner=no_gpu)

    assert snapshot.ffmpeg_present is True
    assert snapshot.ffprobe_present is True
    assert snapshot.resources_present is True
    assert snapshot.user_data_writable is True
    assert snapshot.cache_writable is True
    assert snapshot.nvidia.state == STATUS_UNKNOWN
    assert set(tmp_path.rglob("*")) == before


def test_probe_marks_file_blocking_user_data_path_as_not_writable(tmp_path, monkeypatch):
    resources = tmp_path / "bundle"
    ffmpeg_dir = resources / "ffmpeg"
    ffmpeg_dir.mkdir(parents=True)
    (ffmpeg_dir / "ffmpeg.exe").write_bytes(b"x")
    (ffmpeg_dir / "ffprobe.exe").write_bytes(b"x")
    (resources / "videotrans" / "styles").mkdir(parents=True)
    (resources / "videotrans" / "language").mkdir(parents=True)
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_bytes(b"not-a-directory")
    paths = ReadinessPaths(resources, blocked_parent / "data", blocked_parent / "cache")
    monkeypatch.setattr("videotrans.diagnostics.system_readiness.sys.platform", "win32")

    def no_gpu(argv, timeout):
        raise FileNotFoundError(argv[0])

    snapshot = probe_system(paths, command_runner=no_gpu)
    report = evaluate_readiness(snapshot)

    assert snapshot.user_data_writable is False
    assert snapshot.cache_writable is False
    assert report.workloads[WORKLOAD_BASIC].rating == "blocked"
    assert "storage.user_data_writable" in report.workloads[WORKLOAD_BASIC].blocking_codes
    assert "storage.cache_writable" in report.workloads[WORKLOAD_BASIC].blocking_codes


def test_nvidia_smi_timeout_becomes_unknown_and_not_basic_blocker(tmp_path, monkeypatch):
    resources = tmp_path / "bundle"
    (resources / "ffmpeg").mkdir(parents=True)
    (resources / "ffmpeg" / "ffmpeg.exe").write_bytes(b"x")
    (resources / "ffmpeg" / "ffprobe.exe").write_bytes(b"x")
    (resources / "videotrans" / "styles").mkdir(parents=True)
    (resources / "videotrans" / "language").mkdir(parents=True)
    data = tmp_path / "data"
    data.mkdir()
    cache = data / "tmp"
    cache.mkdir()
    monkeypatch.setattr("videotrans.diagnostics.system_readiness.sys.platform", "win32")

    def timeout(argv, seconds):
        raise subprocess.TimeoutExpired(argv, seconds)

    snapshot = probe_system(ReadinessPaths(resources, data, cache), command_runner=timeout)
    report = evaluate_readiness(snapshot)

    assert snapshot.nvidia.state == STATUS_UNKNOWN
    assert "gpu.nvidia" not in report.workloads[WORKLOAD_BASIC].blocking_codes


def test_requirement_levels_are_workload_specific():
    report = evaluate_readiness(_snapshot())
    gpu = _finding(report, "gpu.nvidia")
    ram = _finding(report, "memory.ram_gib")

    assert gpu.requirements == {
        WORKLOAD_BASIC: "optional",
        WORKLOAD_LOCAL_MODELS: "recommended",
        WORKLOAD_CUDA: "required",
    }
    assert ram.requirements[WORKLOAD_BASIC] == "required"
    assert ram.requirements[WORKLOAD_CUDA] == "recommended"
