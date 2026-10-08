import copy
import importlib.util
import os
from dataclasses import replace
from pathlib import Path

import pytest
from aware_specification_fs_adapter import SpecificationFsSchemaResolutionContext
from aware_specification_fs_sdk_adapter import (
    SpecificationFsSdkProvider,
    SpecificationIterationAdmission,
    revalidate_specification_iteration_admission,
)
from aware_specification_fs_sdk_adapter import draft as draft_module
from aware_specification_fs_sdk_adapter import provider as provider_module
from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationPhaseDefinition,
    SpecificationPhaseDependency,
    SpecificationPhaseGateDefinition,
)
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
)

_module = Path(__file__).parents[5]
_spec = importlib.util.spec_from_file_location(
    "spec_fs_existing_fixtures", _module / "libs/fs_adapter/python/tests/conftest.py"
)
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
canonical_tree = _fixtures.canonical_tree
schema_bytes = _fixtures.schema_bytes


def definition():
    context = SpecificationFsSchemaResolutionContext()
    inv = SpecificationInvariantDefinition("safe", "Never discard other work")
    gate = SpecificationPhaseGateDefinition(
        "verified",
        "The change is independently verified.",
        "aware.specification.gate.evidence-accepted.v1",
        "example.evidence.v1",
        ("specification:example.spec/invariant:safe",),
    )
    phase = SpecificationPhaseDefinition(
        "first",
        "First increment",
        0,
        gate,
        description="Deliver the first bounded increment.",
    )
    return SpecificationDefinition(
        "example.spec",
        "Example",
        1,
        context.semantic_resolution_digest,
        (inv,),
        (phase,),
        "Coordinate bounded changes.",
    )


def open_provider(base, roots):
    fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY)
    try:
        return SpecificationFsSdkProvider(fd, roots)
    finally:
        os.close(fd)


def test_draft_creates_valid_package_and_never_accepts_phase(tmp_path):
    (tmp_path / "plans").mkdir()
    (tmp_path / "dirty.txt").write_text("foreign work\n")
    provider = open_provider(tmp_path, ("plans/demo",))
    try:
        result = SpecificationSdkClient(provider).create_draft(
            SpecificationDraftRequest(definition(), "author", "intent")
        )
        assert result.observation.snapshot.definitions == (definition(),)
        assert result.observation.iterations == ()
        assert len(result.created_paths) == 6
        assert (tmp_path / "dirty.txt").read_text() == "foreign work\n"
        assert (
            (tmp_path / "plans/demo/phases/00-first/README.md")
            .read_text()
            .startswith("# Phase 00")
        )
        assert (
            "State: `planned`"
            in (tmp_path / "plans/demo/phases/00-first/README.md").read_text()
        )
        assert not list((tmp_path / "plans").glob(".aware-spec-draft-*"))
        with pytest.raises(SpecificationOperationError, match="draft_target_exists"):
            provider.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
    finally:
        provider.close()


def test_internal_dependency_and_projection_lower_with_same_owner(tmp_path):
    first = definition().phases[0]
    second = replace(
        first,
        phase_key="second",
        title="Second",
        ordinal=1,
        dependencies=(
            SpecificationPhaseDependency(
                "first-required",
                "specification:example.spec/phase:first",
                first.gate.gate_digest,
                rationale="Needs | foundation\nfirst",
            ),
        ),
    )
    provider = open_provider(tmp_path, ("plan",))
    try:
        result = provider.create_draft(
            SpecificationDraftRequest(
                replace(definition(), phases=(first, second)), "author", "intent"
            )
        )
        assert len(result.observation.snapshot.definitions[0].phases) == 2
        assert (
            result.observation.snapshot.definitions[0]
            .phases[1]
            .dependencies[0]
            .rationale
            == "Needs | foundation\nfirst"
        )
    finally:
        provider.close()


@pytest.mark.parametrize("root", ["../escape", "/absolute", "a/../b", "a\\b"])
def test_bad_root_selection_refuses(tmp_path, root):
    with pytest.raises(SpecificationOperationError):
        open_provider(tmp_path, (root,))


def test_symlink_parent_refused_before_stage(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "alias").symlink_to(outside, target_is_directory=True)
    provider = open_provider(tmp_path, ("alias/demo",))
    try:
        with pytest.raises(SpecificationOperationError):
            provider.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
        assert list(outside.iterdir()) == []
    finally:
        provider.close()


def test_competing_target_is_never_replaced(tmp_path, monkeypatch):
    original = provider_module.rename_no_replace

    def compete(parent_fd, stage, target):
        os.mkdir(target, dir_fd=parent_fd)
        original(parent_fd, stage, target)

    monkeypatch.setattr(provider_module, "rename_no_replace", compete)
    provider = open_provider(tmp_path, ("demo",))
    try:
        with pytest.raises(
            SpecificationOperationError, match="draft_target_exists"
        ) as caught:
            provider.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
        assert caught.value.effect == "none"
        assert list((tmp_path / "demo").iterdir()) == []
        assert not list(tmp_path.glob(".aware-spec-draft-*"))
    finally:
        provider.close()


def test_prepublication_parser_failure_leaves_no_target(tmp_path):
    bad = replace(definition(), description="## Goal\n\nInjected second section")
    provider = open_provider(tmp_path, ("demo",))
    try:
        with pytest.raises(SpecificationOperationError):
            provider.create_draft(SpecificationDraftRequest(bad, "author", "intent"))
        assert list(tmp_path.iterdir()) == []
    finally:
        provider.close()


def test_failure_after_effect_retains_published_qualification(tmp_path, monkeypatch):
    provider = open_provider(tmp_path, ("demo",))

    def fail(request):
        raise SpecificationOperationError("source_changed")

    monkeypatch.setattr(provider, "observe", fail)
    try:
        with pytest.raises(SpecificationOperationError) as caught:
            provider.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
        assert caught.value.effect == "published"
        assert (tmp_path / "demo/aware.spec.toml").is_file()
    finally:
        provider.close()


def test_malformed_result_after_real_publication_retains_unknown_effect(
    tmp_path, monkeypatch
):
    provider = open_provider(tmp_path, ("demo",))
    original_create = provider.create_draft
    publications = []

    def malformed_result(request):
        result = original_create(request)
        publications.append(result.observation.source_digest)
        object.__delattr__(result, "created_paths")
        return result

    monkeypatch.setattr(provider, "create_draft", malformed_result)
    try:
        client = SpecificationSdkClient(provider)
        with pytest.raises(SpecificationOperationError) as caught:
            client.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
        assert caught.value.code == "draft_result_invalid"
        assert caught.value.effect == "unknown"
        assert isinstance(caught.value.__cause__, AttributeError)
        assert (tmp_path / "demo/aware.spec.toml").is_file()
        fresh = client.observe(SpecificationObserveRequest())
        assert fresh.snapshot.definitions == (definition(),)
        assert publications == [fresh.source_digest]
        assert not list(tmp_path.glob(".aware-spec-draft-*"))
    finally:
        provider.close()


def test_failure_during_write_cleans_only_owned_stage(tmp_path, monkeypatch):
    original = draft_module.os.write

    def failure(fd, body):
        raise OSError("fault injection")

    monkeypatch.setattr(draft_module.os, "write", failure)
    provider = open_provider(tmp_path, ("demo",))
    try:
        with pytest.raises(SpecificationOperationError):
            provider.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
        assert list(tmp_path.iterdir()) == []
    finally:
        monkeypatch.setattr(draft_module.os, "write", original)
        provider.close()


def test_real_iteration_admission_revalidation_and_release(canonical_tree):
    base, root = canonical_tree
    provider = open_provider(base, (root,))
    try:
        capability = provider.admit_iteration(
            SpecificationObserveRequest(),
            "specification:example.spec/phase:foundation/iteration:proof",
        )
        fresh = revalidate_specification_iteration_admission(capability)
        assert fresh.source_digest == capability.observation.source_digest
        assert capability.identity.plan.plan_revision == 1
        assert capability.identity.plan_digest.startswith("sha256:")
        provider.release_iteration(capability)
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            revalidate_specification_iteration_admission(capability)
    finally:
        provider.close()


def test_changed_administrative_bytes_still_stale_source(canonical_tree):
    base, root = canonical_tree
    provider = open_provider(base, (root,))
    try:
        capability = provider.admit_iteration(
            SpecificationObserveRequest(),
            "specification:example.spec/phase:foundation/iteration:proof",
        )
        path = base / root / "SPEC.md"
        path.write_text(
            path.read_text().replace("Owner: `fixture`", "Owner: `another`")
        )
        with pytest.raises(SpecificationOperationError, match="source_changed"):
            revalidate_specification_iteration_admission(capability)
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            revalidate_specification_iteration_admission(capability)
    finally:
        provider.close()


def test_capability_cannot_cross_provider_or_be_rebuilt(canonical_tree):
    base, root = canonical_tree
    left = open_provider(base, (root,))
    right = open_provider(base, (root,))
    try:
        capability = left.admit_iteration(
            SpecificationObserveRequest(),
            "specification:example.spec/phase:foundation/iteration:proof",
        )
        with pytest.raises(SpecificationOperationError):
            right.revalidate_iteration(capability)
        with pytest.raises(TypeError):
            copy.copy(capability)
        with pytest.raises(TypeError):
            SpecificationIterationAdmission(
                object(), left, capability.observation, capability.identity
            )
        forged = object.__new__(SpecificationIterationAdmission)
        forged._provider = left
        forged._observation = capability.observation
        forged._identity = capability.identity
        with pytest.raises(SpecificationOperationError):
            revalidate_specification_iteration_admission(forged)
        with pytest.raises(SpecificationOperationError):
            revalidate_specification_iteration_admission(capability.observation)
    finally:
        left.close()
        right.close()


def test_restamped_identity_and_retirement_refuse(canonical_tree):
    base, root = canonical_tree
    provider = open_provider(base, (root,))
    capability = provider.admit_iteration(
        SpecificationObserveRequest(),
        "specification:example.spec/phase:foundation/iteration:proof",
    )
    capability._identity = replace(
        capability.identity, plan=replace(capability.identity.plan, objective="Other")
    )
    with pytest.raises(SpecificationOperationError):
        revalidate_specification_iteration_admission(capability)
    provider.close()
    with pytest.raises(SpecificationOperationError, match="source_provider_closed"):
        revalidate_specification_iteration_admission(capability)


def test_schema_resource_matches_canonical_bytes(schema_bytes):
    import importlib.resources

    carried = (
        importlib.resources.files("aware_specification_fs_sdk_adapter")
        .joinpath("resources/aware-spec-v1.schema.json")
        .read_bytes()
    )
    assert carried == schema_bytes


def test_missing_atomic_primitive_does_not_publish(tmp_path, monkeypatch):
    def unavailable(parent_fd, source, target):
        raise SpecificationOperationError("atomic_draft_publication_unavailable")

    monkeypatch.setattr(provider_module, "rename_no_replace", unavailable)
    provider = open_provider(tmp_path, ("demo",))
    try:
        with pytest.raises(
            SpecificationOperationError, match="atomic_draft_publication_unavailable"
        ):
            provider.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
        assert list(tmp_path.iterdir()) == []
    finally:
        provider.close()


def test_existing_file_and_symlink_are_not_overwritten(tmp_path):
    existing = tmp_path / "file"
    existing.write_text("foreign")
    (tmp_path / "alias").symlink_to(existing)
    for root in ("file", "alias"):
        provider = open_provider(tmp_path, (root,))
        try:
            with pytest.raises(
                SpecificationOperationError, match="draft_target_exists"
            ):
                provider.create_draft(
                    SpecificationDraftRequest(definition(), "author", "intent")
                )
        finally:
            provider.close()
    assert existing.read_text() == "foreign"
    assert (tmp_path / "alias").is_symlink()


def test_wrong_semantic_profile_refuses_before_files(tmp_path):
    provider = open_provider(tmp_path, ("demo",))
    try:
        wrong = replace(definition(), semantic_resolution_digest="sha256:" + "0" * 64)
        with pytest.raises(
            SpecificationOperationError, match="draft_semantic_profile_mismatch"
        ):
            provider.create_draft(SpecificationDraftRequest(wrong, "author", "intent"))
        assert list(tmp_path.iterdir()) == []
    finally:
        provider.close()


def test_parent_substitution_at_validation_refuses_before_publication(
    tmp_path, monkeypatch
):
    parent = tmp_path / "plans"
    parent.mkdir()
    original = provider_module.consume_specification_fs_adaptation

    def change_parent(adapter, result):
        value = original(adapter, result)
        parent.rename(tmp_path / "moved")
        parent.mkdir()
        return value

    monkeypatch.setattr(
        provider_module, "consume_specification_fs_adaptation", change_parent
    )
    provider = open_provider(tmp_path, ("plans/demo",))
    try:
        with pytest.raises(
            SpecificationOperationError, match="source_topology_changed"
        ):
            provider.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
        assert list(parent.iterdir()) == []
        assert list((tmp_path / "moved").iterdir()) == []
    finally:
        provider.close()


def test_modified_staged_metadata_does_not_publish(tmp_path, monkeypatch):
    original = provider_module.stage_files

    def substitute(parent_fd, payload):
        stage = original(parent_fd, payload)
        path = tmp_path / stage / "SPEC.md"
        path.write_text(path.read_text().replace("Owner: author", "Owner: other"))
        return stage

    monkeypatch.setattr(provider_module, "stage_files", substitute)
    provider = open_provider(tmp_path, ("demo",))
    try:
        with pytest.raises(SpecificationOperationError, match="draft_source_mismatch"):
            provider.create_draft(
                SpecificationDraftRequest(definition(), "author", "intent")
            )
        assert list(tmp_path.iterdir()) == []
    finally:
        provider.close()


def test_provider_and_cli_have_no_service_or_ontology_imports():
    import ast

    standard = {
        "__future__",
        "argparse",
        "collections",
        "contextlib",
        "copy",
        "ctypes",
        "dataclasses",
        "errno",
        "hashlib",
        "importlib",
        "json",
        "os",
        "pathlib",
        "secrets",
        "threading",
        "typing",
    }
    neutral = {
        "aware_specification_runtime",
        "aware_specification_fs_source_contract",
        "aware_specification_fs_adapter",
        "aware_specification_sdk",
        "aware_specification_fs_sdk_adapter",
        "aware_protocol_fs_adapter",
        "aware_command_runtime",
    }
    roots = [
        Path(__file__).parents[1] / "aware_specification_fs_sdk_adapter",
        Path(__file__).parents[2] / "cli/aware_specification_cli",
    ]
    imports = set()
    for root in roots:
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in tree.body:
                if isinstance(node, ast.ImportFrom) and node.level == 0:
                    assert not node.module.startswith("aware_protocol")
                elif isinstance(node, ast.Import):
                    assert not any(
                        alias.name.startswith("aware_protocol") for alias in node.names
                    )
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    imports.add(node.module.split(".")[0])
                    if node.module.startswith("aware_protocol"):
                        assert path == roots[1] / "read_commands.py"
    assert imports <= standard | neutral
