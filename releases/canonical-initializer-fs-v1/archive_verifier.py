#!/usr/bin/env python3
"""Acquire the pinned local preview, then delegate to its offline installer."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tarfile
import tempfile

ENVELOPE_SHA256 = "10b126383498b4e4561109f5eb8059161b2c03546d19065b85506f4c41a29c21"
PAYLOAD_SHA256 = "02dfda3a5ad1c3d85fd4c317dc392a867d24cc852001fa75394f90d1245456f1"
SOURCE_SHA256 = "9abe97d23565e86954b092cf361ab6cf651fef11605789bb5794d49d9a9408c7"
ARCHIVE = "aware-goal-fs-preview-linux_x86_64-py312.tar.gz"


def verified_archive(data: bytes, expected: str) -> tuple[str, dict[str, bytes]]:
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("archive_digest_mismatch")
    files: dict[str, bytes] = {}
    roots: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError("unsafe_archive_path")
            if member.isdir():
                continue
            if not member.isfile() or member.name in files:
                raise ValueError("unsupported_or_duplicate_archive_member")
            roots.add(path.parts[0])
            stream = archive.extractfile(member)
            assert stream is not None
            files[member.name] = stream.read()
    if len(roots) != 1:
        raise ValueError("archive_requires_single_root")
    root = next(iter(roots))
    relative = {name.removeprefix(root + "/"): content for name, content in files.items()}
    checked: set[str] = set()
    for line in relative["SHA256SUMS"].decode().splitlines():
        digest, name = line.split("  ", 1)
        if name in checked or name not in relative:
            raise ValueError("invalid_checksum_member")
        if hashlib.sha256(relative[name]).hexdigest() != digest:
            raise ValueError("member_digest_mismatch")
        checked.add(name)
    if checked != set(relative) - {"SHA256SUMS"}:
        raise ValueError("incomplete_checksum_coverage")
    return root, relative


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-executable", type=Path, required=True)
    parser.add_argument("--venv", type=Path, required=True)
    args = parser.parse_args()
    interpreter = args.python_executable.expanduser().resolve(strict=True)
    version = subprocess.check_output(
        [str(interpreter), "-I", "-c", "import sys; print('.'.join(map(str,sys.version_info[:2])))"],
        text=True,
    ).strip()
    if version != "3.12":
        raise ValueError("python_minor_mismatch:3.12:" + version)
    if sys.platform != "linux" or platform.machine() not in {"x86_64", "AMD64"}:
        raise ValueError("unsupported_platform:linux_x86_64_required")
    target = args.venv.expanduser().absolute()
    if target.exists() or target.is_symlink():
        raise ValueError("installation_target_must_be_new")
    archive_path = Path(__file__).resolve().parent / "distributions" / ARCHIVE
    outer_root, outer = verified_archive(archive_path.read_bytes(), ENVELOPE_SHA256)
    payload_name = "payload/aware-goal-native-fs-v2-linux_x86_64-py312.tar.gz"
    inner_root, inner = verified_archive(outer[payload_name], PAYLOAD_SHA256)
    verified_archive(outer["sources/aware-goal-fs-source-capsule-v2.tar.gz"], SOURCE_SHA256)
    retained = Path(tempfile.mkdtemp(prefix="aware-goal-preview-install-"))
    for name, content in outer.items():
        path = retained / outer_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    inner_directory = retained / "installation" / inner_root
    for name, content in inner.items():
        path = inner_directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    environment = {key: value for key, value in os.environ.items()
                   if key in {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR"}}
    environment.update(PYTHON_BIN=str(interpreter), PIP_NO_INDEX="1",
                       PIP_NO_CACHE_DIR="1", PIP_CONFIG_FILE=os.devnull)
    subprocess.run(["/bin/sh", str(inner_directory / "install.sh"), str(target)],
                   env=environment, check=True)
    subprocess.run([str(target / "bin/python"), "-m", "pip", "check"],
                   env=environment, check=True)
    print(json.dumps({"status": "installed", "archive_sha256": ENVELOPE_SHA256,
                      "payload_sha256": PAYLOAD_SHA256, "venv": str(target),
                      "retained_source_and_notices": str(retained / outer_root)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
