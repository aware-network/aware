from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse


PROOF_TESTS = (
    "tests/runtime/test_ocg_sql_migrations_postgres.py",
    "tests/runtime/test_postgres_runtime_ci_proof.py",
    "tests/runtime/test_service_query_conformance.py::test_service_query_conformance_postgres",
)


def _redact_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if not parsed.scheme:
        return "***"
    netloc = parsed.netloc
    if "@" in netloc:
        credentials, host = netloc.rsplit("@", 1)
        if ":" in credentials:
            user, _password = credentials.split(":", 1)
            netloc = f"{user}:***@{host}"
        else:
            netloc = f"***@{host}"
    return urlunparse(parsed._replace(netloc=netloc))


def _tail(text: str, *, limit: int = 6000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


async def _postgres_environment_receipt(admin_url: str) -> dict[str, Any]:
    import asyncpg  # type: ignore

    conn = await asyncpg.connect(admin_url)
    try:
        row = await conn.fetchrow(
            """
SELECT
  current_database() AS database,
  current_user AS user_name,
  inet_server_addr()::text AS server_addr,
  inet_server_port() AS server_port,
  version() AS version;
""".strip()
        )
    finally:
        await conn.close()

    assert row is not None
    return {
        "admin_url": _redact_url(admin_url),
        "database": str(row["database"]),
        "user": str(row["user_name"]),
        "server_addr": str(row["server_addr"]),
        "server_port": int(row["server_port"]),
        "version": str(row["version"]).splitlines()[0],
    }


def _run_pytest(*, package_root: Path, env: dict[str, str]) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", "-q", *PROOF_TESTS]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=package_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "cwd": str(package_root),
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the aware-orm Postgres migration/runtime proof and emit a JSON receipt."
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=None,
        help="Optional path to write the JSON proof receipt.",
    )
    parser.add_argument(
        "--admin-url",
        default=None,
        help="Postgres admin URL. Defaults to AWARE_DB_TEST_ADMIN_URL or AWARE_DB_TEST_URL.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    package_root = Path(__file__).resolve().parents[1]
    admin_url = args.admin_url or os.getenv("AWARE_DB_TEST_ADMIN_URL") or os.getenv("AWARE_DB_TEST_URL")

    receipt: dict[str, Any] = {
        "proof": "aware-orm-postgres-ci-container-proof-v0",
        "package_root": str(package_root),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "tests": list(PROOF_TESTS),
        "postgres": None,
        "pytest": None,
        "status": "failed",
    }

    if not admin_url:
        receipt["error"] = "AWARE_DB_TEST_ADMIN_URL or AWARE_DB_TEST_URL is required."
        _emit_receipt(receipt, args.receipt_path)
        return 2

    env = os.environ.copy()
    env["AWARE_DB_TEST_ADMIN_URL"] = admin_url

    try:
        receipt["postgres"] = asyncio.run(_postgres_environment_receipt(admin_url))
        receipt["pytest"] = _run_pytest(package_root=package_root, env=env)
    except Exception as exc:
        receipt["error"] = str(exc)
        _emit_receipt(receipt, args.receipt_path)
        return 1

    if receipt["pytest"]["returncode"] == 0:
        receipt["status"] = "passed"
        _emit_receipt(receipt, args.receipt_path)
        return 0

    receipt["error"] = "pytest proof failed"
    _emit_receipt(receipt, args.receipt_path)
    return int(receipt["pytest"]["returncode"])


def _emit_receipt(receipt: dict[str, Any], receipt_path: Path | None) -> None:
    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if receipt_path is not None:
        resolved = receipt_path.resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    raise SystemExit(main())
