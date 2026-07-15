from __future__ import annotations

from pathlib import Path
import sys
from typing import cast
from uuid import NAMESPACE_URL, uuid5

import pytest

from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.testing import (
    MetaOIGAssertions,
    materialize_meta_runtime_lane_head,
)
from ._experience_runtime_test_paths import REPO_ROOT

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.append(str(_TESTS_DIR))

from .test_experience_projection_view_invocation_action_meta_runtime import (
    IsolatedMetaAwareRoot,
    _build_experience_meta_runtime,
    _expect_uuid_primitive,
)


@pytest.mark.asyncio
async def test_role_config_invocation_action_policy_meta_runtime_e2e(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_experience_ontology  # noqa: F401
    import aware_identity_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )
    from aware_experience_ontology.invocation.role_config_invocation_action_config import (
        RoleConfigInvocationActionConfig,
    )
    from aware_experience_ontology.stable_ids import (
        stable_experience_invocation_action_config_id,
        stable_projection_experience_id,
        stable_role_config_invocation_action_config_id,
    )

    ns = uuid5(
        NAMESPACE_URL,
        "aware://tests/experience/role-config-invocation-action-runtime/v1",
    )
    opgi_id = uuid5(ns, "opgi")
    projection_experience_name = "role_config_invocation_action_runtime"
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name=projection_experience_name,
    )
    role_config_id = uuid5(ns, "role_config")
    api_capability_endpoint_id = uuid5(ns, "api_capability_endpoint")
    action_config_id = stable_experience_invocation_action_config_id(
        projection_experience_id=projection_experience_id,
        target_kind="api",
        entity_id=api_capability_endpoint_id,
    )
    policy_id = stable_role_config_invocation_action_config_id(
        experience_invocation_action_config_id=action_config_id,
        role_config_id=role_config_id,
        policy_key="invoke",
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="ExperienceInvocationActionConfig",
            branch_id=uuid5(ns, "branch"),
        )
        with lane.activate(commit=True, publish=False):
            action_config = (
                await ExperienceInvocationActionConfig.build_via_projection_experience(
                    projection_experience_id=projection_experience_id,
                    target_kind="api",
                    api_capability_endpoint_id=api_capability_endpoint_id,
                )
            )
        assert lane.last_response is not None
        root_commit_id = lane.last_response.commit_id
        assert root_commit_id is not None
        assert action_config.id == action_config_id

        with lane.activate(commit=True, publish=False):
            policy = await action_config.allow_role_config(
                role_config_id=role_config_id,
                policy_key="invoke",
                requirement_kind="admitted_actor_role",
                description="Conversation participants may send messages.",
            )
        assert policy.id == policy_id
        assert policy.experience_invocation_action_config_id == action_config_id
        assert policy.role_config_id == role_config_id
        assert policy.policy_key == "invoke"
        assert policy.requirement_kind == "admitted_actor_role"
        assert policy.description == "Conversation participants may send messages."
        assert lane.last_response is not None
        policy_commit_id = lane.last_response.commit_id
        assert policy_commit_id is not None
        assert policy_commit_id != root_commit_id

        with lane.activate(commit=True, publish=False):
            repeat = await action_config.allow_role_config(
                role_config_id=role_config_id,
                policy_key="invoke",
                requirement_kind="admitted_actor_role",
                description="Conversation participants may send messages.",
            )
        assert repeat.id == policy_id
        assert lane.last_response is not None
        assert lane.last_response.commit_id is None

        with pytest.raises(RuntimeError, match="field mismatch for existing policy"):
            with lane.activate(commit=True, publish=False):
                await action_config.allow_role_config(
                    role_config_id=role_config_id,
                    policy_key="invoke",
                    requirement_kind="admitted_actor_role",
                    description="A different policy description is a mismatch.",
                )

        with pytest.raises(RuntimeError, match="No ObjectProjectionGraph constructor"):
            with lane.activate(commit=True, publish=False):
                await RoleConfigInvocationActionConfig.build_via_experience_invocation_action_config(
                    experience_invocation_action_config_id=uuid5(
                        ns,
                        "missing_parent",
                    ),
                    role_config_id=role_config_id,
                    policy_key="invoke",
                    requirement_kind="admitted_actor_role",
                )

        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(action_config_id)
    assertions.expect_instance(action_config_id)
    assertions.expect_instance(policy_id)
    assertions.expect_edge(
        source_id=action_config_id,
        target_id=policy_id,
        relationship_name="role_policies",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=policy_id,
        field_name="experience_invocation_action_config_id",
        expected=action_config_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=policy_id,
        field_name="role_config_id",
        expected=role_config_id,
    )
    assertions.expect_primitive(
        instance_id=policy_id,
        field_name="policy_key",
        expected="invoke",
    )
    assertions.expect_primitive(
        instance_id=policy_id,
        field_name="requirement_kind",
        expected="admitted_actor_role",
    )
    assertions.expect_primitive(
        instance_id=policy_id,
        field_name="description",
        expected="Conversation participants may send messages.",
    )
