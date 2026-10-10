from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from uuid import UUID

import pytest
from aware_code_package_delta_contract import (
    CodeLanguage,
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaContractError,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageDeltaProducerRef,
    CodePackageDeltaProduction,
    CodePackageOutputState,
    CodePackagePathRole,
    FrozenJsonObject,
    code_package_delta_output_digest,
    derive_code_package_output_state,
)

DIGEST = "sha256:" + "1" * 64
PACKAGE_ID = UUID("7bb005d6-9517-5f3c-b380-402e35798617")


def _delta(
    content: str | None = "class Issue:\n    pass\n",
    *,
    kind: CodePackageDeltaKind = CodePackageDeltaKind.create,
    language: CodeLanguage | None = CodeLanguage.python,
    path_role: CodePackagePathRole = CodePackagePathRole.generated_code,
    relative_path: str = "aware_workflow_ontology/issue.py",
) -> CodePackageDelta:
    producer = CodePackageDeltaProducerRef(
        "ontology.object_abi",
        "python.ontology-object-facade.v1",
        "language_renderer",
        FrozenJsonObject.from_mapping({"target_ref": "python:workflow.Issue"}),
    )
    provisional = CodePackageDeltaProduction(
        producer,
        PACKAGE_ID,
        DIGEST,
    )
    after = (
        None if content is None else "sha256:" + sha256(content.encode()).hexdigest()
    )
    before = None if kind is CodePackageDeltaKind.create else DIGEST
    provisional_path = CodePackageDeltaPath(
        relative_path,
        kind,
        content,
        before,
        after,
        None if content is None else len(content.encode()),
        language,
        True,
        path_role,
        provisional,
        FrozenJsonObject.from_mapping({}),
    )
    output = code_package_delta_output_digest(
        package_name="aware-workflow-ontology",
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        source_revision_id=DIGEST,
        production=provisional,
        paths=(provisional_path,),
    )
    production = replace(
        provisional,
        output_digest=output,
        emission_payload=FrozenJsonObject.from_mapping({"delta_root_digest": output}),
    )
    path = replace(provisional_path, production=production)
    return CodePackageDelta(
        "aware-workflow-ontology",
        CodePackageDeltaAuthorityKind.code_package_delta,
        CodePackageDeltaAuthorityKind.code_package_delta.value,
        DIGEST,
        production,
        (path,),
    )


def _bind_before_hash(delta: CodePackageDelta, before_hash: str) -> CodePackageDelta:
    provisional = replace(delta.production, output_digest=None)
    provisional_paths = tuple(
        replace(path, before_hash=before_hash, production=provisional)
        for path in delta.paths
    )
    output = code_package_delta_output_digest(
        package_name=delta.package_name,
        authority=delta.authority,
        authority_kind=delta.authority_kind,
        source_revision_id=delta.source_revision_id,
        production=provisional,
        paths=provisional_paths,
    )
    production = replace(provisional, output_digest=output)
    return replace(
        delta,
        production=production,
        paths=tuple(replace(path, production=production) for path in provisional_paths),
    )


def test_strict_canonical_round_trip_and_output_root() -> None:
    delta = _delta()
    body = delta.to_json_bytes()
    assert CodePackageDelta.from_json_bytes(body) == delta
    assert CodePackageDelta.from_json_bytes(body).to_json_bytes() == body
    assert delta.production.output_digest == code_package_delta_output_digest(
        package_name=delta.package_name,
        authority=delta.authority,
        authority_kind=delta.authority_kind,
        source_revision_id=delta.source_revision_id,
        production=delta.production,
        paths=delta.paths,
    )
    with pytest.raises(CodePackageDeltaContractError, match="noncanonical"):
        CodePackageDelta.from_json_bytes(json.dumps(delta.to_wire()).encode())


def test_complete_code_language_and_path_role_vocabulary_is_public_v1() -> None:
    assert tuple(value.value for value in CodeLanguage) == (
        "aware",
        "dart",
        "python",
        "sql",
    )
    assert tuple(value.value for value in CodePackagePathRole) == (
        "authored_source",
        "generated_code",
        "generated_manifest",
        "generated_metadata",
    )


@pytest.mark.parametrize("language", (*tuple(CodeLanguage), None))
@pytest.mark.parametrize("path_role", tuple(CodePackagePathRole))
def test_all_languages_roles_and_language_absence_round_trip(
    language: CodeLanguage | None,
    path_role: CodePackagePathRole,
) -> None:
    value = _delta(
        "semantic output\n",
        language=language,
        path_role=path_role,
        relative_path=f"generated/{path_role.value}.txt",
    )
    body = value.to_json_bytes()
    decoded = CodePackageDelta.from_json_bytes(body)
    assert decoded == value
    assert decoded.paths[0].language is language
    assert decoded.paths[0].path_role is path_role


def test_language_and_role_substitution_fail_closed_against_output_root() -> None:
    value = _delta()
    for field, substitution in (
        ("language", CodeLanguage.dart),
        ("language", None),
        ("path_role", CodePackagePathRole.generated_manifest),
    ):
        payload = value.to_wire()
        payload["paths"][0][field] = (  # type: ignore[index]
            None if substitution is None else substitution.value
        )
        with pytest.raises(CodePackageDeltaContractError, match="output root"):
            CodePackageDelta.from_json_bytes(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            )


@pytest.mark.parametrize(
    ("field", "substitution"),
    (("language", "neutral"), ("path_role", "sdk_generated")),
)
def test_unknown_language_and_role_fail_closed(field: str, substitution: str) -> None:
    value = _delta()
    payload = value.to_wire()
    payload["paths"][0][field] = substitution  # type: ignore[index]
    with pytest.raises(CodePackageDeltaContractError, match="delta body is invalid"):
        CodePackageDelta.from_json_bytes(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        )


@pytest.mark.parametrize(
    "delta",
    (
        _delta("class Issue:\n    changed = True\n", kind=CodePackageDeltaKind.update),
        _delta(None, kind=CodePackageDeltaKind.delete),
    ),
)
def test_update_and_delete_lifecycles_round_trip(delta: CodePackageDelta) -> None:
    assert CodePackageDelta.from_json_bytes(delta.to_json_bytes()) == delta


@pytest.mark.parametrize(
    "path",
    ("../issue.py", "/tmp/issue.py", "a/./issue.py", "a//issue.py", "a\\issue.py"),
)
def test_path_coordinates_fail_closed(path: str) -> None:
    value = _delta()
    with pytest.raises(CodePackageDeltaContractError, match="relative_path"):
        replace(value.paths[0], relative_path=path)


def test_content_hash_and_lifecycle_substitutions_fail_closed() -> None:
    value = _delta()
    path = value.paths[0]
    with pytest.raises(CodePackageDeltaContractError, match="after_hash"):
        replace(path, content_text="substituted\n")
    with pytest.raises(CodePackageDeltaContractError, match="lifecycle"):
        replace(path, before_hash=DIGEST)
    with pytest.raises(CodePackageDeltaContractError, match="lifecycle"):
        replace(path, kind=CodePackageDeltaKind.delete)
    with pytest.raises(CodePackageDeltaContractError, match="size"):
        replace(path, size_bytes=0)


def test_producer_and_output_substitutions_fail_closed() -> None:
    value = _delta()
    with pytest.raises(CodePackageDeltaContractError, match="normalized text"):
        replace(value.production.producer, provider_key=" ontology.object_abi")
    substituted_production = replace(value.production, output_digest=DIGEST)
    substituted_paths = tuple(
        replace(path, production=substituted_production) for path in value.paths
    )
    with pytest.raises(CodePackageDeltaContractError, match="output root"):
        replace(
            value,
            production=substituted_production,
            paths=substituted_paths,
        )
    with pytest.raises(CodePackageDeltaContractError, match="authority identity"):
        replace(value, authority_kind="foreign")


def test_strict_decode_rejects_direct_and_coherently_restamped_invalid_values() -> None:
    value = _delta()
    payload = value.to_wire()
    payload["paths"][0]["relative_path"] = "../escaped.py"  # type: ignore[index]
    with pytest.raises(CodePackageDeltaContractError, match="relative_path"):
        CodePackageDelta.from_json_bytes(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        )
    payload = value.to_wire()
    payload["paths"][0]["content_text"] = "forged\n"  # type: ignore[index]
    with pytest.raises(CodePackageDeltaContractError, match="after_hash"):
        CodePackageDelta.from_json_bytes(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        )


def test_exact_types_and_module_owned_output_encoding_reject_subclasses() -> None:
    value = _delta()
    path = value.paths[0]

    class ForgedProducer(CodePackageDeltaProducerRef):
        pass

    class ForgedProduction(CodePackageDeltaProduction):
        pass

    class ForgedMetadata(FrozenJsonObject):
        pass

    class ForgedPath(CodePackageDeltaPath):
        def output_wire(self) -> dict[str, object]:
            return {
                "relative_path": "claimed.py",
                "kind": "create",
                "before_hash": None,
                "after_hash": DIGEST,
                "size_bytes": 0,
                "language": "python",
                "is_structural": True,
                "path_role": "generated_code",
            }

    class ForgedDelta(CodePackageDelta):
        pass

    with pytest.raises(CodePackageDeltaContractError, match="exact contract type"):
        ForgedProducer(
            value.production.producer.provider_key,
            value.production.producer.producer_key,
            value.production.producer.producer_kind,
            value.production.producer.provider_payload,
        )
    with pytest.raises(CodePackageDeltaContractError, match="exact contract type"):
        ForgedProduction(
            value.production.producer,
            value.production.input_code_package_id,
            value.production.input_digest,
            value.production.output_digest,
            value.production.emission_payload,
        )
    with pytest.raises(CodePackageDeltaContractError, match="exact contract type"):
        ForgedMetadata(value.paths[0].metadata.entries)
    with pytest.raises(CodePackageDeltaContractError, match="exact contract type"):
        ForgedPath(
            "actual.py",
            path.kind,
            path.content_text,
            path.before_hash,
            path.after_hash,
            path.size_bytes,
            path.language,
            path.is_structural,
            path.path_role,
            path.production,
            path.metadata,
        )
    forged_path = object.__new__(ForgedPath)
    for field in (
        "kind",
        "content_text",
        "before_hash",
        "after_hash",
        "size_bytes",
        "language",
        "is_structural",
        "path_role",
        "production",
        "metadata",
    ):
        object.__setattr__(forged_path, field, getattr(path, field))
    object.__setattr__(forged_path, "relative_path", "actual.py")
    with pytest.raises(CodePackageDeltaContractError, match="production/paths"):
        code_package_delta_output_digest(
            package_name=value.package_name,
            authority=value.authority,
            authority_kind=value.authority_kind,
            source_revision_id=value.source_revision_id,
            production=value.production,
            paths=(forged_path,),
        )
    with pytest.raises(CodePackageDeltaContractError, match="exact contract type"):
        ForgedDelta(
            value.package_name,
            value.authority,
            value.authority_kind,
            value.source_revision_id,
            value.production,
            value.paths,
        )


def test_object_new_shells_are_recursively_revalidated_before_encoding() -> None:
    value = _delta()

    metadata = object.__new__(FrozenJsonObject)
    object.__setattr__(metadata, "entries", [("forged", True)])
    with pytest.raises(CodePackageDeltaContractError, match="immutable"):
        metadata.to_wire()

    producer = object.__new__(CodePackageDeltaProducerRef)
    object.__setattr__(producer, "provider_key", " forged")
    object.__setattr__(producer, "producer_key", "renderer")
    object.__setattr__(producer, "producer_kind", None)
    object.__setattr__(producer, "provider_payload", None)
    with pytest.raises(CodePackageDeltaContractError, match="normalized text"):
        producer.to_wire()

    production = object.__new__(CodePackageDeltaProduction)
    object.__setattr__(production, "producer", object())
    object.__setattr__(production, "input_code_package_id", None)
    object.__setattr__(production, "input_digest", None)
    object.__setattr__(production, "output_digest", None)
    object.__setattr__(production, "emission_payload", None)
    with pytest.raises(CodePackageDeltaContractError, match="producer is invalid"):
        production.to_wire()

    path = object.__new__(CodePackageDeltaPath)
    original_path = value.paths[0]
    for field in (
        "relative_path",
        "kind",
        "content_text",
        "before_hash",
        "after_hash",
        "size_bytes",
        "language",
        "is_structural",
        "path_role",
        "production",
    ):
        object.__setattr__(path, field, getattr(original_path, field))
    object.__setattr__(path, "metadata", object())
    with pytest.raises(CodePackageDeltaContractError, match="metadata is invalid"):
        path.to_wire()

    delta = object.__new__(CodePackageDelta)
    for field in (
        "package_name",
        "authority",
        "authority_kind",
        "source_revision_id",
        "production",
        "contract",
    ):
        object.__setattr__(delta, field, getattr(value, field))
    object.__setattr__(delta, "paths", (object(),))
    with pytest.raises(CodePackageDeltaContractError, match="invalid path"):
        delta.to_json_bytes()


def test_output_state_tracks_genesis_update_delete_without_file_bodies() -> None:
    empty = CodePackageOutputState.empty("aware-workflow-ontology")
    assert empty.paths == ()
    assert empty.source_revision_id is None
    assert CodePackageOutputState.from_json_bytes(empty.to_json_bytes()) == empty

    created = derive_code_package_output_state(empty, _delta())
    assert len(created.paths) == 1
    assert b"class Issue" not in created.to_json_bytes()
    assert CodePackageOutputState.from_json_bytes(created.to_json_bytes()) == created

    updated_delta = _bind_before_hash(
        _delta(
            "class Issue:\n    changed = True\n",
            kind=CodePackageDeltaKind.update,
        ),
        created.paths[0].content_hash,
    )
    updated = derive_code_package_output_state(created, updated_delta)
    assert updated.paths[0].content_hash == updated_delta.paths[0].after_hash

    deleted_delta = _bind_before_hash(
        _delta(None, kind=CodePackageDeltaKind.delete),
        updated.paths[0].content_hash,
    )
    deleted = derive_code_package_output_state(updated, deleted_delta)
    assert deleted.paths == ()
    assert deleted.source_revision_id == deleted_delta.source_revision_id


def test_output_state_rejects_stale_delta_and_strict_wire_substitutions() -> None:
    empty = CodePackageOutputState.empty("aware-workflow-ontology")
    state = derive_code_package_output_state(empty, _delta())
    with pytest.raises(CodePackageDeltaContractError, match="before_hash is stale"):
        derive_code_package_output_state(
            state,
            _delta("changed\n", kind=CodePackageDeltaKind.update),
        )

    payload = state.to_wire()
    payload["paths"][0]["size_bytes"] = True  # type: ignore[index]
    with pytest.raises(CodePackageDeltaContractError, match="size_bytes"):
        CodePackageOutputState.from_json_bytes(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        )

    with pytest.raises(CodePackageDeltaContractError, match="digest"):
        replace(state, source_revision_id="sha256:" + "2" * 64)
