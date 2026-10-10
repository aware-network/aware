"""Real neutral source lowering and fresh source capture, not publication authority.

Fixtures are deliberately unregistered. No generated SDK, Service, owner permit,
physical writer or installed customer operation is selected by these proofs.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import test_workspace_publication_contract_freeze as contract
import tree_sitter._binding as parser_binding
import tree_sitter_aware._binding as grammar_binding
from tree_sitter_aware.neutral_ir import (
    NeutralAwareSyntaxError,
    parse_neutral_aware_source,
)
from tree_sitter_aware.ontology_meaning import meaning_value_to_json
from tree_sitter_aware.ontology_meaning_resolver import (
    OntologyMeaningPackageInput,
    resolve_ontology_meaning,
)

ROOT = contract.ROOT
FIXTURES = Path(__file__).parent / "fixtures"
CAPTURE = ROOT / "docs/reports/workspace-publication-source-capture-20261009.json"
VALUE_ROOTS = (
    "WorkspaceRepositoryCommitRequest",
    "WorkspaceRepositoryPublicationBinding",
    "WorkspaceRepositoryPlanVerificationRequest",
    "WorkspaceRepositoryPlanVerification",
    "WorkspaceRepositoryAttemptObserveRequest",
    "WorkspaceRepositoryAttemptObservation",
    "WorkspaceRepositoryLockReleaseObservation",
    "WorkspacePublicationCleanupObservation",
    "WorkspacePublicationPlanObservation",
    "WorkspaceRepositoryPhysicalEffect",
    "WorkspaceRepositoryWriterObservation",
    "WorkspaceRepositoryCommitResult",
    "WorkspaceRepositoryPublicationError",
    "IssueRepositoryPublicationBinding",
    "IssueRepositoryPublicationRequest",
    "IssueRepositoryPublicationEnrollmentRequest",
)
STATE_TYPES = {
    "publication_state": "WorkspacePublicationState",
    "reference_update": "WorkspaceReferenceUpdateState",
    "index_projection": "WorkspaceIndexProjectionState",
    "cleanup_state": "WorkspaceCleanupState",
}
STATE_MEMBERS = {
    "WorkspacePublicationState": ("not_published", "published", "unknown"),
    "WorkspaceReferenceUpdateState": (
        "not_run",
        "cas_applied",
        "cas_failed",
        "unknown",
    ),
    "WorkspaceIndexProjectionState": (
        "not_run",
        "applied",
        "pending",
        "failed",
        "unknown",
    ),
    "WorkspaceCleanupState": ("not_attempted", "completed", "incomplete", "unknown"),
    "WorkspacePhysicalEffectKind": (
        "repository_reference_update",
        "shared_index_projection",
        "transaction_index_write",
        "transaction_index_cleanup",
        "recovery_record_write",
        "recovery_record_cleanup",
        "descriptor_release",
        "source_compensation",
    ),
    "WorkspacePhysicalEffectState": ("not_attempted", "applied", "failed", "unknown"),
    "WorkspacePublicationFailurePhase": (
        "request",
        "admission",
        "physical",
        "finish",
        "result",
        "cleanup",
    ),
}
SOURCE_ROOTS = (
    contract.SDK.parent,
    contract.WORKSPACE / "sdks/workspace/aware",
    contract.WORKSPACE / "libs/workspace_runtime",
    contract.WORKSPACE / "libs/workspace_operator/python",
    contract.WORKFLOW / "sdks/issue/python",
    contract.WORKFLOW / "sdks/issue/aware",
    contract.WORKFLOW / "sdks/issue/filesystem_adapter/python",
    contract.WORKFLOW / "libs/issue_runtime",
    contract.WORKFLOW / "libs/issue_operational_runtime",
    Path("workspaces/aware_kernel/languages/aware/grammar/tree_sitter"),
    Path(
        "workspaces/aware_kernel/languages/aware/grammar/parsed_document_contract/python"
    ),
)
QUALIFICATION_PATHS = (
    Path(__file__).relative_to(ROOT),
    *(
        path.relative_to(ROOT)
        for path in sorted(FIXTURES.glob("*_publication_values.aware"))
    ),
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def _source_paths() -> tuple[str, ...]:
    excluded = {path.as_posix() for path in QUALIFICATION_PATHS}
    paths = set(
        _git(
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            *(path.as_posix() for path in SOURCE_ROOTS),
        ).splitlines()
    )
    paths.update(path.as_posix() for path in contract.PINS)
    paths.add((contract.WORKFLOW / "aware.module.toml").as_posix())
    return tuple(sorted(paths - excluded))


def capture_sources() -> dict[str, object]:
    """Complete named roots, twice observed at one HEAD; not an activation receipt."""
    head = _git("rev-parse", "HEAD").strip()
    paths = _source_paths()
    files = {
        path: {
            "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            "mode": (ROOT / path).stat().st_mode & 0o777,
        }
        for path in paths
    }
    for path, observation in files.items():
        assert (
            hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            == observation["sha256"]
        )
        assert (ROOT / path).stat().st_mode & 0o777 == observation["mode"]
    assert _source_paths() == paths, "Source membership changed during capture"
    assert _git("rev-parse", "HEAD").strip() == head, "HEAD changed during capture"
    return {
        "purpose": "publication-pre-extraction-source-capture",
        "activation_authority": False,
        "captured_head": head,
        "source_roots": [path.as_posix() for path in SOURCE_ROOTS],
        "excluded_qualification_paths": [
            path.as_posix() for path in QUALIFICATION_PATHS
        ],
        "source_files": files,
        "dirty_source_paths": _git("status", "--porcelain", "--", *paths).splitlines(),
        "historical_contract_inventory_sha256": hashlib.sha256(
            (ROOT / contract.INPUTS).read_bytes()
        ).hexdigest(),
        "qualified_value_closure": {
            prefix: {
                "source_sha256": hashlib.sha256(_source(prefix).encode()).hexdigest(),
                "meaning_sha256": _lower(prefix).canonical_sha256,
                "entry_count": len(_lower(prefix).entries),
            }
            for prefix in ("workspace", "issue")
        },
        "observed_parser_artifacts": {
            name: {
                "path": str(Path(module.__file__).relative_to(ROOT)),
                "sha256": hashlib.sha256(
                    Path(module.__file__).read_bytes()
                ).hexdigest(),
            }
            for name, module in (
                ("grammar", grammar_binding),
                ("tree_sitter", parser_binding),
            )
        },
    }


def _source(prefix: str) -> str:
    return (FIXTURES / f"{prefix}_publication_values.aware").read_text(encoding="utf-8")


def _lower(prefix: str, source: str | None = None):
    # Stable virtual coordinates prevent checkout location from changing meaning.
    path = f"/qualification/{prefix}/values.aware"
    document = parse_neutral_aware_source(
        _source(prefix) if source is None else source, source_path=path
    )
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=f"{prefix}-publication-values",
                fqn_prefix=f"{prefix}_publication",
                sources_root=f"/qualification/{prefix}",
                dependencies=(),
                documents=(document,),
                namespace_by_source_path=((path, ""),),
            ),
        ),
        selected_package_names=frozenset({f"{prefix}-publication-values"}),
    )


def _aware_type(node: ast.expr, owner: str, field: str) -> str:
    """Expected owner annotation mapping; does not parse/lower the authored body."""
    spelling = ast.unparse(node)
    if spelling == "tuple[int, int]":
        return "WorkspaceFileIdentity"
    if spelling == "list[list[str]]":
        return "WorkspaceGitCommand[]"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        assert isinstance(node.right, ast.Constant) and node.right.value is None
        return _aware_type(node.left, owner, field) + "?"
    if isinstance(node, ast.Name):
        if node.id == "str" and owner.startswith("Workspace"):
            if field in STATE_TYPES:
                return STATE_TYPES[field]
            if owner == "WorkspaceRepositoryPhysicalEffect" and field in {
                "kind",
                "state",
            }:
                return "WorkspacePhysicalEffect" + field.title()
            if owner == "WorkspaceRepositoryPublicationError" and field == "phase":
                return "WorkspacePublicationFailurePhase"
        return {"str": "String", "int": "Int", "bool": "Bool"}.get(node.id, node.id)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        if node.value.id == "Literal":
            return owner + "".join(part.title() for part in field.split("_"))
        if node.value.id == "list":
            return _aware_type(node.slice, owner, field) + "[]"
        if node.value.id == "tuple":
            assert isinstance(node.slice, ast.Tuple)
            assert isinstance(node.slice.elts[1], ast.Constant)
            assert node.slice.elts[1].value is Ellipsis
            return _aware_type(node.slice.elts[0], owner, field) + "[]"
    raise AssertionError(f"Unqualified annotation {spelling}")


@pytest.mark.parametrize("name", VALUE_ROOTS)
def test_every_declared_value_root_preserves_fields_order_types_and_nullability(
    name: str,
):
    prefix = "issue" if name.startswith("Issue") else "workspace"
    meaning = _lower(prefix)
    symbol = next(
        entry
        for entry in meaning.entries
        if entry.kind == "symbol" and entry.fqn == f"{prefix}_publication.{name}"
    )
    assert meaning_value_to_json(symbol.payload)["inline_value"] is True
    members = {
        entry.fqn.rsplit(".", 1)[1]: meaning_value_to_json(entry.payload)
        for entry in meaning.entries
        if entry.kind == "member" and entry.fqn.rsplit(".", 1)[0] == symbol.fqn
    }
    fields = [
        field
        for field in contract._class(name).body
        if isinstance(field, ast.AnnAssign)
    ]
    assert set(members) == {field.target.id for field in fields}
    for position, field in enumerate(fields):
        payload = members[field.target.id]
        expected = _aware_type(field.annotation, name, field.target.id)
        assert payload["position"] == position
        assert payload["type_expression"] == expected
        assert payload["nullable"] == expected.endswith("?")
        assert payload["collection"] == expected.removesuffix("?").endswith("[]")
        assert payload["identity_key"] is False
        if not payload["primitive"]:
            assert payload["target_fqn"] is not None
            assert payload["target_symbol_kind"] in {"class_def", "enum_def"}


@pytest.mark.parametrize("prefix", ("workspace", "issue"))
def test_real_lowering_is_deterministic_and_source_hashes_are_byte_exact(prefix: str):
    first = _lower(prefix)
    second = _lower(prefix)
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.canonical_sha256 == second.canonical_sha256
    expected_digest = hashlib.sha256(_source(prefix).encode()).hexdigest()
    assert {
        pin.source_sha256 for entry in first.entries for pin in entry.provenance
    } == {expected_digest}


def test_finite_enums_preserve_every_literal_in_the_owner_contract():
    for name in VALUE_ROOTS:
        meaning = _lower("issue" if name.startswith("Issue") else "workspace")
        for field in contract._class(name).body:
            if not isinstance(field, ast.AnnAssign) or not isinstance(
                field.annotation, ast.Subscript
            ):
                continue
            annotation = field.annotation
            if (
                not isinstance(annotation.value, ast.Name)
                or annotation.value.id != "Literal"
            ):
                continue
            enum = _aware_type(annotation, name, field.target.id)
            values = [
                entry.fqn.rsplit(".", 1)[1]
                for entry in meaning.entries
                if entry.kind == "enum_option"
                and entry.fqn.rsplit(".", 1)[0].endswith("." + enum)
            ]
            assert set(values) == {item.value for item in annotation.slice.elts}


@pytest.mark.parametrize("name", tuple(STATE_MEMBERS))
def test_public_effect_and_failure_states_lower_as_finite_enums(name: str):
    entries = sorted(
        (
            entry
            for entry in _lower("workspace").entries
            if entry.kind == "enum_option"
            and entry.fqn.rsplit(".", 1)[0] == f"workspace_publication.{name}"
        ),
        key=lambda entry: meaning_value_to_json(entry.payload)["position"],
    )
    assert (
        tuple(entry.fqn.rsplit(".", 1)[1] for entry in entries) == STATE_MEMBERS[name]
    )


def test_opaque_authority_handles_have_no_authored_value_constructor():
    symbols = {
        entry.fqn.rsplit(".", 1)[1]
        for prefix in ("workspace", "issue")
        for entry in _lower(prefix).entries
        if entry.kind == "symbol"
    }
    assert not symbols & {
        "WorkspaceRepositoryCommitPlan",
        "WorkspacePublicationCapture",
        "WorkspacePublicationWorkAdmission",
        "WorkspacePublicationExecutionClaim",
        "WorkspacePublicationPhysicalTransaction",
        "IssueRepositoryPublicationAdmission",
        "IssueRepositoryPublicationEnrollment",
        "IssueRepositoryPublicationLease",
        "IssueCloseAdmission",
    }


def test_identity_pairs_and_command_log_have_explicit_lossless_value_shapes():
    meaning = _lower("workspace")
    members = {
        entry.fqn.removeprefix("workspace_publication."): meaning_value_to_json(
            entry.payload
        )
        for entry in meaning.entries
        if entry.kind == "member"
    }
    assert members["WorkspaceFileIdentity.device"]["type_expression"] == "Int"
    assert members["WorkspaceFileIdentity.device"]["position"] == 0
    assert members["WorkspaceFileIdentity.inode"]["type_expression"] == "Int"
    assert members["WorkspaceFileIdentity.inode"]["position"] == 1
    assert members["WorkspaceGitCommand.arguments"]["type_expression"] == "String[]"
    assert (
        members["WorkspaceRepositoryWriterObservation.command_log"]["type_expression"]
        == "WorkspaceGitCommand[]"
    )
    assert {key for key in members if key.startswith("WorkspaceFileIdentity.")} == {
        "WorkspaceFileIdentity.device",
        "WorkspaceFileIdentity.inode",
    }


def test_fresh_parser_lowerer_imports_do_not_select_sdk_service_orm_or_permits():
    script = r"""
import json
import sys
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
from tree_sitter_aware.ontology_meaning_resolver import OntologyMeaningPackageInput, resolve_ontology_meaning
source = sys.stdin.read()
parsed = parse_neutral_aware_source(source, source_path="/qualification/workspace/values.aware")
meaning = resolve_ontology_meaning((OntologyMeaningPackageInput(
    package_name="workspace-publication-values", fqn_prefix="workspace_publication",
    sources_root="/qualification/workspace", dependencies=(), documents=(parsed,),
    namespace_by_source_path=((parsed.source_path, ""),),
),), selected_package_names=frozenset({"workspace-publication-values"}))
forbidden = sorted(name for name in sys.modules if name.startswith("aware_") and
    ("sdk" in name or "service" in name or "orm" in name or "issue" in name or "workspace" in name))
print(json.dumps({"meaning_sha256": meaning.canonical_sha256, "forbidden_imports": forbidden}))
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=ROOT,
        input=_source("workspace"),
        capture_output=True,
        text=True,
        check=True,
    )
    observed = json.loads(result.stdout)
    assert observed["forbidden_imports"] == []
    assert observed["meaning_sha256"] == _lower("workspace").canonical_sha256


@pytest.mark.parametrize("prefix", ("workspace", "issue"))
def test_dangling_type_refs_fail_real_resolution(prefix: str):
    source = _source(prefix).replace(
        "repository_ref String", "repository_ref AbsentOwnerType", 1
    )
    with pytest.raises(
        ValueError, match="AbsentOwnerType.*does not resolve exactly once"
    ):
        _lower(prefix, source)


def test_invalid_authored_syntax_fails_closed():
    with pytest.raises(NeutralAwareSyntaxError):
        _lower("workspace", "class Broken {")


def test_source_capture_remains_current_without_repinning_historical_inputs():
    recorded = json.loads(CAPTURE.read_text(encoding="utf-8"))
    current = capture_sources()
    # Our own later publication changes HEAD, not captured source currentness.
    current["captured_head"] = recorded["captured_head"]
    assert current == recorded
    assert recorded["dirty_source_paths"] == []
    assert recorded["activation_authority"] is False


def test_capture_includes_all_runtime_namespaces_and_non_python_resources():
    files = json.loads(CAPTURE.read_text(encoding="utf-8"))["source_files"]
    root = (contract.WORKSPACE / "libs/workspace_runtime").as_posix()
    for namespace in (
        "aware_workspace_runtime",
        "aware_workspace_command",
        "aware_workspace_materialize_transport",
    ):
        assert any(path.startswith(f"{root}/{namespace}/") for path in files)
    assert f"{root}/pyproject.toml" in files
    assert any(path.endswith(".json") for path in files)


if __name__ == "__main__":
    print(json.dumps(capture_sources(), indent=2, sort_keys=True))
