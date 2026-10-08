import hashlib
import importlib.util
import os
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from aware_specification_fs_adapter.observation import (
    mount_namespace_identity,
    validate_source_base,
)
from aware_specification_fs_sdk_adapter import (
    SOURCE_EVIDENCE_CONTRACT,
    SpecificationIterationAdmission,
    revalidate_specification_iteration_source_evidence,
)
from aware_specification_fs_sdk_adapter import provider as provider_module
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationObservation,
    SpecificationObserveRequest,
    SpecificationOperationError,
)

_spec = importlib.util.spec_from_file_location(
    "spec_source_evidence_fixtures", Path(__file__).with_name("test_provider.py")
)
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
canonical_tree = _fixtures.canonical_tree
open_provider = _fixtures.open_provider
ITERATION = "specification:example.spec/phase:foundation/iteration:proof"


def test_evidence_correlates_one_real_adaptation_and_exact_bytes(
    canonical_tree, monkeypatch
):
    base, root = canonical_tree
    provider = open_provider(base, (root,))
    try:
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        adaptations = []
        original = provider_module.adapt_specification_fs_roots

        def observe(*args):
            result = original(*args)
            adaptations.append(result)
            return result

        monkeypatch.setattr(provider_module, "adapt_specification_fs_roots", observe)
        evidence = revalidate_specification_iteration_source_evidence(capability)
        assert len(adaptations) == 1
        assert evidence.contract == SOURCE_EVIDENCE_CONTRACT
        assert evidence.closures is adaptations[0].lowering.closures
        assert evidence.observation.snapshot is adaptations[0].lowering.snapshot
        assert evidence.identity == capability.identity
        assert evidence.observation == capability.observation
        fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY)
        try:
            assert evidence.source_base_identity == validate_source_base(fd)
        finally:
            os.close(fd)
        assert evidence.namespace_identity == mount_namespace_identity()
        closure = evidence.closures[0]
        assert closure.spec_root == root
        for member in closure.members:
            body = (base / root / member.relative_path).read_bytes()
            assert body == member.canonical_body.encode("utf-8")
            assert len(body) == member.size_bytes
            assert "sha256:" + hashlib.sha256(body).hexdigest() == member.body_digest
        with pytest.raises(AttributeError):
            evidence.closures = ()
    finally:
        provider.close()


def test_custom_root_is_exposed_without_fixed_repository_layout(canonical_tree):
    base, root = canonical_tree
    custom = "customer/contracts/example"
    (base / custom).parent.mkdir(parents=True)
    (base / root).rename(base / custom)
    provider = open_provider(base, (custom,))
    try:
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        evidence = revalidate_specification_iteration_source_evidence(capability)
        assert evidence.closures[0].spec_root == custom
        assert evidence.identity.iteration_ref == ITERATION
    finally:
        provider.close()


def test_evidence_contains_all_roots_and_other_root_drift_retires(canonical_tree):
    base, root = canonical_tree
    definition = _fixtures.definition()
    phase = definition.phases[0]
    second = replace(
        definition,
        key="second.spec",
        phases=(
            replace(
                phase,
                gate=replace(
                    phase.gate,
                    invariant_refs=("specification:second.spec/invariant:safe",),
                ),
            ),
        ),
    )
    writer = open_provider(base, ("second",))
    try:
        writer.create_draft(SpecificationDraftRequest(second, "fixture", "intent"))
    finally:
        writer.close()
    roots = tuple(sorted((root, "second")))
    provider = open_provider(base, roots)
    try:
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        evidence = revalidate_specification_iteration_source_evidence(capability)
        assert tuple(c.spec_root for c in evidence.closures) == roots
        assert len(evidence.observation.snapshot.definitions) == 2
        path = base / "second/SPEC.md"
        path.write_text(path.read_text().replace("Owner: fixture", "Owner: other"))
        with pytest.raises(SpecificationOperationError, match="source_changed"):
            revalidate_specification_iteration_source_evidence(capability)
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            revalidate_specification_iteration_source_evidence(capability)
    finally:
        provider.close()


@pytest.mark.parametrize(
    "replacement", ["object", "observation", "evidence", "dto", "forged"]
)
def test_source_evidence_does_not_replace_retained_admission(
    canonical_tree, replacement
):
    base, root = canonical_tree
    provider = open_provider(base, (root,))
    try:
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        evidence = revalidate_specification_iteration_source_evidence(capability)
        forged = object.__new__(SpecificationIterationAdmission)
        forged._provider = provider
        forged._observation = capability.observation
        forged._identity = capability.identity
        value = {
            "object": object(),
            "observation": capability.observation,
            "evidence": evidence,
            "dto": {
                "iteration_ref": ITERATION,
                "source_digest": evidence.observation.source_digest,
            },
            "forged": forged,
        }[replacement]
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            revalidate_specification_iteration_source_evidence(value)
    finally:
        provider.close()


def test_cross_provider_release_and_close_refuse(canonical_tree):
    base, root = canonical_tree
    left = open_provider(base, (root,))
    right = open_provider(base, (root,))
    try:
        capability = left.admit_iteration(SpecificationObserveRequest(), ITERATION)
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            right.revalidate_iteration_source_evidence(capability)
        left.release_iteration(capability)
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            revalidate_specification_iteration_source_evidence(capability)
        current = left.admit_iteration(SpecificationObserveRequest(), ITERATION)
        left.close()
        with pytest.raises(SpecificationOperationError, match="source_provider_closed"):
            revalidate_specification_iteration_source_evidence(current)
    finally:
        left.close()
        right.close()


def test_namespace_change_during_observation_refuses_and_retires(
    canonical_tree, monkeypatch
):
    base, root = canonical_tree
    provider = open_provider(base, (root,))
    try:
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        original_consume = provider_module.consume_specification_fs_adaptation
        namespace = mount_namespace_identity()

        def change_after_observation(adapter, result):
            value = original_consume(adapter, result)
            monkeypatch.setattr(
                provider_module,
                "mount_namespace_identity",
                lambda: (namespace[0], namespace[1], namespace[2] + 1),
            )
            return value

        monkeypatch.setattr(
            provider_module,
            "consume_specification_fs_adaptation",
            change_after_observation,
        )
        with pytest.raises(
            SpecificationOperationError, match="source_topology_changed"
        ):
            revalidate_specification_iteration_source_evidence(capability)
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            revalidate_specification_iteration_source_evidence(capability)
    finally:
        provider.close()


@pytest.mark.parametrize("change", ["digest", "empty", "list", "bool", "identity"])
def test_structural_evidence_mismatch_is_typed(canonical_tree, change):
    base, root = canonical_tree
    provider = open_provider(base, (root,))
    try:
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        evidence = revalidate_specification_iteration_source_evidence(capability)
        changes = {
            "digest": {
                "observation": replace(
                    evidence.observation, source_digest="sha256:" + "0" * 64
                )
            },
            "empty": {"closures": ()},
            "list": {"closures": list(evidence.closures)},
            "bool": {"source_base_identity": (True, 0, 0)},
            "identity": {
                "identity": replace(
                    evidence.identity,
                    plan=replace(evidence.identity.plan, objective="Other"),
                )
            },
        }
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_source_evidence"
        ):
            replace(evidence, **changes[change])
    finally:
        provider.close()


def test_dirty_work_preserved_and_foreign_base_identity_distinct(
    canonical_tree, tmp_path
):
    base, root = canonical_tree
    dirty = base / "foreign.txt"
    dirty.write_bytes(b"keep this work\n")
    provider = open_provider(base, (root,))
    other = tmp_path / "different-source-base"
    other.mkdir()
    try:
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        evidence = revalidate_specification_iteration_source_evidence(capability)
        fd = os.open(other, os.O_RDONLY | os.O_DIRECTORY)
        try:
            assert evidence.source_base_identity != validate_source_base(fd)
        finally:
            os.close(fd)
        assert dirty.read_bytes() == b"keep this work\n"
        assert not (base / ".git").exists()
        assert evidence.observation.authority_mode == "filesystem"
        assert evidence.observation.observation_grade == "local_structural_observation"
    finally:
        provider.close()


def test_identical_bytes_do_not_identify_the_source_base(canonical_tree, tmp_path):
    base, root = canonical_tree
    clone = tmp_path / "clone"
    shutil.copytree(base, clone)
    left = open_provider(base, (root,))
    right = open_provider(clone, (root,))
    try:
        left_cap = left.admit_iteration(SpecificationObserveRequest(), ITERATION)
        right_cap = right.admit_iteration(SpecificationObserveRequest(), ITERATION)
        first = revalidate_specification_iteration_source_evidence(left_cap)
        second = revalidate_specification_iteration_source_evidence(right_cap)
        assert first.observation.source_digest == second.observation.source_digest
        assert first.identity == second.identity
        assert first.source_base_identity != second.source_base_identity
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            left.revalidate_iteration_source_evidence(right_cap)
    finally:
        left.close()
        right.close()


@pytest.mark.parametrize("field", ["observation", "identity"])
def test_incomplete_retained_values_refuse_and_retire(canonical_tree, field):
    base, root = canonical_tree
    provider = open_provider(base, (root,))
    try:
        capability = provider.admit_iteration(SpecificationObserveRequest(), ITERATION)
        value_type = (
            SpecificationObservation
            if field == "observation"
            else type(capability.identity)
        )
        setattr(capability, "_" + field, object.__new__(value_type))
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            revalidate_specification_iteration_source_evidence(capability)
        with pytest.raises(
            SpecificationOperationError, match="invalid_iteration_admission"
        ):
            revalidate_specification_iteration_source_evidence(capability)
    finally:
        provider.close()
