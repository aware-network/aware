#!/usr/bin/env python3
"""Install the exact neutral agent bundle into a new offline environment."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-executable", type=Path, required=True)
    parser.add_argument("--venv", type=Path, required=True)
    args = parser.parse_args()
    interpreter = args.python_executable.resolve(strict=True)
    actual = subprocess.check_output([str(interpreter), "-I", "-c", "import sys; print('.'.join(map(str,sys.version_info[:2])))"], text=True).strip()
    if actual != "3.12":
        raise ValueError("python_minor_mismatch:3.12:" + actual)
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise ValueError("linux_x86_64_required")
    target = args.venv.expanduser().absolute()
    if target.exists() or target.is_symlink():
        raise ValueError("installation_target_must_be_new")
    root = Path(__file__).resolve().parent
    release = json.loads((root / "release.json").read_text())
    spec = importlib.util.spec_from_file_location("verified_preview", root.parent / "install.py")
    assert spec and spec.loader
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    name, files = verifier.verified_archive((root / release["archive"]).read_bytes(), release["archive_sha256"])
    retained = Path(tempfile.mkdtemp(prefix="aware-agent-install-")) / name
    for relative, data in files.items():
        destination = retained / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    environment = {key: value for key, value in os.environ.items() if key in {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR"}}
    environment.update(PIP_NO_INDEX="1", PIP_NO_CACHE_DIR="1", PIP_CONFIG_FILE=os.devnull)
    subprocess.run([str(interpreter), "-I", "-m", "venv", str(target)], env=environment, check=True)
    subprocess.run([str(target / "bin/python"), "-I", "-m", "pip", "install", "--no-index", "--find-links", str(retained / "wheelhouse"), release["root_requirement"]], env=environment, check=True)
    subprocess.run([str(target / "bin/python"), "-I", "-m", "pip", "check"], env=environment, check=True)
    subprocess.run([str(target / "bin/aware"), "--version"], env=environment, check=True)
    print(json.dumps({"outcome": "installed", "archive_sha256": release["archive_sha256"],
                      "payload_packages": len(release["wheels"]), "venv": str(target),
                      "retained_source_and_notices": str(retained)}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
