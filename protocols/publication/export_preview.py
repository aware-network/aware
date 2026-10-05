#!/usr/bin/env python3
"""Issue-owned, hash-pinned exporter for the public consumer overlay."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from source_layout import current_path

BASE = "592fca9473b1e72b130c0d84a452de7523fa93bb"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelope", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("preview_install", root / "protocols/install.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = args.envelope.read_bytes()
    _, envelope = module.verified_archive(data, module.ENVELOPE_SHA256)
    _, source = module.verified_archive(
        envelope["sources/aware-goal-fs-source-capsule-v2.tar.gz"], module.SOURCE_SHA256)
    module.verified_archive(envelope["payload/aware-goal-native-fs-v2-linux_x86_64-py312.tar.gz"],
                            module.PAYLOAD_SHA256)
    outputs = {"protocols/distributions/" + module.ARCHIVE: data}
    outputs.update({current_path("protocols/source/" + name): content for name, content in source.items()})
    outputs["README.md"] = (root / "protocols/publication/README.md.in").read_bytes()
    for name, content in sorted(outputs.items()):
        path = root / name
        if path.is_symlink():
            raise ValueError("symlink_output_not_supported")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    receipt = {
        "format": "aware.protocols.git-publication.v2",
        "public_preview": "goal-fs-readonly-preview-2026-10-05",
        "target_repository": "https://github.com/aware-network/aware",
        "base_git_revision": BASE,
        "aware_source_revision": "3bea9cc913644700be810398293bca899020c299",
        "envelope_sha256": module.ENVELOPE_SHA256,
        "payload_sha256": module.PAYLOAD_SHA256,
        "source_capsule_sha256": module.SOURCE_SHA256,
        "authority_mode": "filesystem",
        "publication_kind": "Consumer protocols and allowlisted neutral workspace source; not a WorkspaceRevision or internal repository export",
        "generator": "protocols/publication/export_preview.py",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "license": "Apache-2.0 for Aware-authored content; upstream terms retained",
        "outputs": {name: {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
                    for name, content in sorted(outputs.items())},
    }
    (root / "protocols/publication/receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"generated_files": len(outputs), "envelope_sha256": module.ENVELOPE_SHA256}))


if __name__ == "__main__":
    main()
