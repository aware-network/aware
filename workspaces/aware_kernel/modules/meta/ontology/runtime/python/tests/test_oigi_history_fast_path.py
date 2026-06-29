from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_history.stable_ids import stable_lane_id
from aware_history_ontology.stable_ids import stable_commit_id
from aware_meta.graph.instance.commit.fs_store import (
    ObjectInstanceGraphCommitEnvelope,
    OigiHistoryDomainCommitProjection,
)
from aware_meta.runtime.commit.identity_history import (
    upsert_object_instance_graph_identity_history_from_domain_commit,
)


@pytest.mark.asyncio
async def test_oigi_history_upsert_projection_index_hit_skips_head_materialization() -> (
    None
):
    domain_oig_id = uuid4()
    oigi_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    oigi_projection_hash = "sha256:test:oigi"
    domain_commit_id = uuid4()
    oigi_lane_commit_id = uuid4()
    oigi_graph_hash_post = "sha256:test:oigi-head"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    history_commit_id = stable_commit_id(
        lane_id=lane_id,
        key=str(domain_commit_id),
    )
    envelope = ObjectInstanceGraphCommitEnvelope(
        commit_id=domain_commit_id,
        lane_id=lane_id,
        key=str(domain_commit_id),
        author_id=uuid4(),
        created_at=datetime.now(UTC),
        status="local",
        parent_commit_ids=(),
        object_instance_graph_commit_id=uuid4(),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        projection_hash=domain_projection_hash,
        source_language="aware",
    )
    projection = OigiHistoryDomainCommitProjection(
        domain_commit_id=domain_commit_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_lane_id=lane_id,
        history_commit_id=history_commit_id,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        oigi_projection_hash=oigi_projection_hash,
        oigi_lane_commit_id=oigi_lane_commit_id,
        oigi_graph_hash_post=oigi_graph_hash_post,
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=[
                SimpleNamespace(
                    name="ObjectInstanceGraphIdentity",
                    projection_hash=oigi_projection_hash,
                )
            ]
        )
    )

    class _Store:
        head_call_count = 0
        projection_read_count = 0

        async def head(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
        ) -> dict[str, object]:
            assert branch_id == domain_oig_id
            assert projection_hash == oigi_projection_hash
            self.head_call_count += 1
            return {
                "commit_id": str(oigi_lane_commit_id),
                "graph_hash_post": oigi_graph_hash_post,
                "object_instance_graph_id": str(oigi_id),
            }

        async def get_oigi_history_domain_commit_projection(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            domain_commit_id: UUID,
        ) -> OigiHistoryDomainCommitProjection | None:
            assert branch_id == domain_oig_id
            assert projection_hash == oigi_projection_hash
            assert domain_commit_id == projection.domain_commit_id
            self.projection_read_count += 1
            return projection

    class _Materializer:
        async def get(self, **_: object) -> object:
            raise AssertionError(
                "projection-index fast path must not materialize OIGI head"
            )

    store = _Store()
    perf_ms: dict[str, int] = {}

    result = await upsert_object_instance_graph_identity_history_from_domain_commit(
        index=index,  # type: ignore[arg-type]
        actor_id=uuid4(),
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_envelope=envelope,
        perf_ms=perf_ms,
        store=store,  # type: ignore[arg-type]
        lane_materializer=_Materializer(),  # type: ignore[arg-type]
    )

    assert result == oigi_id
    assert store.head_call_count == 1
    assert store.projection_read_count == 1
    assert perf_ms["run_commit_reaction_oigi_projection_index_head_hit_count"] == 1
    assert perf_ms["run_commit_reaction_oigi_projection_index_fast_path_count"] == 1
    assert "run_commit_reaction_oigi_materialize_head_ms" not in perf_ms
