from __future__ import annotations

from uuid import uuid4

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.lane.oigi import (
    resolve_ocg_lane_object_instance_graph_identity_id,
)
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
    stable_object_instance_graph_identity_id,
    stable_object_projection_graph_identity_id,
)
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


def test_ocg_lane_oigi_id_is_derived_from_ocgi_opgi_and_oig() -> None:
    ocgi = ObjectConfigGraphIdentity(
        id=stable_object_config_graph_identity_id(key="aware.home"),
        key="aware.home",
        label="ocg:aware.home",
    )
    ocg = ObjectConfigGraph(
        id=uuid4(),
        object_config_graph_identity=ocgi,
        object_config_graph_identity_id=ocgi.id,
        name="aware_home",
        description=None,
        hash="sha256:test:ocg",
        fqn_prefix="aware.home",
        language=CodeLanguage.aware,
    )
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=ocg.id,
        name="object_config_graph",
        projection_hash="sha256:test:ocg-projection",
        language=CodeLanguage.aware,
        description=None,
        supports_virtual_build=True,
    )
    domain_oig_id = ocg.id

    resolved_id = resolve_ocg_lane_object_instance_graph_identity_id(
        identity_graph=ocg,
        object_projection_graph=opg,
        object_instance_graph_id=domain_oig_id,
    )

    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi.id,
        object_projection_graph_id=opg.id,
    )
    assert resolved_id == stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph_id=domain_oig_id,
    )
    assert resolved_id != domain_oig_id


def test_ocg_lane_oigi_id_falls_back_to_stable_ocg_key_not_raw_ocg_id() -> None:
    ocg = ObjectConfigGraph(
        id=uuid4(),
        name="Aware Home",
        description=None,
        hash="sha256:test:ocg",
        fqn_prefix="aware.home",
        language=CodeLanguage.aware,
    )
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=ocg.id,
        name="object_config_graph",
        projection_hash="sha256:test:ocg-projection",
        language=CodeLanguage.aware,
        description=None,
        supports_virtual_build=True,
    )

    resolved_id = resolve_ocg_lane_object_instance_graph_identity_id(
        identity_graph=ocg,
        object_projection_graph=opg,
        object_instance_graph_id=ocg.id,
    )

    ocgi_id = stable_object_config_graph_identity_id(key="aware.home")
    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi_id,
        object_projection_graph_id=opg.id,
    )
    assert resolved_id == stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph_id=ocg.id,
    )
    assert resolved_id != ocg.id


def test_ocg_lane_oigi_id_uses_projection_owner_not_semantic_graph_identity() -> None:
    stale_identity_graph_ocgi_id = uuid4()
    identity_graph_ocgi = ObjectConfigGraphIdentity(
        id=stale_identity_graph_ocgi_id,
        key="aware_meta",
        label="ocg:aware_meta",
    )
    identity_graph = ObjectConfigGraph(
        id=uuid4(),
        object_config_graph_identity=identity_graph_ocgi,
        object_config_graph_identity_id=identity_graph_ocgi.id,
        name="aware_meta",
        description=None,
        hash="sha256:test:identity-graph",
        fqn_prefix="aware.meta",
        language=CodeLanguage.aware,
    )
    semantic_graph_ocgi_id = stable_object_config_graph_identity_id(key="home")
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=identity_graph.id,
        name="object_config_graph",
        projection_hash="sha256:test:object-config-graph",
        language=CodeLanguage.aware,
        description=None,
        supports_virtual_build=True,
    )
    domain_oig_id = uuid4()

    resolved_id = resolve_ocg_lane_object_instance_graph_identity_id(
        identity_graph=identity_graph,
        object_projection_graph=opg,
        object_instance_graph_id=domain_oig_id,
    )

    expected_opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=stable_object_config_graph_identity_id(
            key="aware.meta"
        ),
        object_projection_graph_id=opg.id,
    )
    wrong_semantic_opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=semantic_graph_ocgi_id,
        object_projection_graph_id=opg.id,
    )
    assert resolved_id == stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=expected_opgi_id,
        object_instance_graph_id=domain_oig_id,
    )
    assert resolved_id != stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=stale_identity_graph_ocgi_id,
            object_projection_graph_id=opg.id,
        ),
        object_instance_graph_id=domain_oig_id,
    )
    assert resolved_id != stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=wrong_semantic_opgi_id,
        object_instance_graph_id=domain_oig_id,
    )


def test_ocg_lane_oigi_id_prefers_source_opgi_in_composed_identity_graph() -> None:
    container_ocgi_id = stable_object_config_graph_identity_id(key="aware_environment")
    source_ocgi_id = stable_object_config_graph_identity_id(key="aware_meta")
    opg = ObjectProjectionGraph(
        id=uuid4(),
        object_config_graph_id=uuid4(),
        name="object_config_graph",
        projection_hash="sha256:test:object-config-graph",
        language=CodeLanguage.aware,
        description=None,
        supports_virtual_build=True,
    )
    container_opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=container_ocgi_id,
        object_projection_graph_id=opg.id,
    )
    source_opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=source_ocgi_id,
        object_projection_graph_id=opg.id,
    )
    identity_graph = ObjectConfigGraph(
        id=uuid4(),
        object_config_graph_identity=ObjectConfigGraphIdentity(
            id=container_ocgi_id,
            key="aware_environment",
            label="ocg:aware_environment",
            object_projection_graph_identities=[
                ObjectProjectionGraphIdentity(
                    id=container_opgi_id,
                    object_config_graph_identity_id=container_ocgi_id,
                    object_projection_graph_id=opg.id,
                    projection_name=opg.name,
                    label="opg:object_config_graph",
                ),
                ObjectProjectionGraphIdentity(
                    id=source_opgi_id,
                    object_config_graph_identity_id=source_ocgi_id,
                    object_projection_graph_id=opg.id,
                    projection_name=opg.name,
                    label="opg:object_config_graph",
                ),
            ],
        ),
        name="Aware Environment",
        description=None,
        hash="sha256:test:composed",
        fqn_prefix="aware_environment",
        language=CodeLanguage.aware,
    )
    domain_oig_id = uuid4()

    resolved_id = resolve_ocg_lane_object_instance_graph_identity_id(
        identity_graph=identity_graph,
        object_projection_graph=opg,
        object_instance_graph_id=domain_oig_id,
    )

    assert resolved_id == stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=source_opgi_id,
        object_instance_graph_id=domain_oig_id,
    )
    assert resolved_id != stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=container_opgi_id,
        object_instance_graph_id=domain_oig_id,
    )
