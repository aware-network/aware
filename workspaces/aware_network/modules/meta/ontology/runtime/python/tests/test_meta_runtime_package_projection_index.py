# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from aware_meta.runtime import package_index as package_index_module

from aware_meta.runtime.package_index import (
    META_RUNTIME_SEMANTIC_OBJECT_SOURCE_REF_STORAGE,
    META_RUNTIME_SEMANTIC_OBJECT_PAYLOAD_STORAGE,
    MetaRuntimeSemanticObjectIndexEntry,
    MetaRuntimePackageProjectionIndex,
    MetaRuntimePackageIndexEntry,
    MetaRuntimePackageIndexPatch,
    MetaRuntimeProjectionIndexEntry,
    _semantic_object_entries_from_payload,
    _semantic_object_entry_payload,
    _write_package_projection_index,
    _with_preserved_compatible_index_entries,
    apply_meta_runtime_package_index_patch,
    build_meta_runtime_package_projection_index,
    load_meta_runtime_package_projection_index,
    load_meta_runtime_package_projection_lookup,
    meta_runtime_package_projection_index_path,
    meta_runtime_package_projection_lookup_path,
)


def test_meta_runtime_package_projection_index_bootstraps_from_contract_catalog(
    tmp_path: Path,
) -> None:
    package_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )

    index = build_meta_runtime_package_projection_index(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(package_entry,),
        required_projection_names=("CodePackage",),
    )

    assert index.package_names_for_projection_names(("CodePackage",)) == (
        "code-ontology",
    )
    projection = index.projections_by_name["CodePackage"]
    assert projection.evidence_source == "semantic_contract_projection_catalog"
    assert projection.projection_hash is None
    assert index.packages_by_name["code-ontology"].projection_names == ("CodePackage",)


def test_package_catalog_signature_excludes_materialized_projection_outputs(
    tmp_path: Path,
) -> None:
    base = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=(),
    )
    materialized = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )

    assert package_index_module._package_catalog_signature(
        repo_root=tmp_path,
        package_entries=(base,),
    ) == package_index_module._package_catalog_signature(
        repo_root=tmp_path,
        package_entries=(materialized,),
    )


def test_meta_runtime_package_projection_index_rejects_contract_owner_conflict(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="Conflicting Meta runtime projection index entries",
    ):
        build_meta_runtime_package_projection_index(
            repo_root=tmp_path,
            aware_root=tmp_path,
            package_entries=(
                _package_entry(
                    tmp_path=tmp_path,
                    package_name="code-ontology",
                    fqn_prefix="aware_code",
                    projection_names=("CodePackage",),
                ),
                _package_entry(
                    tmp_path=tmp_path,
                    package_name="other-ontology",
                    fqn_prefix="aware_other",
                    projection_names=("CodePackage",),
                ),
            ),
            required_projection_names=("CodePackage",),
        )


def test_meta_runtime_package_projection_index_prefers_materialized_identity(
    tmp_path: Path,
) -> None:
    package_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )
    index = build_meta_runtime_package_projection_index(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(package_entry,),
        required_projection_names=("CodePackage",),
    )

    patched = apply_meta_runtime_package_index_patch(
        index=index,
        patch=MetaRuntimePackageIndexPatch(
            projection_upserts=(
                MetaRuntimeProjectionIndexEntry(
                    projection_name="CodePackage",
                    package_name="code-ontology",
                    fqn_prefix="aware_code",
                    manifest_path=package_entry.manifest_path,
                    projection_hash="materialized-code-package-hash",
                    evidence_source="materialization_index_receipt",
                ),
            ),
        ),
    )

    projection = patched.projections_by_name["CodePackage"]
    assert projection.evidence_source == "materialization_index_receipt"
    assert projection.projection_hash == "materialized-code-package-hash"


def test_meta_runtime_package_projection_index_skips_stale_preserved_owner(
    tmp_path: Path,
) -> None:
    identity_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="identity-ontology",
        fqn_prefix="aware_identity",
        projection_names=("Identity",),
    )
    attention_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="attention-ontology",
        fqn_prefix="aware_attention",
        projection_names=("ActorFocusRequest",),
    )
    current_index = MetaRuntimePackageProjectionIndex(
        catalog_signature="current",
        packages_by_name={
            "identity-ontology": identity_entry,
            "attention-ontology": attention_entry,
        },
        projections_by_name={
            "ActorFocusRequest": MetaRuntimeProjectionIndexEntry(
                projection_name="ActorFocusRequest",
                package_name="attention-ontology",
                fqn_prefix="aware_attention",
                manifest_path=attention_entry.manifest_path,
                projection_hash="attention-current-hash",
            )
        },
    )
    previous_index = MetaRuntimePackageProjectionIndex(
        catalog_signature="previous",
        packages_by_name={
            "identity-ontology": _package_entry(
                tmp_path=tmp_path,
                package_name="identity-ontology",
                fqn_prefix="aware_identity",
                projection_names=("ActorFocusRequest", "Identity"),
            ),
        },
        projections_by_name={
            "ActorFocusRequest": MetaRuntimeProjectionIndexEntry(
                projection_name="ActorFocusRequest",
                package_name="identity-ontology",
                fqn_prefix="aware_identity",
                manifest_path=identity_entry.manifest_path,
                projection_hash="identity-stale-hash",
            )
        },
    )

    merged = _with_preserved_compatible_index_entries(
        index=current_index,
        previous_index=previous_index,
        package_entries=(identity_entry, attention_entry),
    )

    assert (
        merged.projections_by_name["ActorFocusRequest"].package_name
        == "attention-ontology"
    )
    assert (
        "ActorFocusRequest"
        not in merged.packages_by_name["identity-ontology"].projection_names
    )


def test_meta_runtime_semantic_object_payload_serializes_compact_baseline_fields(
    tmp_path: Path,
) -> None:
    object_id = uuid4()
    entry = MetaRuntimeSemanticObjectIndexEntry(
        semantic_key="aware_code.CodePackage/name",
        object_kind="attribute",
        package_name="code-ontology",
        fqn_prefix="aware_code",
        manifest_path=tmp_path / "modules" / "code" / "aware.ontology.toml",
        object_id=object_id,
        attribute_name="name",
        source_refs=("modules/code/structure/ontology/aware/code.aware",),
        payload={
            "attribute_signature": {"name": "name", "value_mode": "primitive"},
            "current": {"large": "x" * 1000},
            "current_payload": {"large": "y" * 1000},
            "payload": {"legacy_raw_mirror": True},
            "semantic_fingerprint": "fingerprint-1",
        },
    )

    payload = _semantic_object_entry_payload(entry)

    compact_payload = payload["payload"]
    assert compact_payload == {
        "attribute_signature": {"name": "name", "value_mode": "primitive"},
        "semantic_fingerprint": "fingerprint-1",
    }
    assert payload["source_refs"] == [
        "modules/code/structure/ontology/aware/code.aware"
    ]
    assert "current" not in compact_payload
    assert "current_payload" not in compact_payload
    assert "source_refs" not in compact_payload


def test_meta_runtime_semantic_object_payload_round_trips_compact_fields(
    tmp_path: Path,
) -> None:
    entry = MetaRuntimeSemanticObjectIndexEntry(
        semantic_key="aware_code.CodePackage/name",
        object_kind="attribute",
        package_name="code-ontology",
        fqn_prefix="aware_code",
        manifest_path=tmp_path / "modules" / "code" / "aware.ontology.toml",
        attribute_name="name",
        payload={
            "attribute_signature": {"name": "name"},
            "semantic_fingerprint": "fingerprint-1",
        },
    )
    serialized = _semantic_object_entry_payload(entry)

    entries = _semantic_object_entries_from_payload([serialized])

    loaded = entries["aware_code.CodePackage/name"]
    assert loaded.attribute_name == "name"
    assert loaded.payload == {
        "attribute_signature": {"name": "name"},
        "semantic_fingerprint": "fingerprint-1",
    }


def test_meta_runtime_semantic_object_payload_storage_contract_is_compact() -> None:
    assert META_RUNTIME_SEMANTIC_OBJECT_PAYLOAD_STORAGE == "compact_baseline_fields"


def test_meta_runtime_semantic_object_source_refs_round_trip_through_catalog(
    tmp_path: Path,
) -> None:
    source_refs = (
        "modules/code/structure/ontology/aware/code.aware",
        "modules/code/structure/ontology/aware/code_section.aware",
    )
    package_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )
    index = MetaRuntimePackageProjectionIndex(
        catalog_signature="catalog",
        packages_by_name={"code-ontology": package_entry},
        semantic_objects_by_key={
            "aware_code.CodePackage": MetaRuntimeSemanticObjectIndexEntry(
                semantic_key="aware_code.CodePackage",
                object_kind="class",
                package_name="code-ontology",
                fqn_prefix="aware_code",
                manifest_path=package_entry.manifest_path,
                source_refs=source_refs,
            ),
            "aware_code.CodeSection": MetaRuntimeSemanticObjectIndexEntry(
                semantic_key="aware_code.CodeSection",
                object_kind="class",
                package_name="code-ontology",
                fqn_prefix="aware_code",
                manifest_path=package_entry.manifest_path,
                source_refs=source_refs,
            ),
        },
    )

    _write_package_projection_index(aware_root=tmp_path, index=index)

    raw_payload = json.loads(
        meta_runtime_package_projection_index_path(aware_root=tmp_path).read_text(
            encoding="utf-8",
        )
    )
    assert (
        raw_payload["semantic_object_source_ref_storage"]
        == META_RUNTIME_SEMANTIC_OBJECT_SOURCE_REF_STORAGE
    )
    assert len(raw_payload["source_ref_sets"]) == 1
    rows = raw_payload["semantic_objects"]
    assert all("source_ref_set_key" in row for row in rows)
    assert all("source_refs" not in row for row in rows)

    loaded = load_meta_runtime_package_projection_index(aware_root=tmp_path)

    assert loaded is not None
    assert {entry.source_refs for entry in loaded.semantic_objects_by_key.values()} == {
        source_refs
    }


def test_meta_runtime_package_projection_index_reuses_exact_file_witness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )
    index = MetaRuntimePackageProjectionIndex(
        catalog_signature="catalog",
        packages_by_name={"code-ontology": package_entry},
    )
    _write_package_projection_index(aware_root=tmp_path, index=index)

    def fail_json_loads(_payload: str) -> object:
        raise AssertionError("an unchanged index must not be parsed again")

    monkeypatch.setattr(package_index_module.json, "loads", fail_json_loads)

    assert load_meta_runtime_package_projection_index(aware_root=tmp_path) is index


def test_meta_runtime_package_projection_lookup_skips_semantic_object_hydration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )
    catalog_signature = package_index_module._package_catalog_signature(
        repo_root=tmp_path,
        package_entries=(package_entry,),
    )
    index = MetaRuntimePackageProjectionIndex(
        catalog_signature=catalog_signature,
        packages_by_name={"code-ontology": package_entry},
        projections_by_name={
            "CodePackage": MetaRuntimeProjectionIndexEntry(
                projection_name="CodePackage",
                package_name="code-ontology",
                fqn_prefix="aware_code",
                manifest_path=package_entry.manifest_path,
            )
        },
        semantic_objects_by_key={
            "aware_code.CodePackage": MetaRuntimeSemanticObjectIndexEntry(
                semantic_key="aware_code.CodePackage",
                object_kind="class",
                package_name="code-ontology",
                fqn_prefix="aware_code",
                manifest_path=package_entry.manifest_path,
            )
        },
    )
    _write_package_projection_index(aware_root=tmp_path, index=index)
    lookup_path = meta_runtime_package_projection_lookup_path(aware_root=tmp_path)
    lookup_payload = json.loads(lookup_path.read_text(encoding="utf-8"))
    assert lookup_payload["schema"] == (
        package_index_module.META_RUNTIME_PACKAGE_PROJECTION_LOOKUP_SCHEMA
    )
    assert "semantic_objects" not in lookup_payload
    monkeypatch.setattr(
        package_index_module, "_package_projection_index_read_cache", None
    )
    monkeypatch.setattr(
        package_index_module, "_package_projection_lookup_read_cache", None
    )

    def fail_semantic_hydration(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("lookup-only reads must not hydrate semantic objects")

    monkeypatch.setattr(
        package_index_module,
        "_semantic_object_entries_from_payload",
        fail_semantic_hydration,
    )

    lookup = load_meta_runtime_package_projection_lookup(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(package_entry,),
    )

    assert lookup is not None
    assert lookup.projections_by_name["CodePackage"].package_name == "code-ontology"
    assert lookup.semantic_objects_by_key == {}


def test_meta_runtime_package_projection_lookup_does_not_read_full_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )
    catalog_signature = package_index_module._package_catalog_signature(
        repo_root=tmp_path,
        package_entries=(package_entry,),
    )
    index = MetaRuntimePackageProjectionIndex(
        catalog_signature=catalog_signature,
        packages_by_name={"code-ontology": package_entry},
        projections_by_name={
            "CodePackage": MetaRuntimeProjectionIndexEntry(
                projection_name="CodePackage",
                package_name="code-ontology",
                fqn_prefix="aware_code",
                manifest_path=package_entry.manifest_path,
            )
        },
    )
    _write_package_projection_index(aware_root=tmp_path, index=index)
    meta_runtime_package_projection_index_path(aware_root=tmp_path).write_text(
        "not-json",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        package_index_module, "_package_projection_index_read_cache", None
    )
    monkeypatch.setattr(
        package_index_module, "_package_projection_lookup_read_cache", None
    )

    lookup = load_meta_runtime_package_projection_lookup(
        repo_root=tmp_path,
        aware_root=tmp_path,
        package_entries=(package_entry,),
    )

    assert lookup is not None
    assert lookup.projections_by_name["CodePackage"].package_name == "code-ontology"


def test_meta_runtime_package_projection_index_skips_identical_atomic_write(
    tmp_path: Path,
) -> None:
    package_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )
    index = MetaRuntimePackageProjectionIndex(
        catalog_signature="catalog",
        packages_by_name={"code-ontology": package_entry},
    )
    _write_package_projection_index(aware_root=tmp_path, index=index)
    path = meta_runtime_package_projection_index_path(aware_root=tmp_path)
    first_inode = path.stat().st_ino

    _write_package_projection_index(aware_root=tmp_path, index=index)

    assert path.stat().st_ino == first_inode


def test_meta_runtime_package_projection_index_invalidates_external_replacement(
    tmp_path: Path,
) -> None:
    package_entry = _package_entry(
        tmp_path=tmp_path,
        package_name="code-ontology",
        fqn_prefix="aware_code",
        projection_names=("CodePackage",),
    )
    first = MetaRuntimePackageProjectionIndex(
        catalog_signature="first",
        packages_by_name={"code-ontology": package_entry},
    )
    second = MetaRuntimePackageProjectionIndex(
        catalog_signature="second",
        packages_by_name={"code-ontology": package_entry},
    )
    _write_package_projection_index(aware_root=tmp_path, index=first)
    replacement_root = tmp_path / "replacement"
    _write_package_projection_index(aware_root=replacement_root, index=second)
    replacement_path = meta_runtime_package_projection_index_path(
        aware_root=replacement_root
    )
    replacement_path.replace(
        meta_runtime_package_projection_index_path(aware_root=tmp_path)
    )

    loaded = load_meta_runtime_package_projection_index(aware_root=tmp_path)

    assert loaded is not None
    assert loaded.catalog_signature == "second"


def _package_entry(
    *,
    tmp_path: Path,
    package_name: str,
    fqn_prefix: str,
    projection_names: tuple[str, ...],
) -> MetaRuntimePackageIndexEntry:
    manifest_path = tmp_path / "modules" / package_name / "aware.toml"
    return MetaRuntimePackageIndexEntry(
        module_id=package_name.removesuffix("-ontology"),
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        manifest_path=manifest_path,
        projection_names=projection_names,
    )
