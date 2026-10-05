"""Versioned bootstrap preparation; domain authority remains in the existing owners."""
from __future__ import annotations

import argparse
import hashlib
import html
from importlib.resources import files
import json
from pathlib import Path
import shlex
import subprocess
import sys

from aware_protocol_fs_adapter import admit_protocol_manifest, resolve_repository_path_at_use
from aware_repository_sdk import RepositoryPrepareRequest, RepositorySdkOperationClient
from aware_repository_fs_adapter import FilesystemRepositoryPrepareProvider

START = "<!-- aware-agent-contract:start -->"
END = "<!-- aware-agent-contract:end -->"


def template_inputs():
    root = files("aware_agent_cli").joinpath("templates/agent-fs-v1")
    metadata = json.loads(root.joinpath("contract.json").read_bytes())
    documents = {target: root.joinpath(source).read_bytes() for target, source in metadata["files"].items()}
    return metadata, documents


def render_document(data: bytes, command: str, docs_prefix: str = "docs") -> bytes:
    text = data.decode("utf-8")
    text = text.replace("{{AWARE_COMMAND_MARKDOWN}}", "<code>" + html.escape(command) + "</code>")
    text = text.replace("{{AWARE_COMMAND_SHELL}}", shlex.quote(command)).replace("{{DOCS_PREFIX}}", docs_prefix)
    if "{{" in text:
        raise ValueError("unresolved_contract_template")
    return text.encode("utf-8")


def command_path() -> str:
    return str(Path(sys.argv[0]).resolve(strict=True))


def observe_contract(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="aware contract", description="Observe the installed template, not actor authority.")
    parser.parse_args(arguments)
    metadata, documents = template_inputs()
    print(json.dumps({**metadata, "command": command_path(), "template_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in documents.items()},
                      "actor_authentication": "unavailable", "goal_writers": "unavailable"}, sort_keys=True))
    return 0


def initialize(arguments: list[str], *, manifest: str) -> int:
    parser = argparse.ArgumentParser(prog="aware init", description="Install missing versioned agent bootstrap/docs without overwriting customer files.")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--create-repository", action="store_true", help="Explicitly prepare an empty new Git root; no commit, author configuration, remote or push.")
    parser.add_argument("--link-existing-agents", action="store_true", help="Explicitly append a managed contract link to an existing regular AGENTS.md; preserve its original bytes.")
    args = parser.parse_args(arguments)
    prepared = RepositorySdkOperationClient(provider=FilesystemRepositoryPrepareProvider()).prepare_repository(
        RepositoryPrepareRequest(str(args.repository_root), create_if_missing=args.create_repository))
    if prepared.outcome == "refused":
        print(json.dumps(prepared.to_wire(), sort_keys=True), file=sys.stderr)
        return 2
    root = Path(prepared.repository_root).resolve(strict=True)
    metadata, documents = template_inputs()
    command = command_path()
    writes = {"aware.protocol.toml": manifest.encode(),
              ".aware/agent-protocol.md": render_document(documents["AGENTS.md"], command, "../docs")}
    preserved = []
    linked = None

    def checked(name: str) -> Path:
        result = resolve_repository_path_at_use(repository_root=root, relative_path=name, field_name="bootstrap." + name)
        if result.path is None:
            raise ValueError("bootstrap_target_unresolvable:" + ",".join(result.diagnostics))
        path = root / name
        if path.is_symlink():
            raise ValueError("bootstrap_symlink_target_refused:" + name)
        return path

    for name in [*writes, ".aware/agent-bootstrap.json"]:
        if checked(name).exists():
            raise ValueError("bootstrap_target_exists:" + name)
    for name, data in documents.items():
        path = checked(name)
        if path.exists():
            if not path.is_file():
                raise ValueError("bootstrap_regular_file_required:" + name)
            preserved.append(name)
            if name == "AGENTS.md" and args.link_existing_agents:
                original = path.read_bytes()
                if START.encode() in original or END.encode() in original:
                    raise ValueError("existing_managed_contract_requires_reviewed_upgrade")
                linked = (original, original + b"\n\n" + (START + "\nAware filesystem contract `" + metadata["contract_ref"] + "` " + metadata["version"] + ":\nread [.aware/agent-protocol.md](.aware/agent-protocol.md) before agent work.\nResolve conflicts with existing customer instructions explicitly; this link does not grant work authority.\n" + END + "\n").encode())
        else:
            writes[name] = render_document(data, command)
    rendered = {name: hashlib.sha256(data).hexdigest() for name, data in writes.items()}
    provenance = {"contract_ref": metadata["contract_ref"], "version": metadata["version"], "command": command,
                  "template_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in documents.items()},
                  "rendered_sha256": rendered, "preserved": preserved, "linked_existing_agents": linked is not None,
                  "qualification": "Setup provenance, not actor authority or permanent file currentness. No silent upgrade."}
    writes[".aware/agent-bootstrap.json"] = (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode()
    for name, data in writes.items():
        path = checked(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        checked(name)
        with path.open("xb") as stream:
            stream.write(data)
    if linked is not None:
        path = checked("AGENTS.md")
        if path.read_bytes() != linked[0]:
            raise ValueError("existing_agents_changed_during_setup")
        with path.open("ab") as stream:
            stream.write(linked[1][len(linked[0]):])
    admitted = admit_protocol_manifest(repository_root=root, manifest_path=root / "aware.protocol.toml")
    if admitted.filesystem_profile is None:
        raise ValueError("bootstrap_admission_refused:" + ",".join(admitted.diagnostics))
    print(json.dumps({"outcome": "initialized", "profile": metadata["collaboration_profile"], "contract_ref": metadata["contract_ref"],
                      "contract_version": metadata["version"], "created": list(writes), "preserved": preserved,
                      "linked_existing_agents": linked is not None, "manual_integration_required": bool([p for p in preserved if p != "AGENTS.md"] or ("AGENTS.md" in preserved and linked is None)),
                      "repository_preparation": prepared.to_wire(), "authority_mode": "filesystem", "goal_capability": "unavailable", "atomic": False}, sort_keys=True))
    return 0


def prepare_repository(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="aware repository create", description="Prepare an empty repository through the same neutral SDK used by init; does not install the scaffold or publish.")
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(arguments)
    result = RepositorySdkOperationClient(provider=FilesystemRepositoryPrepareProvider()).prepare_repository(
        RepositoryPrepareRequest(args.repository_root, create_if_missing=True, dry_run=args.dry_run))
    print(json.dumps(result.to_wire(), sort_keys=True))
    return 2 if result.outcome == "refused" else 0
