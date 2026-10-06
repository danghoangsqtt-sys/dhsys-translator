import json
import zipfile
from pathlib import Path

import pytest

from scripts.distribution_manifest import (
    artifact_names,
    forbidden_path_reason,
    load_manifest,
    make_manifest,
    record_artifact,
    verify_candidate_against_manifest,
    verify_release,
    write_manifest,
    write_sha256_sidecar,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _candidate(root: Path) -> Path:
    candidate = root / "sp"
    (candidate / "_internal" / "videotrans" / "language").mkdir(parents=True)
    (candidate / "sp.exe").write_bytes(b"frozen-entry-point")
    (candidate / "_internal" / "LICENSE").write_text("GPL", encoding="utf-8")
    (candidate / "_internal" / "videotrans" / "language" / "vi_VN.json").write_text(
        '{"hello": "xin chao"}', encoding="utf-8"
    )
    return candidate


def test_artifact_names_are_deterministic_and_do_not_contain_machine_paths():
    names = artifact_names("4.14")
    assert names == {
        "portable": "pyVideoTrans-DH-4.14-win64-portable.zip",
        "setup": "pyVideoTrans-DH-4.14-win64-setup.exe",
        "manifest": "pyVideoTrans-DH-4.14-win64-manifest.json",
    }
    with pytest.raises(ValueError, match="invalid product version"):
        artifact_names("4.14-local-C:\\Alice")


@pytest.mark.parametrize(
    ("path", "reason_fragment"),
    [
        ("logs/session.log", "user/runtime directory"),
        ("models/voice/model.bin", "user/runtime directory"),
        ("output/private-video.mp4", "user/runtime directory"),
        ("_internal/videotrans/params.json", "configuration/credential"),
        ("_internal/videotrans/cfg.json", "configuration/credential"),
    ],
)
def test_forbidden_distribution_paths_are_rejected(path, reason_fragment):
    assert reason_fragment in forbidden_path_reason(path)


def test_library_model_modules_and_public_ca_certificates_are_not_false_positives():
    assert forbidden_path_reason("_internal/transformers/models/bert/modeling_bert.py") is None
    assert forbidden_path_reason("_internal/certifi/cacert.pem") is None


def test_manifest_contains_only_relative_inventory_paths(tmp_path):
    candidate = _candidate(tmp_path)
    manifest_path = tmp_path / artifact_names("4.14")["manifest"]
    payload = make_manifest(version="4.14", candidate=candidate, build_roots=(str(tmp_path),))
    write_manifest(manifest_path, payload)
    serialized = manifest_path.read_text(encoding="utf-8")

    assert str(tmp_path) not in serialized
    assert all(not Path(item["path"]).is_absolute() for item in payload["candidate"]["files"])
    assert load_manifest(manifest_path)["candidate"]["entry_point"] == "sp.exe"


def test_text_file_with_build_machine_absolute_path_is_rejected(tmp_path):
    candidate = _candidate(tmp_path)
    leaked = candidate / "_internal" / "build-info.txt"
    leaked.write_text(f"built from {tmp_path}\\secret", encoding="utf-8")

    with pytest.raises(ValueError, match="build-machine absolute path"):
        make_manifest(version="4.14", candidate=candidate, build_roots=(str(tmp_path),))


def test_candidate_verification_detects_changed_and_missing_files(tmp_path):
    candidate = _candidate(tmp_path)
    payload = make_manifest(version="4.14", candidate=candidate)

    verify_candidate_against_manifest(candidate, payload)
    (candidate / "sp.exe").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="mismatch"):
        verify_candidate_against_manifest(candidate, payload)

    (candidate / "sp.exe").unlink()
    with pytest.raises(ValueError, match="missing files"):
        verify_candidate_against_manifest(candidate, payload)


def test_release_verification_detects_checksum_tampering(tmp_path):
    candidate = _candidate(tmp_path)
    names = artifact_names("4.14")
    release = tmp_path / "release"
    release.mkdir()
    manifest_path = release / names["manifest"]
    write_manifest(manifest_path, make_manifest(version="4.14", candidate=candidate))

    portable = release / names["portable"]
    with zipfile.ZipFile(portable, "w", allowZip64=True) as archive:
        for source in candidate.rglob("*"):
            if source.is_file():
                archive.write(source, f"sp/{source.relative_to(candidate).as_posix()}")
    record_artifact(manifest_path, "portable", portable)
    write_sha256_sidecar(portable)
    write_sha256_sidecar(manifest_path)

    verify_release(manifest_path, release, require_installer=False)
    portable.write_bytes(portable.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="mismatch"):
        verify_release(manifest_path, release, require_installer=False)


def test_release_requires_setup_by_default(tmp_path):
    candidate = _candidate(tmp_path)
    names = artifact_names("4.14")
    release = tmp_path / "release"
    release.mkdir()
    manifest_path = release / names["manifest"]
    write_manifest(manifest_path, make_manifest(version="4.14", candidate=candidate))
    portable = release / names["portable"]
    with zipfile.ZipFile(portable, "w", allowZip64=True) as archive:
        for source in candidate.rglob("*"):
            if source.is_file():
                archive.write(source, f"sp/{source.relative_to(candidate).as_posix()}")
    record_artifact(manifest_path, "portable", portable)
    write_sha256_sidecar(portable)
    write_sha256_sidecar(manifest_path)

    with pytest.raises(FileNotFoundError, match="setup artifact"):
        verify_release(manifest_path, release)


def test_inno_setup_contract_is_per_user_and_preserves_user_data():
    installer = (PROJECT_ROOT / "installer" / "pyvideotrans.iss").read_text(encoding="utf-8")

    assert "PrivilegesRequired=lowest" in installer
    assert r"DefaultDirName={localappdata}\Programs\pyVideoTrans-DH" in installer
    assert 'Name: "startmenuicon"' in installer
    assert 'Name: "desktopicon"' in installer
    assert r'Filename: "{app}\{#MyAppExeName}"' in installer
    assert all(line.strip() != "[UninstallDelete]" for line in installer.splitlines())
    assert r"%LOCALAPPDATA%\pyVideoTrans" in installer


def test_build_script_passes_verifier_parameters_by_name():
    build_script = (PROJECT_ROOT / "scripts" / "build_local_distribution.ps1").read_text(
        encoding="utf-8"
    )

    assert "$VerifyArgs = @{" in build_script
    assert "ManifestPath = $ManifestPath" in build_script
    assert "InnoCompiler = $InnoCompiler" in build_script
    assert "& $VerifyScript @VerifyArgs" in build_script
    assert '$VerifyArgs = @("-ManifestPath"' not in build_script


def test_installed_smoke_contract_covers_recipient_lifecycle():
    smoke = (PROJECT_ROOT / "scripts" / "smoke_installed_distribution.ps1").read_text(
        encoding="utf-8"
    )

    for token in (
        'ValidateSet("DeveloperHost", "WindowsSandbox", "DisposableVM", "CleanUser")',
        "no_existing_registration = $true",
        'if ($CleanEnvironment) { "pass" } else { "partial" }',
        "first_launch",
        "second_launch",
        "in_place_upgrade",
        "user_data_after_upgrade",
        "user_data_after_uninstall",
        "authenticode_status",
    ):
        assert token in smoke


def test_installed_smoke_contract_isolated_and_read_only():
    smoke = (PROJECT_ROOT / "scripts" / "smoke_installed_distribution.ps1").read_text(
        encoding="utf-8"
    )
    frozen_smoke = (PROJECT_ROOT / "scripts" / "smoke_frozen.py").read_text(
        encoding="utf-8"
    )

    assert "pyvideotrans-recipient-" in smoke
    assert '$env:PATH = $RecipientPath' in smoke
    assert '$env:LOCALAPPDATA = $IsolatedLocalAppData' in smoke
    assert "icacls.exe $InstallDir /deny" in smoke
    assert "collect_system_readiness" in frozen_smoke
    assert '"system_readiness": readiness' in frozen_smoke
