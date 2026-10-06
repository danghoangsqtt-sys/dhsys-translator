from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


SCHEMA_VERSION = 1
PRODUCT_NAME = "pyVideoTrans-DH"
ARCH_LABEL = "win64"

_USER_TOP_LEVEL_DIRS = {
    "cache",
    "logs",
    "models",
    "output",
    "pretrained_models",
    "runtime",
    "tmp",
}
_USER_CONFIG_NAMES = {
    ".env",
    ".netrc",
    "cfg.json",
    "cookies.txt",
    "credentials.json",
    "glossary.txt",
    "params.json",
    "secrets.json",
    "token.json",
    "webui_state.json",
}
_TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".iss",
    ".js",
    ".json",
    ".md",
    ".py",
    ".pyi",
    ".ps1",
    ".rst",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalized_relative_path(value: str | Path) -> str:
    raw = str(value).replace("\\", "/")
    if raw.startswith("/") or _WINDOWS_ABSOLUTE_RE.match(raw):
        raise ValueError(f"absolute path is not allowed: {value}")
    path = PurePosixPath(raw)
    if not raw or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"invalid relative path: {value}")
    return path.as_posix()


def artifact_names(version: str) -> dict[str, str]:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", version):
        raise ValueError(f"invalid product version: {version!r}")
    prefix = f"{PRODUCT_NAME}-{version}-{ARCH_LABEL}"
    return {
        "portable": f"{prefix}-portable.zip",
        "setup": f"{prefix}-setup.exe",
        "manifest": f"{prefix}-manifest.json",
    }


def forbidden_path_reason(relative_path: str | Path) -> str | None:
    normalized = normalized_relative_path(relative_path)
    parts = [part.lower() for part in PurePosixPath(normalized).parts]
    if parts[0] in _USER_TOP_LEVEL_DIRS:
        return f"user/runtime directory is not distributable: {parts[0]}"

    name = parts[-1]
    if name in _USER_CONFIG_NAMES:
        if len(parts) == 1 or "videotrans" in parts:
            return f"user configuration/credential file is not distributable: {name}"

    if name.endswith((".log", ".bak")) and len(parts) == 1:
        return f"runtime file is not distributable: {name}"
    return None


def _iter_candidate_files(candidate: Path):
    for path in sorted((item for item in candidate.rglob("*") if item.is_file())):
        relative = path.relative_to(candidate).as_posix()
        reason = forbidden_path_reason(relative)
        if reason:
            raise ValueError(f"{relative}: {reason}")
        yield path, relative


def _scan_text_for_build_roots(path: Path, roots: tuple[str, ...]) -> None:
    if path.suffix.lower() not in _TEXT_SUFFIXES or path.stat().st_size > 2 * 1024 * 1024:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    lowered = text.lower().replace("/", "\\")
    for root in roots:
        marker = root.lower().replace("/", "\\").rstrip("\\")
        if marker and marker in lowered:
            raise ValueError(f"build-machine absolute path leaked into text file: {path.name}")


def build_candidate_inventory(candidate: Path, build_roots: tuple[str, ...] = ()) -> dict:
    candidate = candidate.resolve()
    executable = candidate / "sp.exe"
    if not executable.is_file():
        raise FileNotFoundError(f"missing frozen entry point: {executable}")

    files: list[dict] = []
    total_bytes = 0
    normalized_roots = tuple(str(Path(root).resolve()) for root in build_roots if root)
    for path, relative in _iter_candidate_files(candidate):
        _scan_text_for_build_roots(path, normalized_roots)
        size = path.stat().st_size
        total_bytes += size
        files.append({
            "path": relative,
            "size": size,
            "sha256": sha256_file(path),
        })

    file_paths = {item["path"] for item in files}
    if "_internal/LICENSE" not in file_paths:
        raise ValueError("frozen candidate is missing the bundled project LICENSE")
    license_files = [
        item["path"]
        for item in files
        if PurePosixPath(item["path"]).name.upper().startswith(("LICENSE", "LICENCE", "NOTICE", "COPYING"))
    ]
    largest = sorted(files, key=lambda item: item["size"], reverse=True)[:20]
    return {
        "root_name": candidate.name,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "entry_point": "sp.exe",
        "entry_point_sha256": sha256_file(executable),
        "license_files": license_files,
        "third_party_notice_count": max(0, len(license_files) - 1),
        "largest_files": largest,
        "files": files,
    }


def make_manifest(
    *,
    version: str,
    candidate: Path,
    build_roots: tuple[str, ...] = (),
) -> dict:
    names = artifact_names(version)
    return {
        "schema_version": SCHEMA_VERSION,
        "product": PRODUCT_NAME,
        "version": version,
        "architecture": ARCH_LABEL,
        "candidate": build_candidate_inventory(candidate, build_roots),
        "artifacts": {
            "portable": {"name": names["portable"]},
            "setup": {"name": names["setup"]},
        },
    }


def load_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported distribution manifest schema")
    if payload.get("product") != PRODUCT_NAME:
        raise ValueError("unexpected product in distribution manifest")
    artifact_names(str(payload.get("version", "")))
    candidate = payload.get("candidate") or {}
    if candidate.get("entry_point") != "sp.exe" or not isinstance(candidate.get("files"), list):
        raise ValueError("distribution manifest is missing candidate inventory")
    return payload


def write_manifest(path: Path, payload: dict) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if re.search(r'(?i)[A-Z]:[\\/]', serialized):
        raise ValueError("manifest contains a build-machine absolute Windows path")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized + "\n", encoding="utf-8")


def record_artifact(manifest_path: Path, kind: str, artifact_path: Path) -> dict:
    payload = load_manifest(manifest_path)
    if kind not in {"portable", "setup"}:
        raise ValueError(f"unknown artifact kind: {kind}")
    expected_name = payload["artifacts"][kind]["name"]
    if artifact_path.name != expected_name:
        raise ValueError(f"unexpected {kind} filename: {artifact_path.name}; expected {expected_name}")
    if not artifact_path.is_file():
        raise FileNotFoundError(f"missing {kind} artifact: {artifact_path}")
    payload["artifacts"][kind].update({
        "size": artifact_path.stat().st_size,
        "sha256": sha256_file(artifact_path),
    })
    write_manifest(manifest_path, payload)
    return payload


def write_sha256_sidecar(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(path)
    sidecar = Path(f"{path}.sha256")
    sidecar.write_text(f"{sha256_file(path)}  {path.name}\n", encoding="ascii")
    return sidecar


def verify_sha256_sidecar(path: Path) -> None:
    sidecar = Path(f"{path}.sha256")
    if not sidecar.is_file():
        raise FileNotFoundError(f"missing SHA-256 sidecar: {sidecar}")
    line = sidecar.read_text(encoding="ascii").strip()
    match = re.fullmatch(r"([A-Fa-f0-9]{64})\s{2}(.+)", line)
    if not match:
        raise ValueError(f"invalid SHA-256 sidecar format: {sidecar.name}")
    expected_hash, expected_name = match.groups()
    if expected_name != path.name:
        raise ValueError(f"SHA-256 sidecar names {expected_name!r}, expected {path.name!r}")
    actual_hash = sha256_file(path)
    if actual_hash.upper() != expected_hash.upper():
        raise ValueError(f"SHA-256 mismatch for {path.name}")


def verify_candidate_against_manifest(candidate: Path, payload: dict) -> None:
    candidate = candidate.resolve()
    expected = {item["path"]: item for item in payload["candidate"]["files"]}
    actual_paths = {
        path.relative_to(candidate).as_posix()
        for path in candidate.rglob("*")
        if path.is_file()
    }
    expected_paths = set(expected)
    missing = sorted(expected_paths - actual_paths)
    unexpected = sorted(actual_paths - expected_paths)
    if missing:
        raise ValueError(f"candidate is missing files: {missing[:5]}")
    if unexpected:
        raise ValueError(f"candidate has unexpected files: {unexpected[:5]}")
    for relative, item in expected.items():
        path = candidate / Path(relative)
        reason = forbidden_path_reason(relative)
        if reason:
            raise ValueError(f"{relative}: {reason}")
        if path.stat().st_size != item["size"]:
            raise ValueError(f"size mismatch: {relative}")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {relative}")


def verify_zip_members(zip_path: Path, payload: dict) -> None:
    root_name = payload["candidate"]["root_name"]
    expected = {f"{root_name}/{item['path']}": item for item in payload["candidate"]["files"]}
    with zipfile.ZipFile(zip_path) as archive:
        members = {
            name.replace("\\", "/"): info
            for info in archive.infolist()
            if not info.is_dir()
            for name in [info.filename]
        }
        actual_names = set(members)
        expected_names = set(expected)
        missing = sorted(expected_names - actual_names)
        unexpected = sorted(actual_names - expected_names)
        if missing:
            raise ValueError(f"portable ZIP is missing files: {missing[:5]}")
        if unexpected:
            raise ValueError(f"portable ZIP has unexpected files: {unexpected[:5]}")
        required_entry = f"{root_name}/sp.exe"
        if required_entry not in members:
            raise ValueError("portable ZIP is missing sp.exe")
        for name in actual_names:
            relative = name[len(root_name) + 1 :]
            reason = forbidden_path_reason(relative)
            if reason:
                raise ValueError(f"{name}: {reason}")


def verify_release(manifest_path: Path, release_dir: Path, require_installer: bool = True) -> dict:
    payload = load_manifest(manifest_path)
    release_dir = release_dir.resolve()
    portable = release_dir / payload["artifacts"]["portable"]["name"]
    setup = release_dir / payload["artifacts"]["setup"]["name"]

    for kind, path in (("portable", portable), ("setup", setup)):
        details = payload["artifacts"][kind]
        if kind == "setup" and not require_installer and "sha256" not in details:
            continue
        if not path.is_file():
            raise FileNotFoundError(f"missing {kind} artifact: {path}")
        if details.get("size") != path.stat().st_size:
            raise ValueError(f"size mismatch for {path.name}")
        if details.get("sha256") != sha256_file(path):
            raise ValueError(f"SHA-256 mismatch for {path.name}")
        verify_sha256_sidecar(path)

    verify_sha256_sidecar(manifest_path)
    verify_zip_members(portable, payload)
    return payload


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and verify pyVideoTrans-DH distribution manifests")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("--candidate", type=Path, required=True)
    inventory.add_argument("--manifest", type=Path, required=True)
    inventory.add_argument("--version", required=True)
    inventory.add_argument("--build-root", action="append", default=[])

    record = subparsers.add_parser("record-artifact")
    record.add_argument("--manifest", type=Path, required=True)
    record.add_argument("--kind", choices=("portable", "setup"), required=True)
    record.add_argument("--path", type=Path, required=True)

    sidecar = subparsers.add_parser("sidecar")
    sidecar.add_argument("--path", type=Path, required=True)

    verify_tree = subparsers.add_parser("verify-tree")
    verify_tree.add_argument("--manifest", type=Path, required=True)
    verify_tree.add_argument("--candidate", type=Path, required=True)

    verify_release_parser = subparsers.add_parser("verify-release")
    verify_release_parser.add_argument("--manifest", type=Path, required=True)
    verify_release_parser.add_argument("--release-dir", type=Path, required=True)
    verify_release_parser.add_argument("--allow-missing-installer", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    try:
        if args.command == "inventory":
            payload = make_manifest(
                version=args.version,
                candidate=args.candidate,
                build_roots=tuple(args.build_root),
            )
            write_manifest(args.manifest, payload)
        elif args.command == "record-artifact":
            record_artifact(args.manifest, args.kind, args.path)
        elif args.command == "sidecar":
            write_sha256_sidecar(args.path)
        elif args.command == "verify-tree":
            verify_candidate_against_manifest(args.candidate, load_manifest(args.manifest))
        elif args.command == "verify-release":
            verify_release(
                args.manifest,
                args.release_dir,
                require_installer=not args.allow_missing_installer,
            )
        else:  # pragma: no cover - argparse prevents this branch.
            raise ValueError(f"unsupported command: {args.command}")
    except (FileNotFoundError, OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
