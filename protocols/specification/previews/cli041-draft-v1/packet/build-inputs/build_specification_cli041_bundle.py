"""Internal completion candidate using pinned owners and existing wheel assembly.

No selected/public artifact is replaced. Generated writes are confined to a
fresh proof root; record() is the canonical generator for the two scoped records.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from email.parser import BytesParser
from pathlib import Path

import build_specification_read_candidate as helper
import project_issue_custody_suppliers as projection

BASE_SHA = "e9579e3307747d5f1ee8e53620e13585832fe19458e6544371279d4b13da6ebe"
BASE_MANIFEST_SHA = "77b7dbbe60c10b1b4b0f981cbe5c47a60fae070fb5118af85f41aca9ec199874"
SPEC_REVISION = "8d8d8dc98ee0c27d8003f9ac965e09a4c27042f0"
CLI_REVISION = "340b72bb9a79d1e7bddd56e998a3b78a2c5a98b9"
PROTOCOL_REVISION = "9b98643bbf0300f2d473efc11a8455ff461f3908"
SPEC_ROOT = "workspaces/aware_kernel/modules/specification/sdks/specification/python"
PROTOCOL_ROOT = "workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python"
CHANGED = {
    "aware-protocol-fs-adapter": (PROTOCOL_ROOT, PROTOCOL_REVISION, "0.6.1"),
    "aware-specification-sdk": (SPEC_ROOT + "/public", SPEC_REVISION, "0.3.1"),
    "aware-specification-fs-sdk-adapter": (
        SPEC_ROOT + "/fs_adapter",
        SPEC_REVISION,
        "0.4.1",
    ),
    "aware-specification-cli": (SPEC_ROOT + "/cli", CLI_REVISION, "0.4.1"),
}
PREFIX = "aware-specification-cli041-completion-internal-v1"
HELPER_SHA = "2888e6fdcc2b340f9c766a40980204a1e9c5254170e8a4432fce687d7383b756"
PROJECTION_SHA = "861c57b52202f89daca973fac89cbfd8d9a06fad75b543eefeb04621dc26fb34"


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def build(repo: Path, baseline: Path, proof: Path) -> dict:
    helper.pinned(Path(helper.__file__), HELPER_SHA)
    helper.pinned(Path(projection.__file__), PROJECTION_SHA)
    archive = helper.load(
        repo / helper.ARCHIVE_HELPER, helper.ARCHIVE_HELPER_SHA, "custody_archive"
    )
    assembler = helper.load(
        repo / helper.BUILDER, helper.BUILDER_SHA, "custody_assembler"
    )
    files = archive.archive_files(helper.pinned(baseline, BASE_SHA))
    archive.verify_checksums(files)
    old = json.loads(files["manifest.json"])
    if sha(files["manifest.json"]) != BASE_MANIFEST_SHA or len(old["wheels"]) != 26:
        raise ValueError("baseline_identity_changed")
    bodies, plan = projection.projection(repo)
    proof.mkdir(exist_ok=False)
    house = proof / "wheelhouse"
    house.mkdir()
    retained = []
    for row in old["wheels"]:
        if row["name"] in CHANGED or row["name"] == "aware-protocol-cli":
            continue
        body = files[row["file"]]
        if sha(body) != row["sha256"]:
            raise ValueError("baseline_wheel_changed")
        (house / Path(row["file"]).name).write_bytes(body)
        retained.append(row)
    if len(retained) != 22:
        raise ValueError("retained_closure_changed")
    provenance = copy.deepcopy(old["source_provenance"])
    provenance["owner_revision"] = CLI_REVISION
    roots = tuple(root + "/" for root, _, _ in CHANGED.values()) + (
        "workspaces/aware_kernel/modules/protocol/libs/cli/python/",
    )
    provenance["files"] = [
        r for r in provenance["files"] if not r["path"].startswith(roots)
    ]
    provenance["source_packages"] = [
        r
        for r in provenance["source_packages"]
        if r["name"] not in {*CHANGED, "aware-protocol-cli"}
    ]
    additions = []
    license_body = helper.committed(repo, CLI_REVISION, "LICENSE")
    for name, (root, ref, version) in CHANGED.items():
        module = name.replace("-", "_")
        if name in projection.PACKAGES:
            selected = {p: b for p, b in bodies.items() if p.startswith(root + "/")}
            rows = [r for r in plan["files"] if r["package"] == name]
        else:
            names = subprocess.check_output(
                ["git", "ls-tree", "-r", "--name-only", ref, "--", root + "/" + module],
                cwd=repo,
                text=True,
            ).splitlines()
            selected, rows = {}, []
            for path in [root + "/pyproject.toml", *names]:
                original = helper.committed(repo, ref, path)
                selected[path] = original
                rows.append(
                    {
                        "package": name,
                        "path": path,
                        "source_revision": ref,
                        "source_sha256": sha(original),
                        "source_bytes": len(original),
                        "source_blob": subprocess.check_output(
                            ["git", "rev-parse", ref + ":" + path], cwd=repo, text=True
                        ).strip(),
                    }
                )
        # Packaging-only legal fields; dependency/extras semantics stay authored.
        selected[root + "/pyproject.toml"] = helper.project_metadata(
            selected[root + "/pyproject.toml"], name, version
        )
        target = proof / "sources" / root
        for path, body in selected.items():
            destination = proof / "sources" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)
            row = next(r for r in rows if r["path"] == path)
            row.update(projected_sha256=sha(body), projected_bytes=len(body))
        (target / "LICENSE").write_bytes(license_body)
        (target / "NOTICE").write_text(
            name
            + "\nCopyright 2026 Luis Lechuga Ruiz\nAware-authored work is Apache-2.0.\nInternal neutral completion source profile; no Service/API authority.\n"
        )
        output = proof / "build" / name
        output.mkdir(parents=True)
        log = helper.run(
            [
                "/usr/local/bin/uv",
                "build",
                "--offline",
                "--wheel",
                "--no-sources",
                "--python",
                "/usr/bin/python3.12",
                "--no-python-downloads",
                "--out-dir",
                str(output),
                str(target),
            ],
            proof,
            env=dict(
                os.environ,
                SOURCE_DATE_EPOCH="0",
                UV_OFFLINE="1",
                UV_PYTHON_DOWNLOADS="never",
                PYTHONHASHSEED="0",
            ),
        )
        (output / "build.log").write_text(log)
        (wheel,) = tuple(output.glob("*.whl"))
        members = archive.wheel_files(wheel.read_bytes())
        for path, body in selected.items():
            if (
                not path.endswith("/pyproject.toml")
                and members.get(path[len(root) + 1 :]) != body
            ):
                raise ValueError("wheel_source_mismatch:" + path)
        shutil.copyfile(wheel, house / wheel.name)
        additions.extend(rows)
        provenance["source_packages"].append(
            {"name": name, "version": version, "path": root}
        )
    provenance["files"].extend(additions)
    provenance["completion_successor"] = {
        "selected_extra": "governed",
        "projection": plan,
        "changed_packages": sorted(CHANGED),
        "separate_setup_interface": "aware-protocol-cli 0.3.1: incompatible authored dependency bounds; separate setup installation required",
        "protocol_completion": "original-owner-observation",
        "predecessor_archive_sha256": BASE_SHA,
    }
    spec = {
        "authority_mode": "filesystem",
        "profile": old["profile"],
        "platform": "linux_x86_64",
        "python_minor": "3.12",
        "bundle_prefix": PREFIX,
        "interfaces": {"specification": "aware-specification-cli[governed]==0.4.1"},
        "launchers": ["aware-spec"],
        "source_packages": [],
        "registry_packages": [],
        "source_derived_packages": [],
    }
    origins = {r["name"]: r["origin"] for r in old["wheels"]}
    for wheel in sorted(house.glob("*.whl")):
        members = archive.wheel_files(wheel.read_bytes())
        (metadata,) = [
            body
            for path, body in members.items()
            if path.endswith(".dist-info/METADATA")
        ]
        data = BytesParser().parsebytes(metadata)
        name = data["Name"]
        field = {
            "aware_source": "source_packages",
            "registry": "registry_packages",
            "source_derived": "source_derived_packages",
        }[origins[name]]
        spec[field].append(
            {
                "name": name,
                "version": data["Version"],
                "hashes": [sha(wheel.read_bytes())],
            }
        )
    result = assembler.assemble_retained_distribution(
        spec, house, proof / "bundle", provenance, epoch=0
    )
    bundle = Path(result["bundle_directory"])
    # Historical assembler's appendix describes setup-only. This candidate has
    # a different selected extra; replace its presentation, not any owner logic.
    (bundle / "README.md").write_text(
        "# Internal SPEC 0.4.1 completion qualification candidate\n\nNot a selected customer release. Python 3.12 / Linux x86_64.\n\nVerify SHA256SUMS, then use PYTHON_BIN=/usr/bin/python3.12 ./install.sh /absolute/new/environment.\nOnly aware-spec is exposed. Use the separately installed accepted setup CLI; never overlay environments.\nThe governed extra is selected; exit 0 requires original correlated whole-context completion.\nLate refusals may retain known publication with exit 2; never automatically retry known publication.\nNo approved iterations, Goal writers, Service/API, every-write detection or continuous confinement are admitted.\nPublic notice/content review, consumer acceptance, selection and publication remain held.\n"
    )
    script = (bundle / "install.sh").read_text()
    script = script.replace(
        '"$PYTHON_BIN" -m venv "$TARGET_VENV"',
        'test ! -e "$TARGET_VENV"\ntest ! -L "$TARGET_VENV"\n"$PYTHON_BIN" -m venv "$TARGET_VENV"',
    )
    (bundle / "install.sh").write_text(script)
    checks = sorted(
        p for p in bundle.rglob("*") if p.is_file() and p.name != "SHA256SUMS"
    )
    (bundle / "SHA256SUMS").write_text(
        "".join(
            sha(p.read_bytes()) + "  " + p.relative_to(bundle).as_posix() + "\n"
            for p in checks
        )
    )
    assembler._deterministic_tar(bundle, Path(result["archive"]), 0)
    result.update(
        archive_sha256=sha(Path(result["archive"]).read_bytes()),
        producer_sha256=sha(Path(__file__).read_bytes()),
        projection_sha256=sha(Path(projection.__file__).read_bytes()),
        changed_packages=sorted(CHANGED),
        preserved_wheels=22,
        removed_packages=[],
        protocol_completion="original-owner-observation",
    )
    (proof / "inputs.json").write_bytes(encoded(provenance))
    (proof / "receipt.json").write_bytes(encoded(result))
    return result


def qualify(repo: Path, proof: Path, tools: Path) -> dict:
    helper.pinned(Path(helper.__file__), HELPER_SHA)
    helper.pinned(Path(projection.__file__), PROJECTION_SHA)
    result = json.loads((proof / "receipt.json").read_bytes())
    if result["producer_sha256"] != sha(Path(__file__).read_bytes()) or result[
        "projection_sha256"
    ] != sha(Path(projection.__file__).read_bytes()):
        raise ValueError("producer_changed_rebuild_required")
    helper.pinned(Path(result["archive"]), result["archive_sha256"])
    harness = (
        repo
        / "docs/specs/aware-portable-protocol/conformance/test_specification_cli041_installed.py"
    )
    helper.run(
        [
            str(repo / ".venv/bin/python"),
            "-B",
            str(harness),
            "prepare",
            "--repo",
            str(repo),
            "--proof",
            str(proof),
            "--tools",
            str(tools),
        ],
        proof,
    )
    # Supply the accepted predecessor's complete wheel set in its own environment.
    archive = helper.load(
        repo / helper.ARCHIVE_HELPER,
        helper.ARCHIVE_HELPER_SHA,
        "custody_baseline_archive",
    )
    baseline_record = json.loads(
        (
            repo
            / "docs/specs/aware-portable-protocol/release/specification-cli040-bundle-v1.json"
        ).read_bytes()
    )
    files = archive.archive_files(
        helper.pinned(Path(baseline_record["archive"]), BASE_SHA)
    )
    baseline = proof / "baseline-bundle"
    baseline.mkdir()
    for path, body in files.items():
        target = baseline / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    for environment, bundle in (
        ("baseline-env", baseline),
        ("env", Path(result["bundle_directory"])),
    ):
        if (proof / environment).exists() or (proof / environment).is_symlink():
            raise ValueError("environment_reuse_refused")
        output = helper.run(
            helper.sandbox(
                proof,
                [
                    "/usr/bin/env",
                    "PYTHON_BIN=/usr/bin/python3.12",
                    "/bin/sh",
                    str(bundle / "install.sh"),
                    str(proof / environment),
                ],
            ),
            proof,
            env={},
        )
        (proof / (environment + "-install.txt")).write_text(output)
        output = helper.run(
            helper.sandbox(
                proof,
                [str(proof / environment / "bin/python"), "-I", "-m", "pip", "check"],
            ),
            proof,
            env={},
        )
        (proof / (environment + "-dependency-check.txt")).write_text(output)
    output = helper.run(
        helper.sandbox(
            proof,
            [
                str(proof / "env/bin/python"),
                "-I",
                str(proof / harness.name),
                "run",
                "--proof",
                str(proof),
            ],
        ),
        proof,
        env={},
    )
    (proof / "installed.txt").write_text(output)
    suites = list(ET.parse(proof / "installed.xml").getroot().iter("testsuite"))
    counts = {
        k: sum(int(s.attrib[k]) for s in suites)
        for k in ("tests", "errors", "failures", "skipped")
    }
    if counts["tests"] == 0 or any(
        counts[k] for k in ("errors", "failures", "skipped")
    ):
        raise ValueError("incomplete_installed_proof")
    result.update(
        installed_status="bounded-installed-completion-qualified",
        installed_tests=counts,
        installed_junit_sha256=sha((proof / "installed.xml").read_bytes()),
        installed_harness_sha256=sha(harness.read_bytes()),
        test_inputs_sha256=sha((proof / "test-inputs.json").read_bytes()),
        positive_command_receipts_sha256=sha(
            (proof / "positive-command-receipts.json").read_bytes()
        ),
        installed_audit=json.loads((proof / "installed-audit.json").read_bytes()),
        source_only_deselections=[
            "test_default_import_does_not_require_protocol",
            "test_package_metadata_and_imports_are_dependency_neutral",
            "test_public_sdk_import_boundary",
        ],
        historical_unknown_deselections=[
            "test_genuine_success_and_read_survives_writer_cleanup",
            "test_unavailable_observation_retains_known_transfer_publication_and_cleanup",
        ],
    )
    (proof / "receipt.json").write_bytes(encoded(result))
    return result


def record(proof: Path, second: Path, destination: Path):
    result = json.loads((proof / "receipt.json").read_bytes())
    other = json.loads((second / "receipt.json").read_bytes())
    if result["producer_sha256"] != sha(Path(__file__).read_bytes()) or result[
        "projection_sha256"
    ] != sha(Path(projection.__file__).read_bytes()):
        raise ValueError("producer_changed_rebuild_required")
    if not result.get("installed_status"):
        raise ValueError("installed_proof_required")
    helper.pinned(Path(result["archive"]), result["archive_sha256"])
    helper.pinned(Path(other["archive"]), result["archive_sha256"])
    result["second_build_archive_sha256"] = other["archive_sha256"]
    result["proof_root"] = str(proof)
    result["second_build_root"] = str(second)
    result["nonclaims"] = [
        "unassisted customer acceptance",
        "approval or approved-iteration authoring",
        "public notice/content acceptance",
        "selection",
        "release",
        "external evaluation",
    ]
    (destination / "specification-cli041-bundle-v1.json").write_bytes(encoded(result))
    (destination / "specification-cli041-bundle-inputs-v1.json").write_bytes(
        (proof / "inputs.json").read_bytes()
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument(
        "--action", choices=["build", "qualify", "record"], default="build"
    )
    parser.add_argument("--tools", type=Path)
    parser.add_argument("--second-proof", type=Path)
    parser.add_argument("--record-directory", type=Path)
    args = parser.parse_args()
    if args.action == "build":
        result = build(
            args.repo.resolve(), args.baseline.resolve(), args.proof.resolve()
        )
    elif args.action == "qualify":
        result = qualify(
            args.repo.resolve(), args.proof.resolve(), args.tools.resolve()
        )
    else:
        record(
            args.proof.resolve(),
            args.second_proof.resolve(),
            args.record_directory.resolve(),
        )
        result = {"status": "recorded"}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
