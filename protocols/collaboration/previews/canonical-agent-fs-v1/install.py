"""Verify the versioned admit successor and use its existing offline installer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import types
from pathlib import Path

PACKET_SHA = "49fd470e4aadf564ec40131f1bffbe95d0f8d65cf0946e60db07dfd88c09531d"
PAYLOAD_SHA = "db23274dcc05c3923c9f7ba33f6bf0d1cbda3717aa120d44ee74ef4d35297b11"
VERIFIER_SHA = "032febe109cf145c65f5edaf14403fc58e7b4e93397535d0327e5ce1a65c6ca9"
ARCHIVE = "canonical-agent-source-notice-review-v1.tar.gz"


def new_target(target: Path) -> None:
    if target.exists() or target.is_symlink():
        raise ValueError("installation_target_must_be_new")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise ValueError("existing_regular_parent_required")


def load_verifier(root: Path) -> types.ModuleType:
    # Public placement is protocols/collaboration/previews/canonical-agent-fs-v1/.
    path = root.parents[2] / "install.py"
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular_verifier_required")
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != VERIFIER_SHA:
        raise ValueError("verifier_digest_changed")
    module = types.ModuleType("accepted_preview_archive_verifier")
    exec(compile(body, str(path), "exec"), module.__dict__)  # noqa: S102 -- pinned verifier only
    return module


def clean_environment(interpreter: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR"}
    }
    environment.update(
        PYTHON_BIN=str(interpreter),
        PIP_NO_INDEX="1",
        PIP_NO_CACHE_DIR="1",
        PIP_CONFIG_FILE=os.devnull,
        PYTHONDONTWRITEBYTECODE="1",
    )
    return environment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-executable", type=Path, required=True)
    parser.add_argument("--venv", type=Path, required=True)
    args = parser.parse_args()
    interpreter = args.python_executable.expanduser().resolve(strict=True)
    version = subprocess.check_output(
        [
            str(interpreter),
            "-I",
            "-c",
            "import sys; print('.'.join(map(str,sys.version_info[:2])))",
        ],
        text=True,
    ).strip()
    if version != "3.12":
        raise ValueError("python_minor_mismatch:3.12:" + version)
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise ValueError("linux_x86_64_required")
    target = args.venv.expanduser().absolute()
    new_target(target)
    root = Path(__file__).resolve().parent
    verifier = load_verifier(root)
    archive = root / "distribution" / ARCHIVE
    if archive.is_symlink() or not archive.is_file():
        raise ValueError("regular_packet_required")
    packet_root, outer = verifier.verified_archive(archive.read_bytes(), PACKET_SHA)
    inner_root, inner = verifier.verified_archive(
        outer["payload/aware-canonical-neutral-fs-internal-v1.tar.gz"], PAYLOAD_SHA
    )
    retained = Path(tempfile.mkdtemp(prefix="aware-specification-install-"))
    for prefix, files in ((packet_root, outer), ("installation/" + inner_root, inner)):
        for name, body in files.items():
            destination = retained / prefix / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)
    inner_directory = retained / "installation" / inner_root
    environment = clean_environment(interpreter)
    try:
        new_target(target)
        subprocess.run(
            ["/bin/sh", str(inner_directory / "install.sh"), str(target)],
            env=environment,
            check=True,
        )
        subprocess.run(
            [str(target / "bin/python"), "-I", "-m", "pip", "check"],
            env=environment,
            check=True,
        )
    except (OSError, ValueError, subprocess.CalledProcessError):
        print(
            json.dumps(
                {
                    "status": "installation_failed",
                    "retained_evidence": str(retained),
                    "venv": str(target),
                }
            ),
            file=sys.stderr,
        )
        raise
    print(
        json.dumps(
            {
                "status": "installed",
                "packet_sha256": PACKET_SHA,
                "payload_sha256": PAYLOAD_SHA,
                "venv": str(target),
                "retained_source_and_notices": str(retained / packet_root),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
