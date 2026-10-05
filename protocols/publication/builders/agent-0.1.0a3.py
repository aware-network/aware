"""Build a consumer projection of existing owners; never copy/rewrite domain decisions."""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import tomllib
import urllib.request
import zipfile

PIN = "728831f6636a611a8baac61dbc258ed563a0e466"
BASE = "workspaces/aware_coordination/modules/workflow/"
PACKAGES = {
    "aware-issue-runtime": (BASE + "libs/issue_runtime", "aware_issue_runtime", "0.2.0a1",
        ["__init__.py", "contracts.py", "parser.py", "source_import.py", "development.py", "first_person_activity.py", "pulse.py", "py.typed"],
        ["aware-issue-operational-runtime==0.2.0+oss.1"]),
    "aware-issue-operational-runtime": (BASE + "libs/issue_operational_runtime", "aware_issue_operational_runtime", "0.2.0+oss.1", None, []),
    "aware-issue-sdk": (BASE + "sdks/issue/python", "aware_issue_sdk", "0.7.0a1",
        ["__init__.py", "operation.py", "local_files.py", "py.typed"],
        ["aware-issue-runtime==0.2.0a1", "pydantic==2.13.5"]),
    "aware-workspace-operator": ("workspaces/aware_workspace/modules/workspace/libs/workspace_operator/python", "aware_workspace_operator", "0.4.0a1",
        ["__init__.py", "commit.py", "models.py", "py.typed"], ["pydantic==2.13.5"]),
    "aware-issue-fs-adapter": (BASE + "sdks/issue/filesystem_adapter/python", "aware_issue_fs_adapter", "0.6.0a1", None,
        ["aware-issue-sdk==0.7.0a1", "aware-issue-runtime==0.2.0a1", "aware-issue-operational-runtime==0.2.0+oss.1", "aware-workspace-operator==0.4.0a1", "aware-protocol-fs-adapter==0.2.0"]),
    "aware-issue-cli": (BASE + "sdks/issue/cli/python", "aware_issue_cli", "0.6.0a1", None,
        ["aware-issue-sdk==0.7.0a1", "aware-issue-fs-adapter==0.6.0a1"]),
}
REGISTRY = {"pydantic": "2.13.5", "pydantic_core": "2.46.5", "annotated_types": "0.8.0", "typing_inspection": "0.4.4"}
PREPARATION_PACKAGES = ["aware-repository-sdk", "aware-repository-fs-adapter"]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source(repo: Path, relative: str) -> bytes:
    tree = subprocess.check_output(["git", "ls-tree", PIN, "--", relative], cwd=repo, text=True)
    if not tree.startswith(("100644 blob ", "100755 blob ")):
        raise ValueError("committed_regular_source_required:" + relative)
    return subprocess.check_output(["git", "show", PIN + ":" + relative], cwd=repo)


def curate_init(raw: bytes, module: str) -> bytes:
    tree = ast.parse(raw)
    if module == "aware_issue_runtime":
        excluded = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_PARTICIPANT_EXPORTS" for t in node.targets):
                excluded = ast.literal_eval(node.value)
        result = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "__getattr__":
                continue
            if isinstance(node, ast.Assign):
                if any(isinstance(t, ast.Name) and t.id == "_PARTICIPANT_EXPORTS" for t in node.targets):
                    continue
                if any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                    node.value = ast.parse(repr([n for n in ast.literal_eval(node.value) if n not in excluded])).body[0].value
            result.append(node)
        tree.body = result
    else:
        maps = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_EXPORT_MODULES" for t in node.targets):
                maps = ast.literal_eval(node.value)
        allowed = ({name: path for name, path in maps.items() if path in {"aware_issue_sdk.operation", "aware_issue_sdk.local_files"}}
                   if module == "aware_issue_sdk" else
                   {name: path for name, path in maps.items() if name in {"run_workspace_commit", "verify_repository_commit_receipt", "WorkspaceCommitOptions", "WorkspaceCommitIssueMetadata", "WorkspaceCommitOutcome"}})
        return ("from importlib import import_module\n_EXPORT_MODULES = " + repr(allowed) + "\n__all__ = sorted(_EXPORT_MODULES)\n"
                "def __getattr__(name):\n    module_name = _EXPORT_MODULES.get(name)\n    if module_name is None:\n        raise AttributeError(name)\n"
                "    value = getattr(import_module(module_name, package=__name__), name)\n    globals()[name] = value\n    return value\n").encode()
    return (ast.unparse(tree) + "\n").encode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repository", type=Path, required=True)
    parser.add_argument("--registry-wheelhouse", type=Path, required=True)
    args = parser.parse_args()
    repo = args.source_repository.resolve()
    root = Path(__file__).resolve().parent
    public = root.parents[1]
    consumer_version = tomllib.loads((root / "source/aware_agent_cli/pyproject.toml").read_text())["project"]["version"]
    subprocess.run(["python3.12", "-B", str(public / "protocols/publication/render_agent_contract.py")], check=True)
    output = root / "distribution"
    output.mkdir(exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix="aware-agent-build-"))
    wheelhouse = working / "aware-agent-fs-linux_x86_64-py312" / "wheelhouse"
    wheelhouse.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location("prior_install", public / "protocols/install.py")
    assert spec and spec.loader
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    _, outer = base.verified_archive((public / "protocols/distributions" / base.ARCHIVE).read_bytes(), base.ENVELOPE_SHA256)
    _, old_payload = base.verified_archive(outer["payload/aware-goal-native-fs-v2-linux_x86_64-py312.tar.gz"], base.PAYLOAD_SHA256)
    for name, data in old_payload.items():
        if name.startswith("wheelhouse/") and name.endswith(".whl") and not name.startswith("wheelhouse/aware_goal_"):
            (wheelhouse / Path(name).name).write_bytes(data)
    license_bytes = source(repo, "LICENSE")
    provenance = []
    for name, (directory, module, version, selected, dependencies) in PACKAGES.items():
        target = root / "source" / name.replace("-", "_")
        (target / module).mkdir(parents=True, exist_ok=True)
        if selected is None:
            listing = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", PIN, "--", directory + "/" + module], cwd=repo, text=True).splitlines()
            selected = [path.removeprefix(directory + "/" + module + "/") for path in listing if path.endswith((".py", ".typed"))]
        for relative in selected:
            source_path = directory + "/" + module + "/" + relative
            original = source(repo, source_path)
            data = curate_init(original, module) if relative == "__init__.py" and module in {"aware_issue_sdk", "aware_issue_runtime", "aware_workspace_operator"} else original
            destination = target / module / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            provenance.append({"package": name, "source_path": source_path,
                               "source_sha256": digest(original), "shipped_sha256": digest(data),
                               "disposition": "curated export facade" if data != original else "byte-identical owner implementation"})
        (target / "LICENSE").write_bytes(license_bytes)
        (target / "NOTICE").write_text(f"{name}\nCopyright 2026 Luis Lechuga Ruiz\nAware-authored work is Apache-2.0.\nNeutral consumer packaging projection of the pinned owner; no domain decision rewrite.\n")
        (target / "README.md").write_text(f"# {name}\n\nSource-derived neutral consumer projection, version {version}.\nSource revision: `{PIN}`.\nOnly the published filesystem operation surface is supported.\nOriginal source coordinates and byte dispositions are in `../../source-provenance.json`.\n")
        metadata = (f'[project]\nname = "{name}"\nversion = "{version}"\nrequires-python = ">=3.12"\n'
                    'license = "Apache-2.0"\nlicense-files = ["LICENSE", "NOTICE"]\n'
                    f'dependencies = {json.dumps(dependencies)}\n'
                    '[build-system]\nrequires = ["hatchling>=1.27.0"]\nbuild-backend = "hatchling.build"\n'
                    f'[tool.hatch.build.targets.wheel]\npackages = ["{module}"]\n')
        if name == "aware-issue-cli":
            metadata += '[project.scripts]\naware-issue-cli = "aware_issue_cli.main:main"\n'
        (target / "pyproject.toml").write_text(metadata)
    agent = root / "source/aware_agent_cli"
    (agent / "LICENSE").write_bytes(license_bytes)
    (agent / "NOTICE").write_text("Aware agent CLI\nCopyright 2026 Luis Lechuga Ruiz\nApache-2.0. Workflow composition only; existing domain owners retain decisions.\n")
    for name in PREPARATION_PACKAGES:
        package = root / "source" / name.replace("-", "_")
        (package / "LICENSE").write_bytes(license_bytes)
        (package / "NOTICE").write_text(name + "\nCopyright 2026 Luis Lechuga Ruiz\nApache-2.0. Neutral filesystem preparation only; existing Issue and publication owners remain unchanged.\n")
    for name in [*PACKAGES, *PREPARATION_PACKAGES, "aware-agent-cli"]:
        subprocess.run(["uv", "build", "--wheel", "--no-sources", "--out-dir", str(wheelhouse), str(root / "source" / name.replace("-", "_"))], check=True)
    registry_evidence = []
    for name, version in REGISTRY.items():
        paths = sorted(args.registry_wheelhouse.glob(name + "-" + version + "-*.whl"))
        if len(paths) != 1:
            raise ValueError("exact_registry_wheel_required:" + name)
        path = paths[0]
        data = path.read_bytes()
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json") as response:
            publication = json.load(response)
        record = next((item for item in publication["urls"] if item["filename"] == path.name and item["digests"]["sha256"] == digest(data)), None)
        if record is None:
            raise ValueError("registry_publication_hash_mismatch:" + name)
        registry_evidence.append({"name": name, "version": version, "filename": path.name, "sha256": digest(data), "url": record["url"]})
        (wheelhouse / path.name).write_bytes(data)
    bundle = wheelhouse.parent
    for name, data in outer.items():
        if name.startswith("notices/") and not name.startswith("notices/wheels/aware-goal-"):
            destination = bundle / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    for wheel_path in wheelhouse.glob("*.whl"):
        with zipfile.ZipFile(wheel_path) as wheel:
            for member in wheel.namelist():
                if ".dist-info/" in member and ("/licenses/" in member or member.rsplit("/", 1)[-1].upper() in {"LICENSE", "NOTICE", "COPYING"}):
                    destination = bundle / "notices/packages" / wheel_path.stem / member
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(wheel.read(member))
    component_root = root / "notices/pydantic-core"
    component_manifest = json.loads((component_root / "manifest.json").read_bytes())
    core_wheel = next(wheelhouse.glob("pydantic_core-*.whl"))
    if component_manifest["wheel_sha256"] != digest(core_wheel.read_bytes()):
        raise ValueError("component_notice_wheel_mismatch")
    for component in component_manifest["components"]:
        for notice in component["legal_files"]:
            if digest((component_root / notice["path"]).read_bytes()) != notice["sha256"]:
                raise ValueError("component_notice_byte_mismatch:" + notice["path"])
    for path in sorted(component_root.rglob("*")):
        if path.is_file():
            destination = bundle / "notices/pydantic-core" / path.relative_to(component_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
    (bundle / "notices/CONSUMER-NOTICES.md").write_bytes((root / "NOTICES.md").read_bytes())
    provenance_document = {"source_revision": PIN, "files": provenance, "registry_acquisitions": registry_evidence,
                           "packaging_change": "Neutral export/dependency projection; three curated __init__ facades; business/owner implementation bytes unchanged.",
                           "consumer_versions": {name: record[2] for name, record in PACKAGES.items()}}
    provenance_document["public_authored_preparation"] = {
        path.relative_to(root).as_posix(): digest(path.read_bytes())
        for name in PREPARATION_PACKAGES
        for path in (root / "source" / name.replace("-", "_")).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts}
    (root / "source-provenance.json").write_text(json.dumps(provenance_document, indent=2, sort_keys=True) + "\n")
    for path in (root / "source").rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            destination = bundle / "source" / path.relative_to(root / "source")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
    (bundle / "source-provenance.json").write_bytes((root / "source-provenance.json").read_bytes())
    wheels = [{"filename": path.name, "sha256": digest(path.read_bytes())} for path in sorted(wheelhouse.glob("*.whl"))]
    if len(wheels) != 22:
        raise ValueError("unexpected_payload_count:" + str(len(wheels)))
    contract_source = tomllib.loads((agent / "pyproject.toml").read_text())["tool"]["aware"]["agent-contract"]["source"]
    contract = json.loads((public / contract_source / "contract.json").read_bytes())
    manifest = {"format": "aware.agent.fs.consumer-bundle.v1", "version": consumer_version, "authority_mode": "filesystem", "python_minor": "3.12", "platform": "linux_x86_64", "wheels": wheels,
                "root_requirement": "aware-agent-cli==" + consumer_version, "source_revision": PIN,
                "agent_contract": {"ref": contract["contract_ref"], "version": contract["version"]},
                "preparation_operation": "repository_sdk.prepare_repository",
                "supported_commands": ["aware", "aware-issue-cli"], "generated_service_or_ontology_packages": []}
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (bundle / "README.md").write_text("# Aware agent filesystem preview\n\nLinux x86-64 / Python 3.12.\nVerify SHA256SUMS before use. Sources and component notices accompany the wheels.\nInstall offline into a new venv: python3.12 -m venv /absolute/new-venv; /absolute/new-venv/bin/python -m pip install --no-index --find-links wheelhouse aware-agent-cli==" + consumer_version + "\nConsumer entrypoint: aware. Setup installs a versioned agent contract and modules. No service, ontology, generated API or development checkout.\n")
    files = sorted(path for path in bundle.rglob("*") if path.is_file())
    (bundle / "SHA256SUMS").write_text("".join(digest(path.read_bytes()) + "  " + path.relative_to(bundle).as_posix() + "\n" for path in files))
    archive = output / ("aware-agent-fs-" + consumer_version + "-linux_x86_64-py312.tar.gz")
    with archive.open("wb") as stream:
        with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as tar:
                for path in sorted(bundle.rglob("*")):
                    if path.is_file():
                        data = path.read_bytes()
                        info = tarfile.TarInfo(bundle.name + "/" + path.relative_to(bundle).as_posix())
                        info.size, info.mode, info.mtime = len(data), 0o644, 0
                        tar.addfile(info, io.BytesIO(data))
    release = {**manifest, "archive": "distribution/" + archive.name, "archive_sha256": digest(archive.read_bytes()),
               "archive_bytes": archive.stat().st_size, "builder_sha256": digest(Path(__file__).read_bytes()),
               "source_provenance_sha256": digest((root / "source-provenance.json").read_bytes())}
    (root / "release.json").write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"archive_sha256": release["archive_sha256"], "packages": len(wheels), "source_files": len(provenance)}))


if __name__ == "__main__":
    main()
