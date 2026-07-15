from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from aware_node_operator.kernel_ops.seed_apply import apply_kernel_seed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply the deterministic Aware kernel seed to the BOOT environment (commit-only)."
    )
    parser.add_argument("--spec", required=True, help="Path to a kernel seed TOML spec")
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Override node WS endpoint (otherwise uses AWARE_NODE_WS_URL/AWARE_NODE_BASE_URL)",
    )
    parser.add_argument(
        "--no-economy", action="store_true", help="Skip Economy catalog seeding"
    )
    args = parser.parse_args(argv)

    spec_path = Path(args.spec).expanduser().resolve()

    asyncio.run(
        apply_kernel_seed(
            spec_path=str(spec_path),
            endpoint=args.endpoint,
            include_economy=not args.no_economy,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
