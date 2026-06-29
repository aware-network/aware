from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.materialization import (
    materialize_object_config_graph_identity,
)
from aware_meta.graph.projection.declarations import (
    ProjectionDeclaration,
    ProjectionObservableDeclaration,
)
from aware_meta.graph.projection.materialization import (
    materialize_projection_identities,
)
from aware_meta.graph.projection.stable_ids import (
    stable_object_projection_graph_id,
    stable_object_projection_graph_observable_id,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_identity_id,
    stable_object_projection_graph_identity_id,
)


def test_projection_identity_materialization_records_canonical_observable_keys() -> (
    None
):
    ocg_id = uuid5(NAMESPACE_URL, "meta://tests/projection-materialization/ocg")
    opg_id = stable_object_projection_graph_id(
        object_config_graph_id=ocg_id,
        name="Identity",
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        object_config_graph_id=ocg_id,
        language=CodeLanguage.aware,
        name="Identity",
        projection_hash="sha256:identity",
    )

    ocgi_result = materialize_object_config_graph_identity(
        ocg_fqn_prefix="aware_meta",
    )
    result = materialize_projection_identities(
        object_config_graph_identity=ocgi_result.object_config_graph_identity,
        object_config_graph_id=ocg_id,
        opgs=[opg],
        declarations_by_name={
            "Identity": ProjectionDeclaration(
                projection_name="Identity",
                label="Identity",
                description=None,
                is_branchable=True,
                observables=(
                    ProjectionObservableDeclaration(
                        key="default",
                        kind="construct",
                        is_default=True,
                        description="Default identity view",
                        position=0,
                    ),
                ),
            ),
        },
    )

    ocgi_id = stable_object_config_graph_identity_id(key="aware_meta")
    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=opg_id,
    )
    observable_id = stable_object_projection_graph_observable_id(
        object_projection_graph_identity_id=opgi_id,
        observable_key="default",
    )

    assert ocgi_result.object_config_graph_identity.id == ocgi_id
    assert len(result.projection_identities) == 1
    assert result.projection_identities[0].projection_name == "Identity"
    assert result.projection_identities[0].object_projection_graph_id == opg_id
    assert (
        result.projection_identities[0].object_projection_graph_identity_id == opgi_id
    )
    assert result.projection_identities[0].projection_hash == "sha256:identity"
    assert result.projection_identities[0].is_branchable is True

    assert len(result.observables) == 1
    assert result.observables[0].projection_name == "Identity"
    assert result.observables[0].object_projection_graph_identity_id == opgi_id
    assert result.observables[0].object_projection_graph_observable_id == observable_id
    assert result.observables[0].observable_key == "default"
    assert result.observables[0].key == "Identity:default"
    assert result.observables[0].kind == "construct"
    assert result.observables[0].description == "Default identity view"
    assert result.observables[0].is_default is True

    opgi = ocgi_result.object_config_graph_identity.object_projection_graph_identities[
        0
    ]
    assert opgi.id == opgi_id
    observable = opgi.object_projection_graph_observables[0]
    assert observable.id == observable_id
    assert observable.observable_key == "default"
    assert observable.key == "Identity:default"


def test_projection_identity_materialization_defaults_first_observable() -> None:
    ocg_id = uuid5(NAMESPACE_URL, "meta://tests/projection-materialization/default")

    ocgi_result = materialize_object_config_graph_identity(
        ocg_fqn_prefix="aware_meta",
    )
    result = materialize_projection_identities(
        object_config_graph_identity=ocgi_result.object_config_graph_identity,
        object_config_graph_id=ocg_id,
        opgs=[],
        declarations_by_name={
            "Identity": ProjectionDeclaration(
                projection_name="Identity",
                label=None,
                description=None,
                is_branchable=False,
                observables=(
                    ProjectionObservableDeclaration(
                        key="first",
                        kind="instance",
                        is_default=False,
                        description=None,
                        position=0,
                    ),
                    ProjectionObservableDeclaration(
                        key="second",
                        kind="construct",
                        is_default=False,
                        description=None,
                        position=1,
                    ),
                ),
            ),
        },
    )

    assert [observable.observable_key for observable in result.observables] == [
        "first",
        "second",
    ]
    assert result.observables[0].is_default is True
    assert result.observables[1].is_default is False


def test_projection_ownership_split_keeps_config_out_of_projection_internals() -> None:
    config_materialization_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/config/materialization.py"
    ).read_text(encoding="utf-8")
    projection_compiler_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/projection/compiler.py"
    ).read_text(encoding="utf-8")
    projection_materialization_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/projection/materialization.py"
    ).read_text(encoding="utf-8")
    config_builder_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/config/builder.py"
    ).read_text(encoding="utf-8")

    assert "aware_meta.graph.projection" not in config_materialization_source
    assert "ObjectProjectionGraph" not in config_materialization_source
    assert (
        "stable_object_projection_graph_observable_id" not in projection_compiler_source
    )
    assert "ObjectProjectionGraphObservable(" not in projection_compiler_source
    assert "ObjectProjectionGraphObservable(" in projection_materialization_source
    assert "aware_meta.graph.config.projection" not in config_builder_source
