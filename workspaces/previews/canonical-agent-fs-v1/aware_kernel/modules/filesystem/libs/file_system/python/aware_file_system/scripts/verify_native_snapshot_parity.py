from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from aware_file_system.native_snapshot import run_workspace_snapshot_parity


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify exact Python/Rust FileSystem snapshot parity."
    )
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--cargo-path", type=Path)
    parser.add_argument("--manifest-path", type=Path)
    parser.add_argument("--target-dir", type=Path)
    parser.add_argument("--receipt-path", type=Path)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)

    receipt = run_workspace_snapshot_parity(
        args.workspace_root,
        cargo_path=args.cargo_path,
        manifest_path=args.manifest_path,
        target_dir=args.target_dir,
    )
    if args.receipt_path is not None:
        receipt_path = args.receipt_path.expanduser().resolve()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt["receipt_path"] = receipt_path.as_posix()
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            receipt,
            indent=None if args.compact else 2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
