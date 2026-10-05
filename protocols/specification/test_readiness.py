"""Preparation accounting only: no Aware imports, parser, admission or enforcement."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import unittest
from pathlib import Path, PurePosixPath

import tomllib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def decode(data):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate_plan_key")
            value[key] = item
        return value

    return json.loads(data, object_pairs_hook=pairs)


def plan():
    return decode((HERE / "readiness.json").read_bytes())


def requirement_name(requirement):
    match = re.match(r"^([a-z][a-z0-9-]*)(?:[<>=]|$)", requirement)
    if match is None:
        raise ValueError("unsupported_authored_requirement_shape")
    return match[1]


def git_bytes(owner, *arguments):
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(owner), *arguments],
        env={
            "PATH": os.defpath,
            "LC_ALL": "C",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
        },
        stderr=subprocess.PIPE,
    )


def verify_owner(owner):
    """Maintainer provenance check of committed blobs, not a customer runtime path."""
    value = plan()
    owner = owner.resolve(strict=True)
    if (
        Path(os.fsdecode(git_bytes(owner, "rev-parse", "--show-toplevel")).rstrip("\n"))
        != owner
    ):
        raise ValueError("owner_repository_root_mismatch")
    commit = value["source_owner"]["commit"]
    if git_bytes(owner, "cat-file", "-t", commit).strip() != b"commit":
        raise ValueError("owner_revision_not_commit")
    pins = [*value["prospective_packages"], *value["source_pins"], *value["resources"]]
    bodies = {}
    for item in pins:
        path = item.get("manifest", item.get("path"))
        expected = item.get("manifest_sha256", item.get("sha256"))
        body = git_bytes(owner, "show", commit + ":" + path)
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("owner_blob_pin_mismatch:" + path)
        bodies[path] = body
    for item in value["prospective_packages"]:
        project = tomllib.loads(bodies[item["manifest"]].decode())["project"]
        for actual, expected in (
            (project["name"], item["name"]),
            (project["version"], item["version"]),
            (project["requires-python"], item["requires_python"]),
            (project["dependencies"], item["dependencies"]),
        ):
            if actual != expected:
                raise ValueError("authored_package_metadata_mismatch")
        if "entrypoint" in item and project.get("scripts") != item["entrypoint"]:
            raise ValueError("authored_entrypoint_mismatch")
    issue_manifest = "workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/pyproject.toml"
    project = tomllib.loads(bodies[issue_manifest].decode())["project"]
    if project["optional-dependencies"]["specification"] != [
        "aware-specification-fs-sdk-adapter>=0.1.0"
    ]:
        raise ValueError("authored_issue_extra_mismatch")
    if any(
        requirement_name(r).startswith("aware-specification")
        for r in project["dependencies"]
    ):
        raise ValueError("specification_leaked_into_mandatory_issue_dependencies")
    return {
        "outcome": "owner_pins_match",
        "committed_blobs": len(pins),
        "supplier_manifests": len(value["prospective_packages"]),
        "authority": "preparation_provenance_only",
        "installed_capability": False,
    }


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.value = plan()
        self.capabilities = {c["id"]: c for c in self.value["capabilities"]}

    def test_record_is_preparation_not_admission(self):
        self.assertEqual(
            self.value["format"], "aware.protocol.specification.consumer-preparation.v1"
        )
        self.assertEqual(self.value["status"], "proposal_not_consumer_admission")
        self.assertEqual(self.value["authority_mode"], "filesystem")

    def test_no_candidate_closure_or_publication_claim(self):
        self.assertIsNone(self.value["consumer_dependency_closure"])
        self.assertIsNone(self.value["public_candidate"])
        self.assertIs(self.value["publication_authorized"], False)

    def test_baseline_matches_immutable_a6_manifest(self):
        data = (ROOT / "protocols/agent/release-a6-candidate.json").read_bytes()
        release = decode(data)
        baseline = self.value["public_baseline"]
        self.assertEqual(hashlib.sha256(data).hexdigest(), baseline["release_sha256"])
        self.assertEqual(release["version"], baseline["version"])
        self.assertEqual(
            release["agent_contract"],
            {"ref": baseline["contract_ref"], "version": baseline["contract_version"]},
        )
        self.assertEqual(release["supported_commands"], baseline["supported_commands"])
        self.assertEqual(len(release["wheels"]), 22)

    def test_baseline_archive_is_unchanged(self):
        release = decode(
            (ROOT / "protocols/agent/release-a6-candidate.json").read_bytes()
        )
        data = (ROOT / "protocols/agent" / release["archive"]).read_bytes()
        self.assertEqual(
            hashlib.sha256(data).hexdigest(),
            self.value["public_baseline"]["archive_sha256"],
        )

    def test_spec_is_unavailable_in_baseline(self):
        self.assertEqual(
            self.value["public_baseline"]["specification_role"], "unavailable"
        )
        self.assertNotIn(
            "aware-spec", self.value["public_baseline"]["supported_commands"]
        )

    def test_reuse_existing_profile_not_new_version_allocation(self):
        profile = self.value["profile_proposal"]
        self.assertEqual(profile["collaboration_profile"], "aware.collaboration.fs_v1")
        self.assertEqual(profile["semantic_version"], 1)
        self.assertIs(profile["new_profile_allocated"], False)
        self.assertEqual(profile["manifest_filename"], "aware.protocol.toml")

    def test_exact_existing_spec_carriage(self):
        profile = self.value["profile_proposal"]
        self.assertEqual(profile["specification_record_profile"], "specification_fs_v1")
        self.assertEqual(profile["specification_manifest"], "aware.spec.toml")
        self.assertEqual(profile["specification_manifest_aware"], 1)
        self.assertEqual(profile["path_template"], "<spec-key>/aware.spec.toml")

    def test_setup_and_admitted_interfaces_are_not_claimed(self):
        profile = self.value["profile_proposal"]
        self.assertIs(profile["setup_implemented"], False)
        self.assertEqual(profile["admitted_customer_commands"], [])
        self.assertIs(profile["roots_discovered_from_dependencies"], False)
        self.assertIs(profile["other_unavailable_records_implicitly_enabled"], False)

    def test_selection_interface_is_not_an_implemented_operation(self):
        proposal = self.value["selection_interface_proposal"]
        self.assertEqual(proposal["status"], "owner_agreement_pending_not_implemented")
        self.assertEqual(proposal["issuer"], "admit_specification_selection")
        self.assertEqual(
            proposal["consumer"],
            "SpecificationFsSdkProvider.from_protocol_selection",
        )
        self.assertEqual(proposal["protocol_owner"], "aware-protocol-fs-adapter")
        for key in ("serialized_authority", "write_authority", "git_commitment"):
            self.assertIs(proposal[key], False)

    def test_selection_preserves_descriptor_and_original_provider_boundary(self):
        proposal = self.value["selection_interface_proposal"]
        self.assertEqual(
            proposal["source_base"],
            "retained_repository_descriptor_not_reopened_path",
        )
        self.assertIs(proposal["before_after_guard"], True)
        self.assertEqual(
            proposal["raw_constructor"],
            "compatibility_internal_only_no_consumer_fallback",
        )
        self.assertEqual(
            proposal["iteration_capability"],
            "distinct_original_SPEC_provider_admission",
        )
        self.assertEqual(
            proposal["integration_dependency"],
            "optional_protocol_extra_in_FS_sdk_adapter",
        )

    def test_factory_is_read_only_even_when_provider_class_has_writer(self):
        proposal = self.value["selection_interface_proposal"]
        self.assertEqual(
            proposal["factory_mode"], "read_only_observation_and_iteration_admission"
        )
        self.assertEqual(
            proposal["draft_writer"],
            "explicit_pre_effect_refusal_until_Issue_governed_writer_accepted",
        )

    def test_factory_failure_and_shared_selection_have_distinct_cleanup(self):
        proposal = self.value["selection_interface_proposal"]
        self.assertEqual(
            proposal["borrowed_descriptor"],
            "fresh_duplicate_never_issuer_retained_descriptor",
        )
        self.assertEqual(
            proposal["construction_validation_failure"],
            "close_new_provider_and_retire_new_admissions",
        )
        self.assertEqual(
            proposal["provider_close"],
            "provider_resources_only_not_shared_selection_release",
        )

    def test_optional_extra_is_lazy_but_required_by_consumer_cli(self):
        proposal = self.value["selection_interface_proposal"]
        self.assertEqual(
            proposal["integration_imports"],
            "lazy_missing_extra_typed_refusal_no_fallback",
        )
        self.assertEqual(
            proposal["consumer_CLI_dependency"],
            "explicit_FS_sdk_adapter_protocol_extra",
        )
        self.assertEqual(proposal["integration_version_bound"], "owner_review_pending")

    def test_setup_is_manifest_only_governed_not_an_authoring_shortcut(self):
        proposal = self.value["setup_behavior_proposal"]
        self.assertEqual(proposal["status"], "owner_agreement_pending_not_implemented")
        self.assertIsNone(proposal["entrance"])
        self.assertEqual(
            proposal["requires"],
            "existing_prepared_Git_repository_and_exact_Issue_scope",
        )
        self.assertEqual(
            proposal["delta"], "unavailable_SPEC_to_explicit_FS_authority_only"
        )
        for key in (
            "creates_SPEC_document",
            "creates_approved_iteration",
            "changes_customer_AGENTS",
            "stages_commits_or_pushes",
        ):
            self.assertIs(proposal[key], False)
        self.assertEqual(proposal["effect_reporting"], ["none", "applied", "unknown"])

    def test_setup_preserves_bindings_and_private_directory_modes(self):
        proposal = self.value["setup_behavior_proposal"]
        self.assertLessEqual(
            {"other_records", "bootstrap", "customer_comments", "directory_modes"},
            set(proposal["preserves"]),
        )
        self.assertEqual(
            proposal["different_active_binding"],
            "refuse_pending_explicit_reconfiguration",
        )
        self.assertEqual(
            proposal["identical_binding"],
            "observed_no_op_fresh_admission_still_required",
        )

    def test_observe_and_draft_use_authored_operations(self):
        for key, operation, provider in (
            (
                "spec-observe",
                "specification_sdk.observe",
                "specification.source.observe",
            ),
            (
                "spec-draft-create",
                "specification_sdk.create_draft",
                "specification.draft.create",
            ),
        ):
            self.assertEqual(self.capabilities[key]["canonical_operation"], operation)
            self.assertEqual(self.capabilities[key]["provider_operation"], provider)
        self.assertEqual(
            self.capabilities["spec-draft-create"]["source_entrance"],
            "aware-spec create-draft",
        )

    def test_identity_is_composition_not_new_sdk_operation(self):
        row = self.capabilities["iteration-identity"]
        self.assertIsNone(row["canonical_operation"])
        self.assertIsNone(row["provider_operation"])
        self.assertEqual(row["source_entrance"], "aware-spec iteration-identity")
        self.assertIn("resolve_iteration_identity", row["composition"])

    def test_pairing_uses_workflow_owner_without_cli_claim(self):
        row = self.capabilities["proposed-pairing"]
        self.assertEqual(
            row["canonical_operation"],
            "issue_sdk.observe_specification_iteration_binding",
        )
        self.assertEqual(
            row["provider_operation"],
            "workflow.issue.specification_iteration_binding.observe",
        )
        self.assertEqual(row["public_status"], "no_cli_or_installed_customer_admission")
        for name in ("binding_persisted", "approval_verified", "work_authorized"):
            self.assertIs(row[name], False)

    def test_retained_port_is_not_serialized_operation_authority(self):
        row = self.capabilities["retained-source-port"]
        self.assertIsNone(row["canonical_operation"])
        self.assertEqual(
            row["public_status"], "library_integration_not_serialized_capability"
        )
        self.assertIn("same-process-original-provider-lifetime", row["requires"])

    def test_unavailable_writers_have_no_invented_operations(self):
        for key in (
            "approved-iteration-authoring-import",
            "durable-iteration-issue-binding",
            "spec-guarded-publication",
        ):
            row = self.capabilities[key]
            self.assertEqual(row["source_status"], "unavailable")
            self.assertEqual(row["public_status"], "unavailable")
            self.assertIsNone(row["canonical_operation"])
            self.assertIsNone(row["source_entrance"])

    def test_all_capability_requirements_name_real_preparation_gates(self):
        gates = {g["id"] for g in self.value["gates"]}
        self.assertEqual(len(gates), len(self.value["gates"]))
        self.assertEqual(len(self.capabilities), len(self.value["capabilities"]))
        for row in self.capabilities.values():
            self.assertLessEqual(set(row["requires"]), gates)

    def test_draft_needs_scope_and_protocol_governance(self):
        self.assertLessEqual(
            {
                "protocol-source-composition",
                "issue-write-governance",
                "semantic-input-preparation",
            },
            set(self.capabilities["spec-draft-create"]["requires"]),
        )
        self.assertEqual(
            self.capabilities["spec-draft-create"]["effect"],
            "write_absent_draft_without_iterations",
        )

    def test_exact_six_prospective_neutral_projects(self):
        names = {p["name"] for p in self.value["prospective_packages"]}
        self.assertEqual(
            names,
            {
                "aware-specification-runtime",
                "aware-specification-fs-source-contract",
                "aware-specification-fs-adapter",
                "aware-specification-sdk",
                "aware-specification-fs-sdk-adapter",
                "aware-specification-cli",
            },
        )
        self.assertEqual(len(names), len(self.value["prospective_packages"]))

    def test_direct_edges_stay_in_neutral_graph_or_jsonschema(self):
        names = {p["name"] for p in self.value["prospective_packages"]}
        for package in self.value["prospective_packages"]:
            self.assertLessEqual(
                {requirement_name(r) for r in package["dependencies"]},
                names | {"jsonschema"},
            )
            self.assertEqual(package["version"], "0.1.0")
            self.assertEqual(package["requires_python"], ">=3.12")

    def test_leaf_packages_have_no_runtime_dependencies(self):
        rows = {p["name"]: p for p in self.value["prospective_packages"]}
        for name in (
            "aware-specification-runtime",
            "aware-specification-fs-source-contract",
        ):
            self.assertEqual(rows[name]["dependencies"], [])

    def test_cli_declares_exact_owner_entrance(self):
        cli = next(
            p
            for p in self.value["prospective_packages"]
            if p["name"] == "aware-specification-cli"
        )
        self.assertEqual(
            cli["entrypoint"], {"aware-spec": "aware_specification_cli.main:main"}
        )

    def test_pin_shapes_paths_and_unique_inventory(self):
        pins = [
            *self.value["prospective_packages"],
            *self.value["source_pins"],
            *self.value["resources"],
        ]
        paths = []
        for item in pins:
            path = item.get("manifest", item.get("path"))
            digest = item.get("manifest_sha256", item.get("sha256"))
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertFalse(PurePosixPath(path).is_absolute())
            self.assertNotIn("..", PurePosixPath(path).parts)
            self.assertNotIn("\\", path)
            paths.append(path)
        self.assertEqual(len(paths), 18)
        self.assertEqual(len(paths), len(set(paths)))
        self.assertRegex(self.value["source_owner"]["commit"], r"^[0-9a-f]{40}$")

    def test_resource_has_held_coverage_not_inherited_clearance(self):
        self.assertEqual(len(self.value["resources"]), 1)
        self.assertEqual(
            self.value["resources"][0]["coverage"],
            "candidate_byte_provenance_notice_review_pending",
        )

    def test_no_maintainer_checkout_is_customer_requirement(self):
        self.assertEqual(
            self.value["source_owner"]["access"],
            "maintainer_source_not_public_download_requirement",
        )
        self.assertNotIn("/home/aware", (HERE / "readiness.json").read_text())

    def test_proposal_links_and_required_limits_are_present(self):
        document = (HERE / "PLAN.md").read_text()
        for name in ("readiness.json", "test_readiness.py"):
            self.assertIn(name, document)
        for term in (
            "one Issue per code-change iteration",
            "inside\npublication",
            "No new version is allocated",
            "not a new operation registry",
            "aware-spec",
            "atomic isolation",
            "unsupported",
            "No push",
        ):
            self.assertIn(term, document)

    def test_duplicate_json_key_refused(self):
        with self.assertRaisesRegex(ValueError, "duplicate_plan_key"):
            decode('{"status":"held","status":"accepted"}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-repository", type=Path)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ReadinessTests)
    )
    if not result.wasSuccessful():
        return 1
    if args.owner_repository is not None:
        print(json.dumps(verify_owner(args.owner_repository), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
