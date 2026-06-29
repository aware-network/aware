from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from uuid import uuid4

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
    stable_object_projection_graph_identity_id,
)
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphCommitIndex
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)


def test_resolve_meta_graph_ocgi_opgi_synthesizes_canonical_projection_identity() -> (
    None
):
    ocg_key = "aware_environment"
    ocgi_id = stable_object_config_graph_identity_id(key=ocg_key)
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=uuid4(),
        name="object_config_graph",
        projection_hash="sha256:test:object-config-graph",
        language=CodeLanguage.aware,
        description=None,
        supports_virtual_build=True,
    )
    stale_opgi = ObjectProjectionGraphIdentity(
        id=uuid4(),
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=opg.id,
        projection_name=opg.name,
        label="stale",
    )
    ocgi = ObjectConfigGraphIdentity(
        id=ocgi_id,
        key=ocg_key,
        label=f"ocg:{ocg_key}",
        object_projection_graph_identities=[stale_opgi],
    )
    ocg = ObjectConfigGraph(
        id=uuid4(),
        object_config_graph_identity=ocgi,
        object_config_graph_identity_id=ocgi.id,
        name="meta-tests",
        description=None,
        hash="sha256:test:ocg",
        fqn_prefix=ocg_key,
        language=CodeLanguage.aware,
        object_projection_graphs=[opg],
    )
    index = cast(
        MetaGraphCommitIndex,
        SimpleNamespace(ocg=ocg, opg_by_hash={opg.projection_hash: opg}),
    )

    resolved_ocgi, resolved_opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=opg.projection_hash,
    )

    assert resolved_ocgi is ocgi
    assert resolved_opgi is not None
    assert resolved_opgi.id == stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=opg.id,
    )
    assert resolved_opgi.id != stale_opgi.id


def test_resolve_meta_graph_ocgi_opgi_prefers_source_owned_projection_identity() -> (
    None
):
    composite_ocg_key = "aware_environment"
    source_ocg_key = "aware_environment"
    composite_ocgi_id = stable_object_config_graph_identity_id(
        key=composite_ocg_key,
    )
    source_ocgi_id = stable_object_config_graph_identity_id(key=source_ocg_key)
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=uuid4(),
        name="environment_config",
        projection_hash="sha256:test:environment-config",
        language=CodeLanguage.aware,
        description=None,
        supports_virtual_build=True,
    )
    source_opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=source_ocgi_id,
        object_projection_graph_id=opg.id,
    )
    source_opgi = ObjectProjectionGraphIdentity(
        id=source_opgi_id,
        object_config_graph_identity_id=source_ocgi_id,
        object_projection_graph_id=opg.id,
        projection_name=opg.name,
        label="opg:environment_config",
        is_branchable=True,
    )
    composite_ocgi = ObjectConfigGraphIdentity(
        id=composite_ocgi_id,
        key=composite_ocg_key,
        label=f"ocg:{composite_ocg_key}",
        object_projection_graph_identities=[source_opgi],
    )
    ocg = ObjectConfigGraph(
        id=uuid4(),
        object_config_graph_identity=composite_ocgi,
        object_config_graph_identity_id=composite_ocgi.id,
        name="workspace semantic",
        description=None,
        hash="sha256:test:composed",
        fqn_prefix=composite_ocg_key,
        language=CodeLanguage.aware,
        object_projection_graphs=[opg],
    )
    index = cast(
        MetaGraphCommitIndex,
        SimpleNamespace(ocg=ocg, opg_by_hash={opg.projection_hash: opg}),
    )

    resolved_ocgi, resolved_opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=opg.projection_hash,
    )

    assert resolved_ocgi is composite_ocgi
    assert resolved_opgi is source_opgi
    assert resolved_opgi.is_branchable is True
    assert composite_ocgi.object_projection_graph_identities == [source_opgi]
