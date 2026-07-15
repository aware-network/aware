"""Node-scoped ActorRole ACL mode policy."""

from __future__ import annotations

import os
from typing import MutableMapping

ACTOR_ROLE_ACL_MODE_ENV = "AWARE_RUNTIME_ACTOR_ROLE_ACL_MODE"
NODE_ACTOR_ROLE_ACL_MODE = "enforce"


def lock_node_actor_role_acl_mode(
    *,
    env: MutableMapping[str, str] | None = None,
) -> str:
    """Hard-lock ActorRole ACL mode for Aware Node runtime rails."""
    target_env = env if env is not None else os.environ
    target_env[ACTOR_ROLE_ACL_MODE_ENV] = NODE_ACTOR_ROLE_ACL_MODE
    return NODE_ACTOR_ROLE_ACL_MODE
