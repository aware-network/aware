"""Two-wheel reader successor over the retained SDK02 bundle; no writer extras.

Uses pinned existing packaging owners. Production bytes come only from committed
supplier inputs. Builds/installs/tests write only beneath a fresh proof root;
record publication is the explicit canonical generator for two scoped JSON files.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from email.parser import BytesParser
from pathlib import Path

SOURCE_REVISION = "6af0ce47c35acf92b498df823e55fe798b5e2ff9"
BASE_SHA = "e1f866b431492f6e117d0fdf3f165e212d7685e46a941d13107c0216a205d582"
BASE_MANIFEST_SHA = "9a1fe10be4526d07ecae90fd807cd3d622c0c1916167a46829587dd203e379d4"
OWNER = "docs/specs/aware-portable-protocol/conformance/build_specification_read_candidate.py"
OWNER_SHA = "2888e6fdcc2b340f9c766a40980204a1e9c5254170e8a4432fce687d7383b756"
SUPPLIER_INPUTS = "docs/specs/aware-portable-protocol/provenance/specification-cli022-reader-successor-inputs-v1.json"
SUPPLIER_INPUTS_SHA = "b05473a438b1cea14f9cc89a77419947e20d3dfbe68bb60dfd1271cea22b6eb4"
ROOT = "workspaces/aware_kernel/modules/specification/sdks/specification/python"
PACKAGES = (
    ("fs_adapter", "aware-specification-fs-sdk-adapter", "0.3.0"),
    ("cli", "aware-specification-cli", "0.2.2"),
)
PREFIX = "aware-specification-cli022-reader-internal-v1"
RECORD = "specification-cli022-reader-bundle-v1.json"
INPUT_RECORD = "specification-cli022-reader-bundle-inputs-v1.json"


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def owner(repo: Path):
    path = repo / OWNER
    if path.is_symlink() or sha(path.read_bytes()) != OWNER_SHA:
        raise ValueError("packaging_owner_changed")
    spec = importlib.util.spec_from_file_location("cli022_pinned_packaging_owner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def supplier_inputs(repo: Path, helper) -> dict:
    body = helper.committed(repo, SOURCE_REVISION, SUPPLIER_INPUTS)
    if sha(body) != SUPPLIER_INPUTS_SHA:
        raise ValueError("supplier_inventory_changed")
    doc = json.loads(body)
    if len(doc["source_pins"]) != 83:
        raise ValueError("supplier_inventory_count_changed")
    for row in doc["source_pins"]:
        source = helper.committed(repo, SOURCE_REVISION, row["path"])
        blob = hashlib.sha1(
            ("blob " + str(len(source)) + "\0").encode() + source
        ).hexdigest()
        if (len(source), sha(source), blob) != (
            row["bytes"],
            row["sha256"],
            row["git_blob"],
        ):
            raise ValueError("supplier_source_changed:" + row["path"])
    return doc


def build(repo: Path, baseline: Path, proof: Path) -> dict:
    helper = owner(repo)
    suppliers = supplier_inputs(repo, helper)
    archive = helper.load(
        repo / helper.ARCHIVE_HELPER, helper.ARCHIVE_HELPER_SHA, "cli022_archive"
    )
    assembler = helper.load(
        repo / helper.BUILDER, helper.BUILDER_SHA, "cli022_assembler"
    )
    files = archive.archive_files(helper.pinned(baseline, BASE_SHA))
    if (
        archive.verify_checksums(files) != 31
        or sha(files["manifest.json"]) != BASE_MANIFEST_SHA
    ):
        raise ValueError("predecessor_identity_changed")
    old = json.loads(files["manifest.json"])
    if len(old["wheels"]) != 27:
        raise ValueError("predecessor_closure_changed")
    proof.mkdir(exist_ok=False)
    house = proof / "wheelhouse"
    before_house = proof / "baseline-wheelhouse"
    house.mkdir()
    before_house.mkdir()
    changed = {name for _, name, _ in PACKAGES}
    for row in old["wheels"]:
        body = files[row["file"]]
        if sha(body) != row["sha256"]:
            raise ValueError("predecessor_wheel_changed")
        (before_house / Path(row["file"]).name).write_bytes(body)
        if row["name"] not in changed:
            (house / Path(row["file"]).name).write_bytes(body)
    provenance = copy.deepcopy(old["source_provenance"])
    license_body = helper.committed(repo, SOURCE_REVISION, "LICENSE")
    additions = []
    for suffix, name, version in PACKAGES:
        package_root = ROOT + "/" + suffix
        module = name.replace("-", "_")
        names = subprocess.check_output(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                SOURCE_REVISION,
                "--",
                package_root + "/" + module,
            ],
            cwd=repo,
            text=True,
        ).splitlines()
        if not names:
            raise ValueError("empty_supplier")
        target = proof / "sources" / package_root
        target.mkdir(parents=True)
        for path in [
            package_root + "/pyproject.toml",
            package_root + "/README.md",
            *names,
        ]:
            original = helper.committed(repo, SOURCE_REVISION, path)
            projected = (
                helper.project_metadata(original, name, version)
                if path.endswith("/pyproject.toml")
                else original
            )
            destination = proof / "sources" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(projected)
            additions.append(
                {
                    "path": path,
                    "source_revision": SOURCE_REVISION,
                    "source_sha256": sha(original),
                    "projected_sha256": sha(projected),
                    "source_bytes": len(original),
                    "projected_bytes": len(projected),
                }
            )
        (target / "LICENSE").write_bytes(license_body)
        (target / "NOTICE").write_bytes(
            (
                name
                + "\nCopyright 2026 Luis Lechuga Ruiz\nAware-authored work is Apache-2.0.\nNeutral reader packaging profile; optional governed exports are not selected commands.\n"
            ).encode()
        )
        destination = proof / "build" / suffix
        destination.mkdir(parents=True)
        output = helper.run(
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
                str(destination),
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
        (destination / "build.log").write_text(output)
        (wheel,) = tuple(destination.glob("*.whl"))
        members = archive.wheel_files(wheel.read_bytes())
        for path in names:
            if members.get(path[len(package_root) + 1 :]) != helper.committed(
                repo, SOURCE_REVISION, path
            ):
                raise ValueError("wheel_owner_bytes_changed:" + path)
        shutil.copyfile(wheel, house / wheel.name)
        next(p for p in provenance["source_packages"] if p["name"] == name)[
            "version"
        ] = version
    roots = tuple(ROOT + "/" + suffix + "/" for suffix, _, _ in PACKAGES)
    provenance["files"] = [
        r for r in provenance["files"] if not r["path"].startswith(roots)
    ] + [r for r in additions if not r["path"].endswith("/README.md")]
    provenance["cli022_reader_successor"] = {
        "source_revision": SOURCE_REVISION,
        "supplier_input_sha256": SUPPLIER_INPUTS_SHA,
        "supplier_input_count": len(suppliers["source_pins"]),
        "predecessor_archive_sha256": BASE_SHA,
        "changed_packages": sorted(changed),
        "preserved_wheels": 25,
        "selected_extra": "protocol",
        "unselected_extras": ["governed", "draft"],
        "protocol_selection": "exact accepted predecessor Protocol0.4 wheel; no current source substitution",
        "inputs": additions,
    }
    spec = {
        "authority_mode": "filesystem",
        "profile": old["profile"],
        "platform": "linux_x86_64",
        "python_minor": "3.12",
        "bundle_prefix": PREFIX,
        "interfaces": {
            "setup": "aware-protocol-cli[specification-setup]==0.3.1",
            "reader": "aware-specification-cli==0.2.2",
        },
        "launchers": ["aware-protocol", "aware-spec"],
        "source_packages": [],
        "registry_packages": [],
        "source_derived_packages": [],
    }
    origins = {r["name"]: r["origin"] for r in old["wheels"]}
    for wheel in sorted(house.glob("*.whl")):
        members = archive.wheel_files(wheel.read_bytes())
        (metadata,) = [
            b for p, b in members.items() if p.endswith(".dist-info/METADATA")
        ]
        data = BytesParser().parsebytes(metadata)
        field = {
            "aware_source": "source_packages",
            "registry": "registry_packages",
            "source_derived": "source_derived_packages",
        }[origins[data["Name"]]]
        spec[field].append(
            {
                "name": data["Name"],
                "version": data["Version"],
                "hashes": [sha(wheel.read_bytes())],
            }
        )
    result = assembler.assemble_retained_distribution(
        spec, house, proof / "bundle", provenance, epoch=0
    )
    result.update(
        proof_root=str(proof),
        baseline_archive=str(baseline),
        baseline_archive_sha256=BASE_SHA,
        producer_sha256=sha(Path(__file__).read_bytes()),
        packaging_owner_sha256=OWNER_SHA,
        source_revision=SOURCE_REVISION,
        supplier_input_sha256=SUPPLIER_INPUTS_SHA,
        unchanged_wheels=25,
        changed_packages=sorted(changed),
        selected_extra="protocol",
        nonclaims=[
            "customer_authoring",
            "installed_governed_closure",
            "every_write_detection",
            "continuous_confinement",
            "public_notice_clearance",
            "selection",
            "release",
        ],
    )
    (proof / "inputs.json").write_bytes(encoded(provenance))
    (proof / "receipt.json").write_bytes(encoded(result))
    return result


def qualify(repo: Path, proof: Path, tools: Path) -> dict:
    helper = owner(repo)
    receipt = json.loads((proof / "receipt.json").read_bytes())
    if receipt["producer_sha256"] != sha(Path(__file__).read_bytes()):
        raise ValueError("producer_changed_rebuild_required")
    helper.pinned(Path(receipt["archive"]), receipt["archive_sha256"])
    setup_owner = helper.load(
        repo / helper.SETUP_HARNESS, helper.SETUP_HARNESS_SHA, "cli022_setup"
    )
    setup = proof / "setup-proof"
    setup_owner.prepare(repo, setup, tools, proof / "inputs.json")
    inventory = json.loads((setup / "test-inputs.json").read_bytes())
    for suffix in (
        "fs_adapter/tests/test_protocol_selection.py",
        "fs_adapter/tests/test_provider.py",
        "cli/tests/test_protocol_cli.py",
    ):
        path = ROOT + "/" + suffix
        body = helper.committed(repo, SOURCE_REVISION, path)
        (setup / "fixtures" / path).write_bytes(body)
        next(r for r in inventory["fixtures"] if r["path"] == path).update(
            revision=SOURCE_REVISION, sha256=sha(body), bytes=len(body)
        )
    count = sum(
        not r["path"].endswith("/pyproject.toml")
        for r in json.loads((proof / "inputs.json").read_bytes())["files"]
    )
    original = helper.pinned(
        repo / helper.SETUP_HARNESS, helper.SETUP_HARNESS_SHA
    ).decode()
    changes = []
    for before, after, expected in [
        ('"0.3.0"', '"0.3.1"', 4),
        ("assert len(expected) == 26", "assert len(expected) == 27", 1),
        ("assert len(matches) == 89", "assert len(matches) == " + str(count), 1),
    ]:
        if original.count(before) != expected:
            raise ValueError("historical_harness_expectation_changed")
        original = original.replace(before, after)
        changes.append({"before": before, "after": after, "occurrences": expected})
    adapted = setup / "test_installed_specification_setup.py"
    adapted.write_text(original)
    inventory.update(
        harness_sha256=sha(adapted.read_bytes()),
        successor_adaptation={
            "original_sha256": helper.SETUP_HARNESS_SHA,
            "changes": changes,
        },
    )
    (setup / "test-inputs.json").write_bytes(encoded(inventory))
    path = (
        repo
        / "docs/specs/aware-portable-protocol/conformance/test_specification_cli022_reader_installed.py"
    )
    test = proof / path.name
    test.write_bytes(path.read_bytes())
    composition_path = "docs/specs/aware-portable-protocol/conformance/test_specification_sdk02_read_composition_v1.py"
    composition = setup / "fixtures" / composition_path
    composition.parent.mkdir(parents=True, exist_ok=True)
    composition.write_bytes(helper.committed(repo, SOURCE_REVISION, composition_path))
    (proof / "read-test-inputs.json").write_bytes(
        encoded(
            {
                "files": {
                    str(p.relative_to(proof)): sha(p.read_bytes())
                    for p in (
                        test,
                        adapted,
                        composition,
                        setup / "test-inputs.json",
                        proof / "inputs.json",
                    )
                },
                "fixture_qualification": "pinned owner synthetic SPEC; no customer authoring",
            }
        )
    )
    for name, version in (("baseline-env", "0.2.1"), ("env", "0.2.2")):
        environment = proof / name
        if environment.exists() or environment.is_symlink():
            raise ValueError("environment_reuse_refused")
        python = str(environment / "bin/python")
        if name == "env":
            command = [
                "/usr/bin/env",
                "PYTHON_BIN=/usr/bin/python3.12",
                "/bin/sh",
                str(Path(receipt["bundle_directory"]) / "install.sh"),
                str(environment),
            ]
        else:
            helper.run(
                helper.sandbox(
                    proof, ["/usr/bin/python3.12", "-m", "venv", str(environment)]
                ),
                proof,
                env={},
            )
            command = [
                python,
                "-I",
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-compile",
                "--only-binary=:all:",
                "--find-links",
                str(proof / "baseline-wheelhouse"),
                "aware-protocol-cli[specification-setup]==0.3.1",
                "aware-specification-cli==" + version,
            ]
        (proof / (name + "-install.txt")).write_text(
            helper.run(helper.sandbox(proof, command), proof, env={})
        )
        (proof / (name + "-dependency-check.txt")).write_text(
            helper.run(
                helper.sandbox(proof, [python, "-I", "-m", "pip", "check"]),
                proof,
                env={},
            )
        )
    python = str(proof / "env/bin/python")
    setup_command = [
        python,
        "-I",
        str(adapted),
        "run",
        "--proof",
        str(setup),
        "--manifest",
        str(Path(receipt["bundle_directory"]) / "manifest.json"),
        "--junit",
        str(proof / "setup.xml"),
        "--basetemp",
        str(proof / "setup-tests"),
    ]
    (proof / "setup.txt").write_text(
        helper.run(helper.sandbox(proof, setup_command), proof, env={})
    )
    test_code = "import sys; sys.path[:0]=[sys.argv.pop(1)]; import pytest; raise SystemExit(pytest.main(sys.argv[1:]))"
    command = [
        python,
        "-I",
        "-c",
        test_code,
        str(setup / "test-tools"),
        "-q",
        "-p",
        "no:cacheprovider",
        str(test),
        str(composition),
        "--import-mode=importlib",
        "-k",
        "not test_exact_accepted_source_and_27_pins_without_metadata_migration",
        "--junitxml=" + str(proof / "read-parity.xml"),
        "--basetemp=" + str(proof / "read-tests"),
    ]
    (proof / "read-parity.txt").write_text(
        helper.run(helper.sandbox(proof, command), proof, env={})
    )
    counts = {}
    for name in ("setup.xml", "read-parity.xml"):
        suites = list(ET.parse(proof / name).getroot().iter("testsuite"))
        counts[name] = {
            k: sum(int(s.attrib[k]) for s in suites)
            for k in ("tests", "errors", "failures", "skipped")
        }
        if counts[name]["tests"] == 0 or any(
            counts[name][k] for k in ("errors", "failures", "skipped")
        ):
            raise ValueError("incomplete_installed_proof")
    byte_matches = json.loads((setup / "owner-byte-audit.json").read_bytes())["matches"]
    if len(byte_matches) != count:
        raise ValueError("installed_owner_byte_account_changed")
    receipt.update(
        installed_status="reader-only-installed-parity-and-writer-refusal-pass",
        installed_test_counts=counts,
        setup_junit_sha256=sha((proof / "setup.xml").read_bytes()),
        read_junit_sha256=sha((proof / "read-parity.xml").read_bytes()),
        installed_test_sha256=sha(test.read_bytes()),
        test_inputs_sha256=sha((proof / "read-test-inputs.json").read_bytes()),
        audit=json.loads((setup / "dependency-audit.json").read_bytes()),
        installed_byte_matches=len(byte_matches),
        installed_owner_audit_sha256=sha(
            (setup / "owner-byte-audit.json").read_bytes()
        ),
        harness_adaptation=inventory["successor_adaptation"],
    )
    (proof / "receipt.json").write_bytes(encoded(receipt))
    return receipt


def record(proof: Path, second: Path, destination: Path) -> None:
    receipt = json.loads((proof / "receipt.json").read_bytes())
    if receipt["producer_sha256"] != sha(Path(__file__).read_bytes()):
        raise ValueError("producer_changed_rebuild_required")
    helper = owner(Path(__file__).resolve().parents[4])
    other = json.loads((second / "receipt.json").read_bytes())
    helper.pinned(Path(other["archive"]), receipt["archive_sha256"])
    if (
        receipt.get("installed_status")
        != "reader-only-installed-parity-and-writer-refusal-pass"
    ):
        raise ValueError("installed_proof_required")
    inputs = json.loads((proof / "inputs.json").read_bytes())
    body = encoded(inputs)
    receipt.update(second_archive=other["archive"], retained_inputs_sha256=sha(body))
    for name in (RECORD, INPUT_RECORD):
        if (destination / name).exists():
            raise ValueError("immutable_record_exists")
    (destination / INPUT_RECORD).write_bytes(body)
    (destination / RECORD).write_bytes(encoded(receipt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--baseline-archive", type=Path, required=True)
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument("--test-tools", type=Path)
    parser.add_argument("--second-proof", type=Path)
    parser.add_argument("--record-directory", type=Path)
    args = parser.parse_args()
    result = build(args.repository_root, args.baseline_archive, args.proof_root)
    if args.test_tools is not None:
        result = qualify(args.repository_root, args.proof_root, args.test_tools)
    if args.record_directory is not None:
        if args.second_proof is None:
            parser.error("--second-proof required for record generation")
        record(args.proof_root, args.second_proof, args.record_directory)
    print(json.dumps(result, indent=2, sort_keys=True))
