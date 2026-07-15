from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from aware_node_operator.kernel_ops.seed_program_apply import apply_kernel_seed_program


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply a kernel seed expressed as a `.aware program` to the BOOT environment (commit-only)."
    )
    parser.add_argument(
        "--program", required=True, help="Path to a kernel seed .aware program file"
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Override node WS endpoint (otherwise uses AWARE_NODE_WS_URL/AWARE_NODE_BASE_URL)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Explicit repository/workspace root for aware.programs.toml registry "
            "loading (otherwise uses AWARE_NODE_OPERATOR_REPO_ROOT, "
            "AWARE_NODE_REPO_ROOT, AWARE_REPO_ROOT, AWARE_REPOSITORY_ROOT, or the "
            "program's semantic manifest anchor)"
        ),
    )
    parser.add_argument(
        "--profile",
        default=None,
        help=(
            "Optional kernel seed profile TOML path (defaults to "
            "<program>.profile.toml or AWARE_KERNEL_SEED_PROFILE)"
        ),
    )
    parser.add_argument(
        "--no-economy", action="store_true", help="Skip Economy catalog seeding"
    )
    args = parser.parse_args(argv)

    program_path = Path(args.program).expanduser().resolve()

    asyncio.run(
        apply_kernel_seed_program(
            program_path=str(program_path),
            repo_root=args.repo_root,
            profile_path=args.profile,
            endpoint=args.endpoint,
            include_economy=not args.no_economy,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
