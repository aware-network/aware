from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from uuid import UUID

from aware_api.client import AwareApiClient, AwareApiConfig
from aware_api.context import AwareApiContext
from aware_identity.auth.public_key.generator import canonicalize_ed25519_public_key
from aware_identity_ontology.stable_ids import stable_actor_id, stable_identity_id
from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperation,
)
from aware_utils.aware_root import ensure_aware_oig_dir, require_aware_root
from aware_utils.logging import logger


@dataclass(frozen=True, slots=True)
class _RemoteLane:
    branch_id: UUID
    projection_hash: str
    head: dict | None


def _normalize_node_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if not endpoint:
        return endpoint

    # Accept http(s) and convert to ws(s) for the duplex client.
    if endpoint.startswith("http://"):
        endpoint = "ws://" + endpoint[len("http://") :]
    elif endpoint.startswith("https://"):
        endpoint = "wss://" + endpoint[len("https://") :]

    # `AwareApiDuplexClient` appends `/{client_app}/{server_app}` to the configured endpoint.
    # Historically some callers passed an endpoint that already included `/interface/network_node`,
    # which results in a double path like `/interface/network_node/interface/network_node`.
    trimmed = endpoint.rstrip("/")
    for suffix in ("/interface/network_node", "/network_node/network_node"):
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)]
            break
    trimmed = trimmed.rstrip("/")

    # Drop any leftover path/query fragments (operators sometimes paste full URLs).
    try:
        parsed = urlparse(trimmed)
        if parsed.scheme and parsed.netloc:
            trimmed = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    except Exception:
        pass

    return trimmed.rstrip("/")


def _atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _read_text_arg(*, value: str, path: str) -> str:
    raw = (value or "").strip()
    if raw:
        return raw
    file_path = (path or "").strip()
    if not file_path:
        return ""
    return Path(file_path).expanduser().read_text(encoding="utf-8").strip()


def _parse_uuid(value: str, *, field: str) -> UUID:
    try:
        return UUID(value)
    except Exception as exc:
        raise SystemExit(f"Invalid {field}: {value!r}") from exc


def _extract_parent_commit_id(commit_payload: dict) -> UUID | None:
    commit = commit_payload.get("commit")
    if not isinstance(commit, dict):
        return None
    parents = commit.get("commit_parents")
    if not isinstance(parents, list) or not parents:
        return None
    first = parents[0]
    if not isinstance(first, dict):
        return None
    raw = first.get("parent_commit_id")
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return UUID(raw)
    except Exception:
        return None


async def _fetch_lane_index(*, client: AwareApiClient, include_empty: bool) -> list[_RemoteLane]:
    service_op = EnvironmentServiceOperation.parse(
        {
            "service": "replication",
            "op": "list_lane_heads",
            "include_empty": include_empty,
        }
    )
    response = await client.call_service_operation(service_operation=service_op)
    payload = response.service_operation.model_dump(mode="json", exclude_none=True)
    lanes_raw = payload.get("lanes")
    if not isinstance(lanes_raw, list):
        raise RuntimeError("replication.list_lane_heads returned invalid lanes payload")

    lanes: list[_RemoteLane] = []
    for lane in lanes_raw:
        if not isinstance(lane, dict):
            continue
        raw_branch = lane.get("branch_id")
        raw_hash = lane.get("projection_hash")
        if not isinstance(raw_branch, str) or not raw_branch.strip():
            continue
        if not isinstance(raw_hash, str) or not raw_hash.strip():
            continue
        branch_id = _parse_uuid(raw_branch, field="branch_id")
        head = lane.get("head")
        if head is not None and not isinstance(head, dict):
            head = None
        lanes.append(_RemoteLane(branch_id=branch_id, projection_hash=raw_hash, head=head))

    return lanes


async def _fetch_commit_meta(
    *,
    client: AwareApiClient,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
) -> dict | None:
    service_op = EnvironmentServiceOperation.parse(
        {
            "service": "replication",
            "op": "get_commit_meta",
            "branch_id": str(branch_id),
            "projection_hash": projection_hash,
            "commit_id": str(commit_id),
        }
    )
    response = await client.call_service_operation(service_operation=service_op)
    payload = response.service_operation.model_dump(mode="json", exclude_none=True)
    meta = payload.get("meta")
    if meta is None:
        return None
    if not isinstance(meta, dict):
        return None
    return meta


async def _replicate_lane(
    *,
    client: AwareApiClient,
    oig_root: Path,
    lane: _RemoteLane,
    max_commits: int,
    include_meta: bool,
) -> int:
    if not lane.head or not lane.head.get("commit_id"):
        return 0

    lane_dir = oig_root / str(lane.branch_id) / lane.projection_hash
    commits_dir = lane_dir / "commits"
    commits_dir.mkdir(parents=True, exist_ok=True)

    _atomic_write_json(lane_dir / "HEAD.json", lane.head)

    head_commit_id = _parse_uuid(str(lane.head["commit_id"]), field="commit_id")
    cur = head_commit_id
    visited: set[UUID] = set()
    fetched = 0

    while cur is not None and cur not in visited:
        visited.add(cur)
        commit_path = commits_dir / f"{cur}.json"
        meta_path = commits_dir / f"{cur}.meta.json"

        commit_payload: dict
        if commit_path.exists():
            try:
                commit_payload = json.loads(commit_path.read_text(encoding="utf-8"))
            except Exception:
                commit_payload = {}
        else:
            commit_payload = {}

        if not commit_payload:
            response = await client.get_object_instance_graph_commit(
                commit_id=cur,
                branch_id=lane.branch_id,
                projection_hash=lane.projection_hash,
            )
            if (response.status or "").lower() != "succeeded":
                raise RuntimeError(
                    f"GetObjectInstanceGraphCommit failed (branch_id={lane.branch_id} projection_hash={lane.projection_hash} commit_id={cur}): {response.error}"
                )
            payload = response.commit
            if isinstance(payload, str):
                commit_payload = json.loads(payload)
            elif isinstance(payload, dict):
                commit_payload = payload
            else:
                raise RuntimeError(f"Unexpected commit payload type: {type(payload)} (commit_id={cur})")

            _atomic_write_json(commit_path, commit_payload)
            fetched += 1
            if max_commits > 0 and fetched >= max_commits:
                break

        if include_meta and not meta_path.exists():
            meta = await _fetch_commit_meta(
                client=client,
                branch_id=lane.branch_id,
                projection_hash=lane.projection_hash,
                commit_id=cur,
            )
            if meta:
                _atomic_write_json(meta_path, meta)

        parent_id = _extract_parent_commit_id(commit_payload)
        if parent_id is None:
            break
        cur = parent_id

    return fetched


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m aware_network.network.node.replicate",
        description=(
            "Network-owned replication helper:\n"
            "- pull OIG commits from a remote node via NetworkOperation\n"
            "- write them to the local filesystem commit store (AWARE_ROOT/.aware/oig)\n"
            "- optionally rebuild the DB projection index from commits\n"
        ),
    )

    parser.add_argument(
        "--remote-endpoint",
        required=True,
        help=(
            "Remote node base WebSocket endpoint (e.g. wss://node.aware.run). "
            "If you pass a full duplex path like `/interface/network_node`, it will be normalized."
        ),
    )
    parser.add_argument("--public-key", default="", help="Identity public key (ed25519:<hex>).")
    parser.add_argument(
        "--public-key-file",
        default="",
        help="Path to file containing identity public key.",
    )
    parser.add_argument(
        "--private-key",
        default="",
        help="Identity private key material (hex/base64; 32 bytes).",
    )
    parser.add_argument(
        "--private-key-file",
        default="",
        help="Path to file containing identity private key material.",
    )
    parser.add_argument(
        "--identity-type",
        default="human",
        choices=("human", "agent", "organization", "system"),
        help="Identity type used to derive deterministic actor_id (default: human).",
    )

    parser.add_argument(
        "--aware-root",
        default="",
        help="Override AWARE_ROOT for writing the commit store (defaults to env AWARE_ROOT).",
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include lanes without HEAD.json in the replication index.",
    )
    parser.add_argument(
        "--only-branch-id",
        default="",
        help="Only replicate this branch_id (UUID).",
    )
    parser.add_argument(
        "--only-projection-hash",
        default="",
        help="Only replicate this projection_hash.",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=0,
        help="Max commits to fetch per lane (0 = no limit).",
    )
    parser.add_argument(
        "--include-meta",
        action="store_true",
        help="Also sync <commit_id>.meta.json (commit action descriptors) when available.",
    )
    parser.add_argument(
        "--reindex-db",
        action="store_true",
        help="After syncing commits, run `python -m aware_meta_environment_service.reindex_db` to rebuild DB projections.",
    )
    parser.add_argument(
        "--reindex-dry-run",
        action="store_true",
        help="Validate commit hashes without writing to the DB (passed to reindex_db).",
    )
    parser.add_argument(
        "--reindex-skip-commit-actions",
        action="store_true",
        help="Skip rebuilding commit action metadata rows (passed to reindex_db).",
    )

    return parser.parse_args(argv)


async def _main_async(args: argparse.Namespace) -> int:
    if args.aware_root.strip():
        aware_root_dir = Path(args.aware_root.strip()).expanduser()
        aware_root_dir.mkdir(parents=True, exist_ok=True)
        os.environ["AWARE_ROOT"] = str(aware_root_dir.resolve())

    aware_root = require_aware_root(purpose="replicate")
    oig_root = ensure_aware_oig_dir(aware_root=aware_root, require_writable=True)

    public_key = _read_text_arg(value=args.public_key, path=args.public_key_file)
    private_key = _read_text_arg(value=args.private_key, path=args.private_key_file)
    if not public_key or not private_key:
        raise SystemExit("Both --public-key/--public-key-file and --private-key/--private-key-file are required.")

    canonical_pub, public_key_bytes = canonicalize_ed25519_public_key(public_key)
    identity_id = stable_identity_id(public_key=f"ed25519:{public_key_bytes.hex()}", type=args.identity_type)
    actor_id = stable_actor_id(identity_id=identity_id)
    logger.info(
        "Replication identity resolved (identity_id=%s actor_id=%s)",
        identity_id,
        actor_id,
    )

    remote_endpoint = _normalize_node_endpoint(args.remote_endpoint)
    if not remote_endpoint:
        raise SystemExit("--remote-endpoint resolved to an empty value after normalization")

    client = AwareApiClient(
        AwareApiConfig(
            endpoint=remote_endpoint,
            actor_id=actor_id,
            request_timeout=float(os.environ.get("AWARE_REPLICATION_REQUEST_TIMEOUT_S", "30.0")),
            context=None,
        )
    )
    try:
        await client.authenticate_identity_session(public_key=canonical_pub, private_key=private_key)

        boot = await client.get_boot_environment_descriptor()
        if (boot.status or "").lower() not in {"succeeded", "ready", "running"}:
            raise RuntimeError(f"Remote boot environment is not ready: status={boot.status} error={boot.error}")
        if boot.descriptor is None:
            raise RuntimeError(f"Remote boot environment descriptor missing: status={boot.status} error={boot.error}")

        desc = boot.descriptor
        if desc.process_id is None or desc.thread_id is None:
            raise RuntimeError(
                "Remote boot environment missing process/thread ids "
                f"(environment_id={desc.boot_environment_id} process_id={desc.process_id} thread_id={desc.thread_id})"
            )

        client.set_context(
            AwareApiContext(
                environment_id=desc.boot_environment_id,
                process_id=desc.process_id,
                thread_id=desc.thread_id,
                branch_id=desc.branch_id,
                projection_hash=None,
            )
        )

        lanes = await _fetch_lane_index(client=client, include_empty=args.include_empty)
        if args.only_branch_id.strip():
            only_branch = _parse_uuid(args.only_branch_id.strip(), field="only_branch_id")
            lanes = [l for l in lanes if l.branch_id == only_branch]
        if args.only_projection_hash.strip():
            only_hash = args.only_projection_hash.strip()
            lanes = [l for l in lanes if l.projection_hash == only_hash]

        total_commits = 0
        for lane in lanes:
            fetched = await _replicate_lane(
                client=client,
                oig_root=oig_root,
                lane=lane,
                max_commits=args.max_commits,
                include_meta=args.include_meta,
            )
            total_commits += fetched
            if fetched:
                logger.info(
                    "Replicated lane (branch_id=%s projection_hash=%s commits=%s)",
                    lane.branch_id,
                    lane.projection_hash,
                    fetched,
                )

        logger.info(
            "Replication complete (lanes=%s commits_fetched=%s oig_root=%s)",
            len(lanes),
            total_commits,
            oig_root,
        )

    finally:
        await client.close()

    if args.reindex_db:
        cmd = [sys.executable, "-m", "aware_meta_environment_service.reindex_db"]
        if args.only_branch_id.strip():
            cmd += ["--only-branch-id", args.only_branch_id.strip()]
        if args.only_projection_hash.strip():
            cmd += ["--only-projection-hash", args.only_projection_hash.strip()]
        if args.reindex_dry_run:
            cmd.append("--dry-run")
        if args.reindex_skip_commit_actions:
            cmd.append("--skip-commit-actions")
        logger.info("Running DB reindex: %s", " ".join(cmd))
        subprocess.run(cmd, check=True)

    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
