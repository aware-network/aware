"""Retire only pinned legacy public snapshot outputs, with recoverable preimages."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

BASE = "592fca9473b1e72b130c0d84a452de7523fa93bb"
LEGACY = ["workspaces", "aware.repo.toml", ".aware/repository/revision-filesystem.manifest.json", ".aware/workspace/public-git-mirror.manifest.json",
          "docs/legal", "docs/goals/PROTOCOL.md", "docs/specs/PROTOCOL.md", "protocols/publication/infrastructure-readme.md"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    remote = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=root, text=True).strip()
    if remote not in {"https://github.com/aware-network/aware", "https://github.com/aware-network/aware.git"}:
        raise ValueError("expected_public_repository_required")
    listing = subprocess.check_output(["git", "ls-tree", "-r", "-z", BASE, "--", *LEGACY], cwd=root)
    rows = []
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        header, name = entry.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        relative = name.decode()
        path = root / relative
        if mode not in {"100644", "100755"} or kind != "blob" or not path.is_file() or path.is_symlink():
            raise ValueError("regular_legacy_preimage_required:" + relative)
        data = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if actual != oid:
            raise ValueError("legacy_preimage_changed:" + relative)
        rows.append({"path": relative, "git_blob": oid, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    document = {"format": "aware.protocols-only-retirement.v1", "baseline_revision": BASE,
                "preservation": "Removed from current tree only; Git history unchanged and exact preimages quarantined locally.", "files": rows}
    if args.apply:
        quarantine = Path(tempfile.mkdtemp(prefix="aware-public-legacy-preimages-"))
        for row in rows:
            source = root / row["path"]
            target = quarantine / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
        # Empty legacy directories only. Never recursively delete a repository/workspace root.
        for name in ("workspaces", "docs/legal", "docs/goals", "docs/specs", ".aware/repository", ".aware/workspace"):
            directory = root / name
            if directory.is_dir():
                for child in sorted(directory.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                    if child.is_dir() and not child.is_symlink():
                        child.rmdir()
                directory.rmdir()
        inventory_bytes = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
        (quarantine / "retirement-inventory.json").write_bytes(inventory_bytes)
        public_record = {"format": document["format"], "baseline_revision": BASE,
                         "preservation": document["preservation"], "retired_roots": LEGACY,
                         "retired_files": len(rows), "retired_bytes": sum(r["bytes"] for r in rows),
                         "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
                         "verification": "Exact deleted paths and preimages are independently recoverable from this pinned baseline and the publication diff. No history rewrite."}
        (root / "protocols/publication/protocols-only-retirement.json").write_text(json.dumps(public_record, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"retired_files": len(rows), "quarantined_bytes": sum(r["bytes"] for r in rows), "recoverable_preimages": str(quarantine)}))
    else:
        print(json.dumps({"retired_files": len(rows), "bytes": sum(r["bytes"] for r in rows), "mode": "validated_plan"}))


if __name__ == "__main__":
    main()
