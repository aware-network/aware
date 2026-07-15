# pyright: reportPrivateUsage=false

from __future__ import annotations

from pathlib import Path

import pytest

from aware_meta.runtime.package_index import (
    MetaRuntimePackageProjectionIndex,
    MetaRuntimePackageIndexEntry,
    MetaRuntimePackageIndexPatch,
    MetaRuntimeProjectionIndexEntry,
    _with_preserved_compatible_index_entries,
    apply_meta_runtime_package_index_patch,
    build_meta_runtime_package_projection_index,
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
