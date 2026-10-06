"""Build a distinct, source-derived jsonschema wheel without benchmarks.

This is an internal package-owner build input, not a registry-wheel rewrite or
public release operation. It downloads only pinned inputs, builds in a temporary
source tree, verifies the resulting wheel, then writes a new private output dir.
"""

from __future__ import annotations

import argparse
import base64
import csv
from email.parser import BytesParser
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import urllib.error
import urllib.request
import zipfile

SOURCE_URL = (
    "https://files.pythonhosted.org/packages/b3/fc/"
    "e067678238fa451312d4c62bf6e6cf5ec56375422aee02f9cb5f909b3047/"
    "jsonschema-4.26.0.tar.gz"
)
SOURCE_SHA256 = "0c26707e2efad8aa1bfc5b7ce170f3fccc2e4918ff85989ba9ffa9facb2be326"
OFFICIAL_WHEEL_URL = (
    "https://files.pythonhosted.org/packages/69/90/"
    "f63fb5873511e014207a475e2bb4e8b2e570d655b00ac19a9a0ca0a385ee/"
    "jsonschema-4.26.0-py3-none-any.whl"
)
OFFICIAL_WHEEL_SHA256 = "d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce"
SOURCE_ROOT = "jsonschema-4.26.0"
TARGET_VERSION = "4.26.0+aware.1"
TARGET_WHEEL_NAME = "jsonschema-4.26.0+aware.1-py3-none-any.whl"
BUILD_EPOCH = "1760000000"
CONSTRAINTS = Path(__file__).with_name("build-constraints-jsonschema-v1.txt")

MODIFICATIONS = f"""# Aware packaging modification

This wheel is derived from the jsonschema 4.26.0 source archive, SHA-256
{SOURCE_SHA256}. Aware changed the wheel build configuration to omit the
`jsonschema/benchmarks/` subtree and assigned the distinct local version
`{TARGET_VERSION}`. The upstream runtime Python modules are unchanged.
The original jsonschema MIT COPYING remains included. This document describes
the packaging delta; it does not assert rights over separately sourced content.
"""


class BuildRefusal(RuntimeError):
    """A pinned source, build, or wheel invariant was not met."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_pinned(url: str, expected_sha256: str, *, max_bytes: int = 10_000_000) -> bytes:
    if not url.startswith("https://files.pythonhosted.org/"):
        raise BuildRefusal("source_url_untrusted")
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise BuildRefusal("source_too_large")
    if sha256(data) != expected_sha256:
        raise BuildRefusal("source_digest_mismatch")
    return data


def extract_source(data: bytes, destination: Path) -> Path:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise BuildRefusal("empty_source_archive")
        for member in members:
            path = PurePosixPath(member.name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or path.parts[0] != SOURCE_ROOT
                or not (member.isfile() or member.isdir())
            ):
                raise BuildRefusal(f"unsafe_source_member:{member.name}")
        archive.extractall(destination, members=members, filter="data")
    root = destination / SOURCE_ROOT
    if not (root / "pyproject.toml").is_file():
        raise BuildRefusal("source_pyproject_missing")
    return root


def _replace_once(source: str, old: str, new: str, reason: str) -> str:
    if source.count(old) != 1:
        raise BuildRefusal(f"source_contract_drift:{reason}")
    return source.replace(old, new, 1)


def patched_pyproject(source: str) -> str:
    result = _replace_once(
        source,
        'requires = ["hatchling", "hatch-vcs", "hatch-fancy-pypi-readme"]',
        'requires = ["hatchling", "hatch-fancy-pypi-readme"]',
        "build_requirements",
    )
    result = _replace_once(
        result, '[tool.hatch.version]\nsource = "vcs"\n\n', "", "vcs_version"
    )
    result = _replace_once(
        result, '[project]\nname = "jsonschema"',
        f'[project]\nname = "jsonschema"\nversion = "{TARGET_VERSION}"',
        "project_version",
    )
    result = _replace_once(
        result, 'license-files = ["COPYING"]',
        'license-files = ["COPYING", "AWARE-MODIFICATIONS.md"]',
        "license_files",
    )
    result = _replace_once(
        result, 'dynamic = ["version", "readme"]',
        'dynamic = ["readme"]',
        "dynamic_version",
    )
    if "[tool.hatch.build.targets.wheel]" in result:
        raise BuildRefusal("source_contract_drift:wheel_target")
    result += '\n[tool.hatch.build.targets.wheel]\nexclude = ["/jsonschema/benchmarks/**"]\n'
    metadata = tomllib.loads(result)
    if metadata["project"]["version"] != TARGET_VERSION:
        raise BuildRefusal("patched_version_invalid")
    if metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["exclude"] != [
        "/jsonschema/benchmarks/**"
    ]:
        raise BuildRefusal("patched_exclusion_invalid")
    return result


def _metadata(wheel: zipfile.ZipFile) -> tuple[object, bytes, bytes]:
    names = wheel.namelist()
    metadata_path = next(
        (name for name in names if name.endswith(".dist-info/METADATA")), None
    )
    entry_path = next(
        (name for name in names if name.endswith(".dist-info/entry_points.txt")), None
    )
    legal_path = next(
        (name for name in names if name.endswith(".dist-info/licenses/COPYING")), None
    )
    if not metadata_path or not entry_path or not legal_path:
        raise BuildRefusal("wheel_metadata_missing")
    metadata = BytesParser().parsebytes(wheel.read(metadata_path))
    return metadata, wheel.read(entry_path), wheel.read(legal_path)


def _verify_record(wheel: zipfile.ZipFile) -> None:
    names = wheel.namelist()
    if len(names) != len(set(names)):
        raise BuildRefusal("duplicate_wheel_member")
    record_name = next((name for name in names if name.endswith(".dist-info/RECORD")), None)
    if record_name is None:
        raise BuildRefusal("wheel_record_missing")
    record = list(csv.reader(io.StringIO(wheel.read(record_name).decode("utf-8"))))
    if {row[0] for row in record} != set(names):
        raise BuildRefusal("wheel_record_incomplete")
    for path, digest, size in record:
        if path == record_name:
            if digest or size:
                raise BuildRefusal("wheel_record_self_hash")
            continue
        data = wheel.read(path)
        expected = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        if digest != f"sha256={expected}" or size != str(len(data)):
            raise BuildRefusal(f"wheel_record_mismatch:{path}")


def verify_wheel(candidate: bytes, official: bytes) -> dict[str, object]:
    with zipfile.ZipFile(io.BytesIO(candidate)) as built, zipfile.ZipFile(
        io.BytesIO(official)
    ) as original:
        _verify_record(built)
        built_names = set(built.namelist())
        original_names = set(original.namelist())
        benchmark = sorted(
            name for name in original_names if name.startswith("jsonschema/benchmarks/")
        )
        if len(benchmark) != 13:
            raise BuildRefusal("official_benchmark_inventory_changed")
        if any(name.startswith("jsonschema/benchmarks/") for name in built_names):
            raise BuildRefusal("benchmark_subtree_retained")
        original_runtime = {
            name for name in original_names
            if name.startswith("jsonschema/") and not name.startswith("jsonschema/benchmarks/")
        }
        built_runtime = {name for name in built_names if name.startswith("jsonschema/")}
        if built_runtime != original_runtime:
            raise BuildRefusal("runtime_member_set_changed")
        for name in original_runtime:
            if built.read(name) != original.read(name):
                raise BuildRefusal(f"runtime_member_bytes_changed:{name}")
        built_metadata, built_entry, built_legal = _metadata(built)
        original_metadata, original_entry, original_legal = _metadata(original)
        if built_metadata["Name"] != "jsonschema" or built_metadata["Version"] != TARGET_VERSION:
            raise BuildRefusal("wheel_identity_invalid")
        if sorted(built_metadata.get_all("Requires-Dist", [])) != sorted(
            original_metadata.get_all("Requires-Dist", [])
        ):
            raise BuildRefusal("wheel_dependencies_changed")
        if built_entry != original_entry or built_legal != original_legal:
            raise BuildRefusal("wheel_entry_or_license_changed")
        notice_path = (
            f"jsonschema-{TARGET_VERSION}.dist-info/licenses/AWARE-MODIFICATIONS.md"
        )
        if notice_path not in built_names or built.read(notice_path) != MODIFICATIONS.encode():
            raise BuildRefusal("modification_notice_missing")
        return {
            "omitted_benchmark_members": len(benchmark),
            "preserved_runtime_members": len(original_runtime),
            "dependencies_unchanged": True,
            "entrypoint_unchanged": True,
            "upstream_copying_unchanged": True,
            "record_verified": True,
        }


def _run(*args: str, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(args, env=env, check=False, capture_output=True, text=True)
    if result.returncode:
        raise BuildRefusal(
            f"tool_failed:{Path(args[0]).name}:{result.returncode}:"
            f"{result.stderr[-1200:]}"
        )


def build(output: Path, python: Path, uv: Path) -> dict[str, object]:
    if output.exists():
        raise BuildRefusal("output_exists")
    if not output.parent.is_dir() or not python.is_file() or not uv.is_file():
        raise BuildRefusal("build_input_unavailable")
    source = fetch_pinned(SOURCE_URL, SOURCE_SHA256)
    official = fetch_pinned(OFFICIAL_WHEEL_URL, OFFICIAL_WHEEL_SHA256)
    constraints_sha = sha256(CONSTRAINTS.read_bytes())

    with tempfile.TemporaryDirectory(prefix="aware-jsonschema-cb-") as temp_name:
        temp = Path(temp_name)
        source_root = extract_source(source, temp / "source")
        pyproject = source_root / "pyproject.toml"
        patched = patched_pyproject(pyproject.read_text(encoding="utf-8"))
        pyproject.write_text(patched, encoding="utf-8")
        (source_root / "AWARE-MODIFICATIONS.md").write_text(
            MODIFICATIONS, encoding="utf-8"
        )
        build_wheels = temp / "build-wheels"
        build_wheels.mkdir()
        environment = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "LANG": "C.UTF-8",
            "SOURCE_DATE_EPOCH": BUILD_EPOCH,
            "PYTHONHASHSEED": "0",
        }
        _run(
            str(python), "-m", "pip", "download", "--disable-pip-version-check",
            "--only-binary=:all:", "--no-deps", "--require-hashes",
            "--dest", str(build_wheels), "-r", str(CONSTRAINTS), env=environment,
        )
        if len(list(build_wheels.glob("*.whl"))) != 7:
            raise BuildRefusal("build_dependency_count_mismatch")
        dist = temp / "dist"
        dist.mkdir()
        _run(
            str(uv), "build", "--no-config", "--no-cache", "--offline",
            "--no-index", "--find-links", str(build_wheels),
            "--build-constraints", str(CONSTRAINTS), "--require-hashes",
            "--python", str(python), "--no-python-downloads", "--wheel",
            "--out-dir", str(dist), str(source_root), env=environment,
        )
        wheels = list(dist.glob("*.whl"))
        if len(wheels) != 1 or wheels[0].name != TARGET_WHEEL_NAME:
            raise BuildRefusal("built_wheel_identity_mismatch")
        candidate = wheels[0].read_bytes()
        verification = verify_wheel(candidate, official)
        result: dict[str, object] = {
            "status": "internal_source_wheel_verified",
            "distribution": "jsonschema",
            "version": TARGET_VERSION,
            "source_sha256": SOURCE_SHA256,
            "official_wheel_sha256": OFFICIAL_WHEEL_SHA256,
            "constraints_sha256": constraints_sha,
            "patched_pyproject_sha256": sha256(patched.encode()),
            "wheel_file": TARGET_WHEEL_NAME,
            "wheel_sha256": sha256(candidate),
            "wheel_bytes": len(candidate),
            "verification": verification,
            "scope": "package_wheel_only; no bundle, installed matrix, or public clearance",
        }
        output.mkdir(mode=0o700)
        target = output / TARGET_WHEEL_NAME
        shutil.copyfile(wheels[0], target)
        (output / "build-result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        target.chmod(0o444)
        (output / "build-result.json").chmod(0o444)
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path("/usr/bin/python3.12"))
    parser.add_argument("--uv", type=Path, default=Path("/usr/local/bin/uv"))
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output_dir, args.python, args.uv), indent=2))
    except (BuildRefusal, OSError, urllib.error.URLError) as error:
        print(f"build_refused:{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
