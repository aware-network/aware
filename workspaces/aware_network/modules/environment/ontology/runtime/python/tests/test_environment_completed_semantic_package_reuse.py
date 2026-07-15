from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code.semantic_materialization import (
    SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY,
)
from aware_environment.materialization import environment_workspace_provider
from aware_environment.materialization import service as environment_service
from aware_meta.materialization import stable_object_config_graph_package_branch_id
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_ontology_ontology.stable_ids import (
    stable_ontology_config_id,
    stable_ontology_package_id,
)


def _graph(*, graph_id: UUID, fqn_prefix: str) -> ObjectConfigGraph:
    return ObjectConfigGraph.model_construct(
        id=graph_id,
        name=fqn_prefix,
        fqn_prefix=fqn_prefix,
        hash="semantic-hash",
        object_config_graph_nodes=[],
        object_projection_graphs=[],
    )


def _completed_context(
    *,
    workspace_root: Path,
    package_name: str = "identity-ontology",
    fqn_prefix: str = "aware_identity",
) -> tuple[dict[str, object], dict[str, UUID]]:
    aware_toml_path = workspace_root / "modules/identity/ontology/structure/aware.toml"
    branch_id = stable_object_config_graph_package_branch_id(
        workspace_root=workspace_root,
        aware_toml_path=aware_toml_path,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    ids = {
        "branch": branch_id,
        "graph": uuid4(),
        "code_package": uuid4(),
        "code_head": uuid4(),
        "code_oig": uuid4(),
        "ocg_head": uuid4(),
        "ocg_oig": uuid4(),
        "ocg_package": uuid4(),
        "ocg_package_head": uuid4(),
        "ocg_package_oig": uuid4(),
        "config": stable_ontology_config_id(
            name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        "config_commit": uuid4(),
        "config_head": uuid4(),
        "config_oig": uuid4(),
        "package": stable_ontology_package_id(
            name=package_name,
            fqn_prefix=fqn_prefix,
        ),
        "package_commit": uuid4(),
        "package_head": uuid4(),
        "package_oig": uuid4(),
    }
    detail = {
        "module_name": "identity",
        "aware_toml_path": "modules/identity/ontology/structure/aware.toml",
        "source_manifest_path": "modules/identity/ontology/structure/aware.toml",
        "semantic_contract_manifest_relative_path": (
            "modules/identity/ontology/aware.ontology.toml"
        ),
        "manifest_relative_path": "modules/identity/ontology/aware.ontology.toml",
        "package_root": "modules/identity/ontology",
        "workspace_package_root": "modules/identity/ontology",
        "sources_root": "modules/identity/ontology/structure",
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "semantic_branch_id": str(ids["branch"]),
        "code_package_id": str(ids["code_package"]),
        "code_package_head_commit_id": str(ids["code_head"]),
        "code_package_object_instance_graph_commit_id": str(ids["code_oig"]),
        "object_config_graph_package_id": str(ids["ocg_package"]),
        "object_config_graph_package_head_commit_id": str(ids["ocg_package_head"]),
        "object_config_graph_package_object_instance_graph_commit_id": str(
            ids["ocg_package_oig"]
        ),
        "object_config_graph_id": str(ids["graph"]),
        "object_config_graph_head_commit_id": str(ids["ocg_head"]),
        "object_config_graph_object_instance_graph_commit_id": str(ids["ocg_oig"]),
        "ontology_config_commit_id": str(ids["config_commit"]),
        "ontology_package_commit_id": str(ids["package_commit"]),
    }

    def bundle(
        *, root_kind: str, root_id: UUID, head: UUID, oig: UUID
    ) -> dict[str, object]:
        return {
            "package_kind": "ontology",
            "package_key": package_name,
            "semantic_contract_provider_key": "aware_ontology",
            "semantic_root_kind": root_kind,
            "semantic_root_id": str(root_id),
            "semantic_branch_id": str(ids["branch"]),
            "semantic_head_commit_id": str(head),
            "semantic_object_instance_graph_commit_id": str(oig),
            "semantic_packages": [detail],
        }

    config_bundle = bundle(
        root_kind="OntologyConfig",
        root_id=ids["config"],
        head=ids["config_head"],
        oig=ids["config_oig"],
    )
    package_bundle = bundle(
        root_kind="OntologyPackage",
        root_id=ids["package"],
        head=ids["package_head"],
        oig=ids["package_oig"],
    )

    return (
        {
            "semantic_object_config_graphs": (
                _graph(graph_id=ids["graph"], fqn_prefix=fqn_prefix),
            ),
            SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY: (
                config_bundle,
                package_bundle,
            ),
            "workspace_materialized_semantic_package_refs": (
                {
                    key: value
                    for key, value in config_bundle.items()
                    if key != "semantic_packages"
                },
                {
                    key: value
                    for key, value in package_bundle.items()
                    if key != "semantic_packages"
                },
            ),
        },
        ids,
    )


def test_completed_semantic_package_context_decodes_exact_paired_evidence(
    tmp_path: Path,
) -> None:
    context, ids = _completed_context(workspace_root=tmp_path)

    completed = environment_workspace_provider._completed_semantic_packages_by_package_name_from_context(
        context=context,
        workspace_root=tmp_path,
    )

    result = completed["identity-ontology"]
    graph_by_package = environment_workspace_provider._source_object_config_graphs_by_package_name_from_context(
        context
    )
    assert result.semantic_branch_id == ids["branch"]
    assert result.object_config_graph_id == ids["graph"]
    assert graph_by_package["identity-ontology"].id == ids["graph"]
    assert result.code_package_head_commit_id == ids["code_head"]
    assert result.ontology_config_head_commit_id == ids["config_head"]
    assert result.ontology_config_commit_id == ids["config_commit"]
    assert result.ontology_package_head_commit_id == ids["package_head"]
    assert result.ontology_package_commit_id == ids["package_commit"]
    assert result.semantic_commit_strategy == "completed_semantic_package_reuse"


def test_completed_semantic_package_context_rejects_partial_evidence(
    tmp_path: Path,
) -> None:
    context, _ = _completed_context(workspace_root=tmp_path)
    context[SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY] = tuple(
        context[SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY]
    )[1:]

    assert not (
        environment_workspace_provider._completed_semantic_packages_by_package_name_from_context(
            context=context,
            workspace_root=tmp_path,
        )
    )


def test_completed_semantic_package_context_selects_current_completed_refs_from_stale_intents(
    tmp_path: Path,
) -> None:
    context, ids = _completed_context(workspace_root=tmp_path)
    current_intents = tuple(context[SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY])
    stale_intents = tuple(
        {
            **intent,
            "semantic_head_commit_id": str(uuid4()),
            "semantic_object_instance_graph_commit_id": str(uuid4()),
        }
        for intent in current_intents
    )
    context[SEMANTIC_PACKAGE_SELECTION_INTENTS_CONTEXT_KEY] = (
        *stale_intents,
        *current_intents,
    )

    completed = environment_workspace_provider._completed_semantic_packages_by_package_name_from_context(
        context=context,
        workspace_root=tmp_path,
    )

    assert (
        completed["identity-ontology"].ontology_config_head_commit_id
        == ids["config_head"]
    )
    assert (
        completed["identity-ontology"].ontology_package_head_commit_id
        == ids["package_head"]
    )


def test_completed_semantic_package_context_rejects_uncompleted_intent(
    tmp_path: Path,
) -> None:
    context, _ = _completed_context(workspace_root=tmp_path)
    context["workspace_materialized_semantic_package_refs"] = ()

    assert not (
        environment_workspace_provider._completed_semantic_packages_by_package_name_from_context(
            context=context,
            workspace_root=tmp_path,
        )
    )


def test_completed_semantic_package_context_rejects_intents_without_completed_refs(
    tmp_path: Path,
) -> None:
    context, _ = _completed_context(workspace_root=tmp_path)
    context.pop("workspace_materialized_semantic_package_refs")

    assert not (
        environment_workspace_provider._completed_semantic_packages_by_package_name_from_context(
            context=context,
            workspace_root=tmp_path,
        )
    )


@pytest.mark.asyncio
async def test_completed_semantic_package_currentness_requires_all_exact_lane_heads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, ids = _completed_context(workspace_root=tmp_path)
    completed = (
        environment_workspace_provider._completed_semantic_packages_by_package_name_from_context(
            context=context,
            workspace_root=tmp_path,
        )
    )["identity-ontology"]
    graph = tuple(context["semantic_object_config_graphs"])[0]
    spec = environment_service._DiscoveredEnvironmentSemanticPackageSpec(
        module_name="identity",
        aware_toml_path=(tmp_path / "modules/identity/ontology/structure/aware.toml"),
        ontology_manifest_path="modules/identity/ontology/aware.ontology.toml",
        source_manifest_path="modules/identity/ontology/structure/aware.toml",
        package_name="identity-ontology",
        fqn_prefix="aware_identity",
        dependency_package_names=(),
        manifest_relative_path="modules/identity/ontology/aware.ontology.toml",
        package_root="modules/identity/ontology",
        workspace_package_root="modules/identity/ontology",
        sources_root="modules/identity/ontology/structure",
        surface="ontology",
    )
    projection_hashes = {
        "code": "code-projection",
        "ocg": "ocg-projection",
        "ocg_package": "ocg-package-projection",
        "config": "config-projection",
        "package": "package-projection",
    }
    head_by_projection = {
        projection_hashes["code"]: ids["code_head"],
        projection_hashes["ocg"]: ids["ocg_head"],
        projection_hashes["ocg_package"]: ids["ocg_package_head"],
        projection_hashes["config"]: ids["config_commit"],
        projection_hashes["package"]: ids["package_commit"],
    }
    oig_by_head = {
        ids["code_head"]: ids["code_oig"],
        ids["ocg_head"]: ids["ocg_oig"],
        ids["ocg_package_head"]: ids["ocg_package_oig"],
        ids["config_commit"]: ids["config_oig"],
        ids["package_commit"]: ids["package_oig"],
    }

    async def fake_head(
        *, workspace_root: Path, branch_id: UUID, projection_hash: str
    ) -> UUID | None:
        assert workspace_root == tmp_path
        assert branch_id == ids["branch"]
        return head_by_projection.get(projection_hash)

    async def fake_oig(
        *,
        workspace_root: Path,
        branch_id: UUID,
        projection_hash: str,
        domain_commit_id: UUID,
    ) -> UUID | None:
        assert workspace_root == tmp_path
        assert branch_id == ids["branch"]
        assert head_by_projection[projection_hash] == domain_commit_id
        return oig_by_head.get(domain_commit_id)

    monkeypatch.setattr(environment_service, "_lane_domain_head_commit_id", fake_head)
    monkeypatch.setattr(
        environment_service,
        "_object_instance_graph_commit_id_from_domain_commit",
        fake_oig,
    )

    async def is_current() -> bool:
        return await environment_service._completed_semantic_package_ref_is_current(
            semantic_package=completed,
            graph=graph,
            package_spec=spec,
            workspace_root=tmp_path,
            code_package_projection_hash=projection_hashes["code"],
            object_config_graph_projection_hash=projection_hashes["ocg"],
            object_config_graph_package_projection_hash=(
                projection_hashes["ocg_package"]
            ),
            ontology_config_projection_hash=projection_hashes["config"],
            ontology_package_projection_hash=projection_hashes["package"],
        )

    assert await is_current()
    head_by_projection[projection_hashes["package"]] = uuid4()
    assert not await is_current()


def test_completed_semantic_package_synthetic_result_preserves_coordinates(
    tmp_path: Path,
) -> None:
    context, ids = _completed_context(workspace_root=tmp_path)
    completed = (
        environment_workspace_provider._completed_semantic_packages_by_package_name_from_context(
            context=context,
            workspace_root=tmp_path,
        )
    )["identity-ontology"]
    graph = tuple(context["semantic_object_config_graphs"])[0]

    result = environment_service._meta_service_result_from_completed_semantic_package(
        semantic_package=completed,
        graph=graph,
    )

    assert result.object_config_graph is graph
    assert result.code_package_head_commit_id == ids["code_head"]
    assert result.object_config_graph_package_head_commit_id == ids["ocg_package_head"]
    assert result.semantic_commit_strategy == "completed_semantic_package_reuse"
