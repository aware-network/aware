"""Build a hash-complete Portable Protocol filesystem client bundle."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

CONTRACT = "aware.portable-protocol.client-distribution.v1"


class BuildError(RuntimeError):
    """A typed client-distribution build failure."""


def _run(
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture: bool = False,
) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        raise BuildError(f"command_failed:{args[0]}:{result.returncode}:{detail}")
    return (result.stdout or "").strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise BuildError(f"unsafe_source_path:{value}")
    return path


def load_spec(path: Path) -> dict[str, Any]:
    return _parse_spec(path.read_bytes())


def _parse_spec(raw: bytes) -> dict[str, Any]:
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise BuildError("invalid_source_spec") from error
    if data.get("schema") != "aware.portable-protocol.client-distribution-source.v1":
        raise BuildError("unsupported_source_spec")
    if data.get("authority_mode") != "filesystem":
        raise BuildError("unsupported_authority_mode")
    sources = data.get("source_packages")
    registries = data.get("registry_packages")
    derived = data.get("source_derived_packages", [])
    if not isinstance(sources, list) or not sources:
        raise BuildError("missing_source_packages")
    if not isinstance(registries, list) or not registries:
        raise BuildError("missing_registry_packages")
    if not isinstance(derived, list):
        raise BuildError("invalid_source_derived_packages")
    names: set[str] = set()
    for item in [*sources, *registries, *derived]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise BuildError("invalid_package_record")
        normalized = item["name"].lower().replace("_", "-")
        if normalized in names:
            raise BuildError(f"duplicate_package:{normalized}")
        names.add(normalized)
        if not isinstance(item.get("version"), str):
            raise BuildError(f"missing_package_version:{normalized}")
    for item in sources:
        _safe_relative(item.get("path", ""))
    if "package_source_revision" in data and not re.fullmatch(
        r"[0-9a-f]{40}", str(data["package_source_revision"])
    ):
        raise BuildError("invalid_package_source_revision")
    if "bundle_prefix" in data and not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", str(data["bundle_prefix"])
    ):
        raise BuildError("invalid_bundle_prefix")
    if "launchers" in data:
        launchers = data["launchers"]
        if not isinstance(launchers, list) or not launchers or any(
            not isinstance(item, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item)
            for item in launchers
        ):
            raise BuildError("invalid_launchers")
    if "package_lock_path" in data or "package_lock_sha256" in data:
        if not isinstance(data.get("package_lock_path"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", str(data.get("package_lock_sha256", ""))
        ):
            raise BuildError("invalid_package_lock_binding")
        _safe_relative(data["package_lock_path"])
    for item in [*sources, *registries, *derived]:
        if "hashes" in item and (
            not isinstance(item["hashes"], list) or not item["hashes"]
            or any(not isinstance(h, str) or not re.fullmatch(r"[0-9a-f]{64}", h)
                   for h in item["hashes"])
        ):
            origin = "source_derived" if item in derived else ("registry" if item in registries else "source")
            raise BuildError(f"invalid_{origin}_wheel_hashes")
    if derived:
        if not isinstance(data.get("consumer_lock_path"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", str(data.get("consumer_lock_sha256", ""))
        ):
            raise BuildError("invalid_consumer_lock_binding")
        _safe_relative(data["consumer_lock_path"])
        for item in derived:
            if len(item.get("hashes", [])) != 1:
                raise BuildError(f"source_derived_exact_hash_required:{item['name']}")
            if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("source_sha256", ""))):
                raise BuildError(f"invalid_source_derived_source_hash:{item['name']}")
            if not re.fullmatch(r"[0-9a-f]{40}", str(item.get("recipe_revision", ""))):
                raise BuildError(f"invalid_source_derived_recipe_revision:{item['name']}")
            for field in ("recipe", "constraints", "report"):
                if not isinstance(item.get(f"{field}_path"), str) or not re.fullmatch(
                    r"[0-9a-f]{64}", str(item.get(f"{field}_sha256", ""))
                ):
                    raise BuildError(f"invalid_source_derived_{field}_binding:{item['name']}")
                _safe_relative(item[f"{field}_path"])
    elif "consumer_lock_path" in data or "consumer_lock_sha256" in data:
        raise BuildError("consumer_lock_without_source_derived_packages")
    return data


def _committed_spec(
    repo: Path, path: Path, commit: str
) -> tuple[dict[str, Any], dict[str, str]]:
    try:
        relative = path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError as error:
        raise BuildError("source_spec_outside_repository") from error
    entry = _run("git", "ls-tree", commit, "--", relative, cwd=repo, capture=True)
    if not entry.startswith(("100644 blob ", "100755 blob ")):
        raise BuildError("source_spec_not_committed_regular_file")
    result = subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        raise BuildError("source_spec_unavailable")
    try:
        supplied = path.read_bytes()
    except OSError as error:
        raise BuildError("source_spec_unavailable") from error
    if supplied != result.stdout:
        raise BuildError("source_spec_revision_mismatch")
    # Parse retained committed bytes, never reread the mutable supplied file.
    return _parse_spec(result.stdout), {
        "path": relative,
        "sha256": hashlib.sha256(result.stdout).hexdigest(),
    }


def _committed_file(repo: Path, revision: str, path: str, expected_hash: str) -> bytes:
    entry = _run("git", "ls-tree", revision, "--", path, cwd=repo, capture=True)
    if not entry.startswith(("100644 blob ", "100755 blob ")):
        raise BuildError(f"committed_input_not_regular:{path}")
    result = subprocess.run(
        ("git", "show", f"{revision}:{path}"), cwd=repo,
        check=False, capture_output=True,
    )
    if result.returncode or hashlib.sha256(result.stdout).hexdigest() != expected_hash:
        raise BuildError(f"committed_input_hash_mismatch:{path}")
    return result.stdout


def _verify_source_derived_provenance(repo: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for package in spec.get("source_derived_packages", []):
        revision = package["recipe_revision"]
        bindings: dict[str, dict[str, str]] = {}
        for field in ("recipe", "constraints", "report"):
            path = package[f"{field}_path"]
            digest = package[f"{field}_sha256"]
            _committed_file(repo, revision, path, digest)
            bindings[field] = {"path": path, "sha256": digest}
        records.append({
            "name": package["name"], "version": package["version"],
            "wheel_sha256": package["hashes"][0],
            "source_sha256": package["source_sha256"],
            "recipe_revision": revision, **bindings,
        })
    return records


def _verify_consumer_lock(
    repo: Path, revision: str, spec: dict[str, Any], wheels: list[dict[str, str]]
) -> dict[str, str] | None:
    if not spec.get("source_derived_packages"):
        return None
    path = spec["consumer_lock_path"]
    digest = spec["consumer_lock_sha256"]
    raw = _committed_file(repo, revision, path, digest)
    try:
        lock = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise BuildError("invalid_consumer_lock") from error
    if any(lock.get(key) != spec[key] for key in ("profile", "python_minor", "platform")) or (
        lock.get("schema") != "aware.portable-protocol.consumer-wheel-lock.v1"
    ):
        raise BuildError("consumer_lock_target_mismatch")
    packages = lock.get("packages")
    if not isinstance(packages, list) or any(
        not isinstance(item, dict) or set(item) != {"name", "version", "origin", "sha256"}
        for item in packages
    ):
        raise BuildError("invalid_consumer_lock_packages")
    expected = sorted(
        ({key: item[key] for key in ("name", "version", "origin", "sha256")} for item in wheels),
        key=lambda item: item["name"].lower(),
    )
    if sorted(packages, key=lambda item: str(item["name"]).lower()) != expected:
        raise BuildError("consumer_lock_wheel_mismatch")
    return {"path": path, "sha256": digest, "revision": revision}


def _verify_build_environment(spec: dict[str, Any]) -> dict[str, str]:
    minor = f"{sys.version_info[0]}.{sys.version_info[1]}"
    if minor != spec.get("python_minor"):
        raise BuildError(f"build_python_minor_mismatch:{spec.get('python_minor')}:{minor}")
    if spec.get("platform") != "linux_x86_64":
        raise BuildError("unsupported_build_target")
    if platform.system().lower() != "linux" or platform.machine().lower() != "x86_64":
        raise BuildError("build_platform_mismatch:linux_x86_64")
    versions: dict[str, str] = {"python": platform.python_version()}
    for tool, command in (
        ("uv", ("uv", "--version")),
        ("pip", (sys.executable, "-m", "pip", "--version")),
    ):
        try:
            reported = _run(*command, capture=True).split()
        except (OSError, BuildError) as error:
            raise BuildError(f"build_tool_unavailable:{tool}") from error
        if len(reported) < 2 or reported[0] != tool:
            raise BuildError(f"build_tool_version_unavailable:{tool}")
        versions[tool] = reported[1]
    return versions


def _extract_revision(repo: Path, revision: str, destination: Path) -> int:
    commit = _run(
        "git", "rev-parse", "--verify", f"{revision}^{{commit}}", cwd=repo, capture=True
    )
    epoch_text = _run(
        "git", "show", "-s", "--format=%ct", commit, cwd=repo, capture=True
    )
    archive = destination.parent / "source.tar"
    with archive.open("wb") as stream:
        result = subprocess.run(
            ("git", "archive", "--format=tar", commit),
            cwd=repo,
            stdout=stream,
            check=False,
        )
    if result.returncode:
        raise BuildError(f"git_archive_failed:{result.returncode}")
    destination.mkdir()
    with tarfile.open(archive, "r:") as bundle:
        bundle.extractall(destination, filter="data")
    return int(epoch_text)


def _verify_source_metadata(source_root: Path, package: dict[str, str]) -> None:
    pyproject = source_root / Path(package["path"]) / "pyproject.toml"
    if not pyproject.is_file():
        raise BuildError(f"missing_pyproject:{package['path']}")
    metadata = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {})
    actual_name = str(metadata.get("name", "")).lower().replace("_", "-")
    expected_name = package["name"].lower().replace("_", "-")
    if actual_name != expected_name:
        raise BuildError(f"package_name_mismatch:{expected_name}:{actual_name}")
    if metadata.get("version") != package["version"]:
        raise BuildError(
            f"package_version_mismatch:{expected_name}:{package['version']}:{metadata.get('version')}"
        )


def _write_install_script(bundle: Path, spec: dict[str, Any]) -> None:
    requirements = " ".join(spec["interfaces"].values())
    expected_minor = spec["python_minor"]
    content = f"""#!/bin/sh
set -eu
PYTHON_BIN="${{PYTHON_BIN:-python3}}"
TARGET_VENV="${{1:-.aware-portable-venv}}"
actual_minor="$($PYTHON_BIN -c 'import sys; print(f"{{sys.version_info.major}}.{{sys.version_info.minor}}")')"
test "$actual_minor" = "{expected_minor}" || {{ echo "python_minor_mismatch:{expected_minor}:$actual_minor" >&2; exit 2; }}
"$PYTHON_BIN" -m venv "$TARGET_VENV"
"$TARGET_VENV/bin/python" -m pip install --no-index --find-links "$(dirname "$0")/wheelhouse" {requirements}
"$TARGET_VENV/bin/aware-protocol" version
"$TARGET_VENV/bin/aware-goal-cli" --help >/dev/null
"$TARGET_VENV/bin/aware-issue-cli" --help >/dev/null
"""
    target = bundle / "install.sh"
    target.write_text(content, encoding="utf-8")
    target.chmod(0o755)

    if "launchers" in spec:
        # Native CLI activation does not claim service interfaces in its closure.
        start = content.index('"$TARGET_VENV/bin/aware-protocol" version')
        content = content[:start] + "".join(
            f'"$TARGET_VENV/bin/{name}" --help >/dev/null\n'
            for name in spec["launchers"]
        )
        target.write_text(content, encoding="utf-8")


def _write_readme(bundle: Path, spec: dict[str, Any], revision: str) -> None:
    bundle.joinpath("README.md").write_text(
        "\n".join(
            [
                "# Aware Protocol filesystem client distribution",
                "",
                f"Source revision: `{revision}`",
                f"Authority mode: `{spec['authority_mode']}`",
                f"Protocol profile: `{spec['profile']}`",
                f"Target: `{spec['platform']}` / Python `{spec['python_minor']}`",
                "",
                "Install into a fresh environment:",
                "",
                "```bash",
                "./install.sh /absolute/path/to/new-venv",
                "```",
                "",
                "Verify `SHA256SUMS` before installation. This bundle exposes filesystem",
                "operations only. It contains no Service/API authority, credentials, Aware",
                "development checkout, editable package, or `PYTHONPATH` dependency.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _normalized_wheel_name(name: str) -> str:
    return name.lower().replace("-", "_")


def _verify_wheel_inventory(
    wheelhouse: Path, spec: dict[str, Any]
) -> list[dict[str, str]]:
    wheels = sorted(wheelhouse.glob("*.whl"))
    expected = [*spec["source_packages"], *spec["registry_packages"], *spec.get("source_derived_packages", [])]
    if len(wheels) != len(expected):
        raise BuildError(f"wheel_count_mismatch:{len(expected)}:{len(wheels)}")
    records: list[dict[str, str]] = []
    remaining = set(wheels)
    for package in expected:
        prefix = f"{_normalized_wheel_name(package['name'])}-{package['version']}-"
        matches = [path for path in remaining if path.name.lower().startswith(prefix)]
        if len(matches) != 1:
            raise BuildError(
                f"wheel_identity_mismatch:{package['name']}:{package['version']}:{len(matches)}"
            )
        wheel = matches[0]
        remaining.remove(wheel)
        origin = (
            "aware_source" if package in spec["source_packages"] else
            "source_derived" if package in spec.get("source_derived_packages", []) else
            "registry"
        )
        records.append(
            {
                "name": package["name"],
                "version": package["version"],
                "file": f"wheelhouse/{wheel.name}",
                "sha256": _sha256(wheel),
                "origin": origin,
            }
        )
        if package.get("hashes") and records[-1]["sha256"] not in package["hashes"]:
            diagnostic_origin = "source" if origin == "aware_source" else origin
            raise BuildError(f"{diagnostic_origin}_wheel_hash_mismatch:{package['name']}")
    return sorted(records, key=lambda item: item["name"].lower())


def _copy_retained_source_wheels(
    retained: Path, wheelhouse: Path, spec: dict[str, Any]
) -> None:
    """Reuse accepted bytes, not a rebuilt wheel assumed equivalent by version."""
    sources = spec["source_packages"]
    if any(not package.get("hashes") for package in sources):
        raise BuildError("retained_source_wheel_hashes_required")
    candidates = list(retained.glob("*.whl"))
    if len(candidates) != len(sources):
        raise BuildError("retained_source_wheel_count_mismatch")
    selected: list[tuple[Path, str]] = []
    for package in sources:
        prefix = f"{_normalized_wheel_name(package['name'])}-{package['version']}-"
        matches = [path for path in candidates if path.name.lower().startswith(prefix)]
        if len(matches) != 1:
            raise BuildError(f"retained_source_wheel_identity_mismatch:{package['name']}")
        path = matches[0]
        if path.is_symlink() or not path.is_file():
            raise BuildError("retained_source_wheel_not_regular")
        expected = _sha256(path)
        if expected not in package["hashes"]:
            raise BuildError(f"source_wheel_hash_mismatch:{package['name']}")
        selected.append((path, expected))
    for path, expected in selected:
        destination = wheelhouse / path.name
        shutil.copyfile(path, destination)
        if _sha256(destination) != expected:
            raise BuildError("retained_source_wheel_changed_during_copy")


def _copy_source_derived_wheels(
    retained: Path, wheelhouse: Path, spec: dict[str, Any]
) -> None:
    """Accept only exact reviewed derivative bytes; never fetch by version."""
    packages = spec["source_derived_packages"]
    candidates = list(retained.glob("*.whl"))
    if len(candidates) != len(packages):
        raise BuildError("source_derived_wheel_count_mismatch")
    selected: list[tuple[Path, str]] = []
    for package in packages:
        prefix = f"{_normalized_wheel_name(package['name'])}-{package['version']}-"
        matches = [path for path in candidates if path.name.lower().startswith(prefix)]
        if len(matches) != 1:
            raise BuildError(f"source_derived_wheel_identity_mismatch:{package['name']}")
        path = matches[0]
        if path.is_symlink() or not path.is_file():
            raise BuildError("source_derived_wheel_not_regular")
        expected = package["hashes"][0]
        if _sha256(path) != expected:
            raise BuildError(f"source_derived_wheel_hash_mismatch:{package['name']}")
        selected.append((path, expected))
    for path, expected in selected:
        destination = wheelhouse / path.name
        shutil.copyfile(path, destination)
        if _sha256(destination) != expected:
            raise BuildError("source_derived_wheel_changed_during_copy")


def _deterministic_tar(source: Path, target: Path, epoch: int) -> None:
    with (
        target.open("wb") as raw,
        gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=epoch
        ) as compressed,
        tarfile.open(fileobj=compressed, mode="w:") as archive,
    ):
        for path in sorted(source.rglob("*")):
            relative = path.relative_to(source.parent)
            info = archive.gettarinfo(str(path), arcname=str(relative))
            info.uid = 0
            info.gid = 0
            info.uname = "root"
            info.gname = "root"
            info.mtime = epoch
            if path.is_file():
                with path.open("rb") as stream:
                    archive.addfile(info, stream)
            else:
                archive.addfile(info)


def assemble_retained_distribution(
    spec: dict[str, Any],
    wheelhouse: Path,
    output: Path,
    provenance: dict[str, Any],
    *,
    epoch: int,
) -> dict[str, Any]:
    """Assemble a separately governed internal projection, never another engine.

    Callers qualify source projections/builds separately. This entrance admits
    only a hash-complete wheel inventory; it does not solve dependencies or
    establish source, installation, notice or public-release acceptance.
    """
    if spec.get("authority_mode") != "filesystem":
        raise BuildError("unsupported_authority_mode")
    prefix = spec.get("bundle_prefix", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", prefix):
        raise BuildError("invalid_bundle_prefix")
    if spec.get("platform") != "linux_x86_64" or spec.get("python_minor") != "3.12":
        raise BuildError("unsupported_build_target")
    packages = [
        *spec["source_packages"],
        *spec["registry_packages"],
        *spec.get("source_derived_packages", []),
    ]
    names = [p["name"].lower().replace("_", "-") for p in packages]
    if len(set(names)) != len(names):
        raise BuildError("duplicate_package")
    if any(len(p.get("hashes", [])) != 1 for p in packages):
        raise BuildError("exact_wheel_hashes_required")
    if any(p.is_symlink() or not p.is_file() for p in wheelhouse.iterdir()):
        raise BuildError("retained_wheelhouse_not_regular")
    wheels = _verify_wheel_inventory(wheelhouse, spec)
    if {p.name for p in wheelhouse.iterdir()} != {Path(w["file"]).name for w in wheels}:
        raise BuildError("retained_wheelhouse_extra_member")
    bundle = output / prefix
    archive = output / (prefix + ".tar.gz")
    if (
        bundle.exists()
        or bundle.is_symlink()
        or archive.exists()
        or archive.is_symlink()
    ):
        raise BuildError("immutable_candidate_exists")
    output.mkdir(parents=True, exist_ok=True)
    destination = bundle / "wheelhouse"
    destination.mkdir(parents=True)
    for wheel in wheels:
        target = bundle / wheel["file"]
        shutil.copyfile(wheelhouse / target.name, target)
        if _sha256(target) != wheel["sha256"]:
            raise BuildError("retained_wheel_changed_during_copy")
    _write_install_script(bundle, spec)
    _write_readme(bundle, spec, provenance["owner_revision"])
    with (bundle / "README.md").open("a", encoding="utf-8") as stream:
        stream.write(
            "\nInternal setup/read qualification candidate, not a customer release.\n"
            "Setup uses the installed typed optional composition; no setup CLI\n"
            "or governed SPEC draft writer is supplied. Existing qualified SPEC\n"
            "documents/iterations are separately supplied test input.\n"
            "Currentness means exact observed state under cooperative filesystem\n"
            "topology; it is not detection of every intervening write. Equal-byte\n"
            "same-inode rewrites can be unobservable. Every-write detection and\n"
            "continuous confinement are unsupported by this profile.\n"
        )
    lock = {
        "schema": "aware.portable-protocol.consumer-wheel-lock.v1",
        "profile": spec["profile"],
        "python_minor": "3.12",
        "platform": "linux_x86_64",
        "packages": [
            {k: w[k] for k in ("name", "version", "origin", "sha256")} for w in wheels
        ],
    }
    manifest = {
        "schema": CONTRACT,
        "status": "internal-installed-qualification-candidate",
        "profile": spec["profile"],
        "authority_mode": "filesystem",
        "target": {"python_minor": "3.12", "declared_platform": "linux_x86_64"},
        "interfaces": spec["interfaces"],
        "launchers": spec["launchers"],
        "package_count": len(wheels),
        "wheels": wheels,
        "source_provenance": provenance,
        "nonclaims": [
            "installed_acceptance",
            "draft_authoring",
            "service_authority",
            "notice_clearance",
            "consumer_freeze",
            "public_release",
        ],
    }
    for name, value in (("manifest.json", manifest), ("consumer-lock.json", lock)):
        (bundle / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    files = sorted(p for p in bundle.rglob("*") if p.is_file())
    (bundle / "SHA256SUMS").write_text(
        "".join(
            _sha256(p) + "  " + p.relative_to(bundle).as_posix() + "\n" for p in files
        )
    )
    _deterministic_tar(bundle, archive, epoch)
    return {
        "archive": str(archive),
        "archive_sha256": _sha256(archive),
        "manifest_sha256": _sha256(bundle / "manifest.json"),
        "consumer_lock_sha256": _sha256(bundle / "consumer-lock.json"),
        "package_count": len(wheels),
        "bundle_directory": str(bundle),
    }


def build(
    repo: Path, spec_path: Path, revision: str, output: Path,
    *, retained_source_wheelhouse: Path | None = None,
    retained_source_derived_wheelhouse: Path | None = None,
) -> dict[str, Any]:
    commit = _run(
        "git", "rev-parse", "--verify", f"{revision}^{{commit}}", cwd=repo, capture=True
    )
    spec, source_spec = _committed_spec(repo, spec_path, commit)
    derived = spec.get("source_derived_packages", [])
    if bool(derived) != (retained_source_derived_wheelhouse is not None):
        raise BuildError("source_derived_wheelhouse_selection_mismatch")
    derived_provenance = _verify_source_derived_provenance(repo, spec)
    build_tools = _verify_build_environment(spec)
    package_commit = spec.get("package_source_revision", commit)
    if _run("git", "rev-parse", "--verify", f"{package_commit}^{{commit}}", cwd=repo, capture=True) != package_commit:
        raise BuildError("package_source_revision_mismatch")
    package_lock = None
    if "package_lock_path" in spec:
        lock = subprocess.run(
            ("git", "show", f"{package_commit}:{spec['package_lock_path']}"),
            cwd=repo, check=False, capture_output=True,
        )
        if lock.returncode or hashlib.sha256(lock.stdout).hexdigest() != spec["package_lock_sha256"]:
            raise BuildError("package_lock_revision_mismatch")
        package_lock = {"path": spec["package_lock_path"], "sha256": spec["package_lock_sha256"]}
    prefix = spec.get("bundle_prefix", "aware-portable-protocol-fs-v1")
    bundle_name = f"{prefix}-{package_commit[:12]}-{spec['platform']}-py{spec['python_minor'].replace('.', '')}"
    output.mkdir(parents=True, exist_ok=True)
    bundle = output / bundle_name
    archive_path = output / f"{bundle_name}.tar.gz"
    if bundle.exists() or archive_path.exists():
        raise BuildError(f"output_exists:{bundle_name}")

    with tempfile.TemporaryDirectory(
        prefix="aware-portable-client-build-"
    ) as temporary:
        temp = Path(temporary)
        source_root = temp / "source"
        epoch = _extract_revision(repo, package_commit, source_root)
        wheelhouse = bundle / "wheelhouse"
        wheelhouse.mkdir(parents=True)
        environment = os.environ.copy()
        environment.update({"SOURCE_DATE_EPOCH": str(epoch), "PYTHONHASHSEED": "0"})

        for package in spec["source_packages"]:
            _verify_source_metadata(source_root, package)
            if retained_source_wheelhouse is None:
                _run(
                    "uv", "build", "--wheel", "--no-create-gitignore",
                    "--python", sys.executable, "--no-python-downloads",
                    "--out-dir", str(wheelhouse),
                    str(source_root / Path(package["path"])), env=environment,
                )
        if retained_source_wheelhouse is not None:
            _copy_retained_source_wheels(retained_source_wheelhouse, wheelhouse, spec)
        if retained_source_derived_wheelhouse is not None:
            _copy_source_derived_wheels(retained_source_derived_wheelhouse, wheelhouse, spec)

        registry_requirements = [
            f"{item['name']}=={item['version']}" for item in spec["registry_packages"]
        ]
        _run(
            sys.executable,
            "-m",
            "pip",
            "download",
            "--only-binary=:all:",
            "--no-deps",
            "--dest",
            str(wheelhouse),
            *registry_requirements,
        )

        wheels = _verify_wheel_inventory(wheelhouse, spec)
        consumer_lock = _verify_consumer_lock(repo, commit, spec, wheels)
        _write_install_script(bundle, spec)
        _write_readme(bundle, spec, package_commit)
        manifest = {
            "schema": CONTRACT,
            "profile": spec["profile"],
            "authority_mode": spec["authority_mode"],
            "source_revision": package_commit,
            "build_spec_revision": commit,
            "source_spec": source_spec,
            "build_tools": build_tools,
            "source_wheel_mode": "rebuilt" if retained_source_wheelhouse is None else "retained_hash_verified",
            "package_lock": package_lock,
            "consumer_lock": consumer_lock,
            "source_derived_provenance": derived_provenance,
            "source_commit_epoch": epoch,
            "target": {
                "declared_platform": spec["platform"],
                "python_minor": spec["python_minor"],
                "build_system": platform.system().lower(),
                "build_machine": platform.machine().lower(),
            },
            "interfaces": spec["interfaces"],
            "package_count": len(wheels),
            "editable_packages": 0,
            "wheels": wheels,
            "nonclaims": [
                "service_api_authority",
                "actor_world_participation",
                "goal_acceptance",
                "general_release_acceptance",
            ],
        }
        manifest_path = bundle / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        checksum_paths = [
            bundle / "README.md",
            bundle / "install.sh",
            manifest_path,
            *wheelhouse.glob("*.whl"),
        ]
        bundle.joinpath("SHA256SUMS").write_text(
            "".join(
                f"{_sha256(path)}  {path.relative_to(bundle).as_posix()}\n"
                for path in sorted(checksum_paths)
            ),
            encoding="utf-8",
        )
        _deterministic_tar(bundle, archive_path, epoch)

    result = {
        "schema": "aware.portable-protocol.client-distribution-build-result.v1",
        "status": "built",
        "bundle_directory": str(bundle),
        "archive": str(archive_path),
        "archive_sha256": _sha256(archive_path),
        "manifest_sha256": _sha256(bundle / "manifest.json"),
        "source_revision": package_commit,
        "build_spec_revision": commit,
        "source_spec": source_spec,
        "build_tools": build_tools,
        "package_lock": package_lock,
        "consumer_lock": consumer_lock,
        "source_derived_provenance": derived_provenance,
        "package_count": len(manifest["wheels"]),
    }
    output.joinpath(f"{bundle_name}.build-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--retained-source-wheelhouse", type=Path)
    parser.add_argument("--retained-source-derived-wheelhouse", type=Path)
    args = parser.parse_args()
    try:
        result = build(
            args.repo_root.resolve(),
            args.spec.resolve(),
            args.source_revision,
            args.output_dir.resolve(),
            retained_source_wheelhouse=args.retained_source_wheelhouse,
            retained_source_derived_wheelhouse=args.retained_source_derived_wheelhouse,
        )
    except BuildError as error:
        print(
            json.dumps(
                {"schema": CONTRACT, "status": "failed", "diagnostic": str(error)},
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
