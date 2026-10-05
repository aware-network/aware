"""Exact-source relocation and byte inventory; never exports an internal workspace."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "protocols/publication/source-layout.json"


def configuration():
    return json.loads(CONFIG.read_bytes())


def relative(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or ".." in path.parts:
        raise ValueError("layout_path_invalid:" + value)
    return value


def current_path(previous: str) -> str:
    matches = [m["path"] for m in configuration()["moves"] if m["previous_path"] == previous]
    if len(matches) != 1:
        raise ValueError("source_coordinate_not_admitted:" + previous)
    return relative(matches[0])


def agent_project(name: str, root: Path = ROOT) -> Path:
    return root / relative(configuration()["agent_projects"][name.replace("-", "_")])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relocate", action="store_true", help="One-time byte-preserving move; refuses existing destinations.")
    parser.add_argument("--retain-builder", action="store_true", help="Retain the exact accepted a3 producer as historical build evidence.")
    parser.add_argument("--record", action="store_true", help="Record baseline and current hashes after an Issue-scoped layout change.")
    args = parser.parse_args()
    config = configuration()
    baseline = config["baseline_revision"]
    checked = []
    for item in config["moves"]:
        old, new = relative(item["previous_path"]), relative(item["path"])
        before = subprocess.check_output(["git", "show", baseline + ":" + old], cwd=ROOT)
        checked.append((item, before))
        if args.relocate:
            source, destination = ROOT / old, ROOT / new
            if source.is_symlink() or not source.is_file() or source.read_bytes() != before:
                raise ValueError("relocation_source_changed:" + old)
            if destination.exists() or destination.is_symlink():
                raise ValueError("relocation_destination_exists:" + new)
    if args.relocate:
        for item, _ in checked:
            destination = ROOT / item["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            (ROOT / item["previous_path"]).rename(destination)
    if args.retain_builder:
        destination = ROOT / "protocols/publication/builders/agent-0.1.0a3.py"
        data = subprocess.check_output(["git", "show", baseline + ":protocols/agent/build_bundle.py"], cwd=ROOT)
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError("historical_builder_changed")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    if args.record:
        for item, before in checked:
            path = ROOT / item["path"]
            if path.is_symlink() or not path.is_file():
                raise ValueError("layout_regular_file_required:" + item["path"])
            data = path.read_bytes()
            item.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                        previous_sha256=hashlib.sha256(before).hexdigest(),
                        byte_identical=data == before)
        for item in config.get("additions", []):
            path = ROOT / relative(item["path"])
            if path.is_symlink() or not path.is_file():
                raise ValueError("layout_regular_file_required:" + item["path"])
            data = path.read_bytes()
            item.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        CONFIG.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"files": len(checked), "relocated": args.relocate, "recorded": args.record}))


if __name__ == "__main__":
    main()
