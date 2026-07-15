from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_identity_ontology.organization.organization import Organization
from aware_identity_ontology.organization.organization_enums import (
    OrganizationMemberRole,
)

from aware_economy.stable_ids import (
    stable_smart_contract_config_id,
    stable_smart_contract_id,
)

from aware_agent.stable_ids import (
    stable_agent_config_id,
    stable_agent_id,
    stable_agent_process_id,
)

from aware_node_operator.kernel_ops.seed_keys import (
    load_seed_keypairs,
    resolve_seed_keypair,
)
from aware_node_operator.kernel_ops.seed_plan import (
    KernelSeedPlan,
    build_kernel_seed_plan,
)
from aware_node_operator.kernel_ops.seed_spec import KernelSeedSpec
from aware_node_operator.kernel_ops.seed_deterministic import (
    build_seed_agent_profile_request,
    economy_wallet_seed,
)
from aware_node_operator.kernel_ops.legacy_api_models import FunctionCallRequest


def _legacy_api_unavailable() -> RuntimeError:
    return RuntimeError(
        "Kernel seed apply requires the retired legacy `aware_api.client` rail. "
        "The helper is quarantined under `aware-node-operator`; use the SDK/API "
        "service rail for live product paths."
    )


try:
    from aware_api.client import AwareApiClient, AwareApiConfig
    from aware_api.context import AwareApiContext
except ImportError:

    class AwareApiConfig:  # type: ignore[no-redef]
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise _legacy_api_unavailable()

    class AwareApiContext:  # type: ignore[no-redef]
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise _legacy_api_unavailable()

    class AwareApiClient:  # type: ignore[no-redef]
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise _legacy_api_unavailable()


def _normalize_node_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    # `NetworkDuplexClient` appends `/{client_app}/{server_app}` to the configured endpoint.
    # Historically some callers passed an endpoint that already included `/interface/network_node`,
    # which results in a double path like `/interface/network_node/interface/network_node` and a 403.
    suffix = "/interface/network_node"
    trimmed = endpoint.rstrip("/")
    if trimmed.endswith(suffix):
        trimmed = trimmed[: -len(suffix)]
    return trimmed.rstrip("/")


def _resolve_function_id(*, class_config: Any, function_name: str) -> UUID:
    for fn in list(getattr(class_config, "function_configs", []) or []):
        if getattr(fn, "name", None) == function_name:
            return fn.id
    raise RuntimeError(
        f"Function not found on ClassConfig (class_config_id={getattr(class_config, 'id', None)}): {function_name}"
    )


def _resolve_node_endpoint(*, override: str | None = None) -> str:
    if override and override.strip():
        return _normalize_node_endpoint(override)
    endpoint = os.getenv("AWARE_NODE_WS_URL")
    if endpoint:
        return _normalize_node_endpoint(endpoint)
    base = os.getenv("AWARE_NODE_BASE_URL")
    if base:
        if base.startswith("http://"):
            return _normalize_node_endpoint("ws://" + base[len("http://") :])
        if base.startswith("https://"):
            return _normalize_node_endpoint("wss://" + base[len("https://") :])
        return _normalize_node_endpoint(base)
    raise RuntimeError(
        "Missing node endpoint. Set AWARE_NODE_WS_URL/AWARE_NODE_BASE_URL or pass --endpoint."
    )


@dataclass(frozen=True, slots=True)
class BootContext:
    environment_id: UUID
    process_id: UUID
    thread_id: UUID


@dataclass(frozen=True, slots=True)
class IdentityOpgRef:
    opg_id: UUID
    projection_hash: str


@contextmanager
def _lane_context(*, client: AwareApiClient, branch_id: UUID, projection_hash: str):
    prev = client.get_context()
    client.set_context(
        AwareApiContext(
            environment_id=prev.environment_id,
            process_id=prev.process_id,
            thread_id=prev.thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
    )
    try:
        yield
    finally:
        client.set_context(prev)


async def _resolve_boot_context(*, client: AwareApiClient) -> BootContext:
    boot = await client.get_boot_environment_descriptor()
    if boot.status != "ready" or boot.descriptor is None:
        raise RuntimeError(
            f"Boot environment is not ready: status={boot.status} error={boot.error}"
        )
    env_id = boot.descriptor.boot_environment_id
    process_id = boot.descriptor.process_id
    thread_id = boot.descriptor.thread_id
    if process_id is None or thread_id is None:
        raise RuntimeError(
            "Boot environment descriptor missing process_id/thread_id "
            f"(process_id={process_id} thread_id={thread_id})"
        )
    return BootContext(
        environment_id=env_id, process_id=process_id, thread_id=thread_id
    )


async def _resolve_identity_opg(*, client: AwareApiClient) -> IdentityOpgRef:
    desc = await client.describe_environment_config()
    identity_opg = next(
        (o for o in desc.opgs if (o.name or "").strip() == "Identity"), None
    )
    if identity_opg is None:
        raise RuntimeError("Identity OPG not found in describe_environment_config")
    if not (identity_opg.projection_hash or "").strip():
        raise RuntimeError("Identity OPG missing projection_hash")
    return IdentityOpgRef(
        opg_id=identity_opg.id, projection_hash=identity_opg.projection_hash
    )


def _build_seed_agent_profile_request(
    *,
    label: str,
    identity_id: UUID,
    spec_id: str,
    spec_version: int,
) -> dict[str, Any]:
    return build_seed_agent_profile_request(
        label=label,
        identity_id=identity_id,
        spec_id=spec_id,
        spec_version=spec_version,
    )


async def _ensure_identity_lane(
    *,
    client: AwareApiClient,
    actor_id: UUID,
    identity_id: UUID,
    public_key: str,
    identity_type: str,
    identity_opg_id: UUID,
    identity_projection_hash: str,
    signup_via_profile_function_id: UUID | None = None,
    create_profile_request: dict[str, Any] | None = None,
) -> None:
    head = await client.get_lane_head(
        branch_id=identity_id, projection_hash=identity_projection_hash
    )
    if head.commit_id is not None:
        return

    prev = client.get_context()
    client.set_context(
        AwareApiContext(
            environment_id=prev.environment_id,
            process_id=prev.process_id,
            thread_id=prev.thread_id,
            branch_id=identity_id,
            projection_hash=identity_projection_hash,
        )
    )
    try:
        if create_profile_request is None:
            await client.signup_identity(
                public_key=public_key,
                identity_type=identity_type,
                commit=True,
                publish=False,
            )
            return

        if signup_via_profile_function_id is None:
            raise RuntimeError(
                "signup_via_profile_function_id is required when create_profile_request is provided"
            )

        await client.invoke_function(
            FunctionCallRequest(
                call_target="opg_constructor",
                object_id=None,
                object_projection_graph_id=identity_opg_id,
                function_id=signup_via_profile_function_id,
                args=[],
                kwargs={
                    "public_key": public_key,
                    "create_profile_request": create_profile_request,
                },
                actor_id=actor_id,
                commit=True,
                publish=False,
            )
        )
    finally:
        client.set_context(prev)


def _economy_wallet_seed(*, identity_id: UUID) -> tuple[str, str, str, UUID]:
    """
    v0 deterministic economy wallet seed.

    This matches the FinanceEntity.build anti-footgun contract:
    - public_key = sha256(identity_id)
    - private_key_encrypted = "dev:" + sha256(identity_id)
    - wallet_id = stable_wallet_id(pub, priv)
    """

    seed = economy_wallet_seed(identity_id=identity_id)
    return (
        seed.address,
        seed.public_key,
        seed.private_key_encrypted,
        seed.wallet_id,
    )


async def apply_kernel_seed(
    *,
    spec_path: str,
    endpoint: str | None = None,
    include_economy: bool = True,
) -> KernelSeedPlan:
    """
    Apply the kernel seed (commit-only) to the node-managed BOOT environment.

    Invariants:
    - Uses real identity sessions (anti-claim enforced by identity.signup).
    - Checks lane heads for idempotent constructor ensures.
    - Never reads DB tables directly (commit-truth only).
    """

    spec = KernelSeedSpec.load(Path(spec_path))
    plan = build_kernel_seed_plan(spec)

    keypairs = load_seed_keypairs()

    node_endpoint = _resolve_node_endpoint(override=endpoint)

    system = plan.system_identity
    system_keypair = resolve_seed_keypair(
        keypairs=keypairs,
        identity_id=system.identity_id,
        identity_type_value="system",
    )

    system_client = AwareApiClient(
        AwareApiConfig(endpoint=node_endpoint, actor_id=system.actor_id)
    )
    try:
        boot_ctx = await _resolve_boot_context(client=system_client)
        system_client.set_context(
            AwareApiContext(
                environment_id=boot_ctx.environment_id,
                process_id=boot_ctx.process_id,
                thread_id=boot_ctx.thread_id,
                branch_id=None,
                projection_hash=None,
            )
        )
        await system_client.authenticate_identity_session(
            public_key=system_keypair.public_key,
            private_key=system_keypair.private_key,
        )

        identity_opg = await _resolve_identity_opg(client=system_client)

        # Ensure the system identity lane exists (OS-plane author).
        await _ensure_identity_lane(
            client=system_client,
            actor_id=system.actor_id,
            identity_id=system.identity_id,
            public_key=system_keypair.public_key,
            identity_type="system",
            identity_opg_id=identity_opg.opg_id,
            identity_projection_hash=identity_opg.projection_hash,
        )
    finally:
        await system_client.close()

    provider = plan.provider_org.provider
    org_keypair = resolve_seed_keypair(
        keypairs=keypairs,
        identity_id=provider.identity_id,
        identity_type_value="organization",
    )

    org_client = AwareApiClient(
        AwareApiConfig(endpoint=node_endpoint, actor_id=provider.actor_id)
    )
    org_client.set_context(
        AwareApiContext(
            environment_id=boot_ctx.environment_id,
            process_id=boot_ctx.process_id,
            thread_id=boot_ctx.thread_id,
            branch_id=None,
            projection_hash=None,
        )
    )
    await org_client.authenticate_identity_session(
        public_key=org_keypair.public_key, private_key=org_keypair.private_key
    )

    # Ensure provider org identity lane exists (must be authored by the org actor).
    await _ensure_identity_lane(
        client=org_client,
        actor_id=provider.actor_id,
        identity_id=provider.identity_id,
        public_key=org_keypair.public_key,
        identity_type="organization",
        identity_opg_id=identity_opg.opg_id,
        identity_projection_hash=identity_opg.projection_hash,
    )

    # Resolve OPGs required for organization + economy seeding (and agent bootstrap).
    desc = await org_client.describe_environment_config()
    agent_opg = next((o for o in desc.opgs if (o.name or "").strip() == "Agent"), None)
    if agent_opg is None:
        available = sorted({(o.name or "").strip() for o in desc.opgs})
        raise RuntimeError(f"Agent OPG not found (available={available})")

    from aware_agent_ontology.agent.agent import Agent
    from aware_agent_ontology.agent.process.agent_process import AgentProcess
    from aware_identity_ontology.identity.identity import Identity

    agent_build_fn_id = _resolve_function_id(
        class_config=Agent.ensure_class_config(),
        function_name="build_via_agent_config",
    )
    agent_create_process_fn_id = _resolve_function_id(
        class_config=Agent.ensure_class_config(), function_name="create_process"
    )
    agent_process_create_thread_fn_id = _resolve_function_id(
        class_config=AgentProcess.ensure_class_config(), function_name="create_thread"
    )
    identity_signup_via_profile_fn_id = _resolve_function_id(
        class_config=Identity.ensure_class_config(), function_name="signup_via_profile"
    )

    # Ensure executor agent identity lanes exist (must be authored by each agent).
    for ex in plan.executors:
        agent_keypair = resolve_seed_keypair(
            keypairs=keypairs,
            identity_id=ex.identity_id,
            identity_type_value="agent",
        )
        agent_client = AwareApiClient(
            AwareApiConfig(endpoint=node_endpoint, actor_id=ex.actor_id)
        )
        agent_client.set_context(org_client.get_context())
        await agent_client.authenticate_identity_session(
            public_key=agent_keypair.public_key, private_key=agent_keypair.private_key
        )
        try:
            await _ensure_identity_lane(
                client=agent_client,
                actor_id=ex.actor_id,
                identity_id=ex.identity_id,
                public_key=agent_keypair.public_key,
                identity_type="agent",
                identity_opg_id=identity_opg.opg_id,
                identity_projection_hash=identity_opg.projection_hash,
                signup_via_profile_function_id=identity_signup_via_profile_fn_id,
                create_profile_request=_build_seed_agent_profile_request(
                    label=ex.label,
                    identity_id=ex.identity_id,
                    spec_id=plan.spec_id,
                    spec_version=plan.spec_version,
                ),
            )

            # Ensure executor has a commit-backed AgentProcessThread (APT) ready for inference execution.
            #
            # Canonical contract:
            # - `agent` is its own projection branch (one projection per branch).
            # - Branch ID for the `agent` lane is the deterministic Agent.id.
            # - Agent/Process/Thread ids are deterministic from env_id + parent ids.
            agent_config_id = stable_agent_config_id(key="default")
            agent_id = stable_agent_id(
                agent_config_id=agent_config_id,
                identity_id=ex.identity_id,
                key="default",
            )
            agent_process_id = stable_agent_process_id(
                agent_id=agent_id,
                key="default",
            )

            lane_head = await agent_client.get_lane_head(
                branch_id=agent_id, projection_hash=agent_opg.projection_hash
            )
            if lane_head.commit_id is None:
                with _lane_context(
                    client=agent_client,
                    branch_id=agent_id,
                    projection_hash=agent_opg.projection_hash,
                ):
                    # Agent.build_via_agent_config (constructor).
                    await agent_client.invoke_function(
                        FunctionCallRequest(
                            call_target="opg_constructor",
                            object_id=None,
                            object_projection_graph_id=agent_opg.id,
                            function_id=agent_build_fn_id,
                            args=[],
                            kwargs={
                                "agent_config_id": agent_config_id,
                                "identity_id": ex.identity_id,
                                "key": "default",
                            },
                            actor_id=ex.actor_id,
                            commit=True,
                            publish=False,
                        )
                    )

                    # Agent.create_process (instance).
                    await agent_client.invoke_function(
                        FunctionCallRequest(
                            call_target="instance",
                            object_id=agent_id,
                            object_projection_graph_id=None,
                            function_id=agent_create_process_fn_id,
                            args=["default", "default"],
                            kwargs={},
                            actor_id=ex.actor_id,
                            commit=True,
                            publish=False,
                        )
                    )

                    # AgentProcess.create_thread (instance).
                    await agent_client.invoke_function(
                        FunctionCallRequest(
                            call_target="instance",
                            object_id=agent_process_id,
                            object_projection_graph_id=None,
                            function_id=agent_process_create_thread_fn_id,
                            args=["main", "Main", True],
                            kwargs={"system_instruction_text": "You are Aware."},
                            actor_id=ex.actor_id,
                            commit=True,
                            publish=False,
                        )
                    )
        finally:
            await agent_client.close()

    org_opg = next(
        (o for o in desc.opgs if (o.name or "").strip() == "Organization"), None
    )
    if org_opg is None:
        available = sorted({(o.name or "").strip() for o in desc.opgs})
        raise RuntimeError(f"Organization OPG not found (available={available})")

    # Ensure Organization root exists (org lane, authored by org actor).
    org_head = await org_client.get_lane_head(
        branch_id=plan.provider_org.organization_id,
        projection_hash=org_opg.projection_hash,
    )
    if org_head.commit_id is None:
        create_fn_id = _resolve_function_id(
            class_config=Organization.ensure_class_config(), function_name="create"
        )
        with _lane_context(
            client=org_client,
            branch_id=plan.provider_org.organization_id,
            projection_hash=org_opg.projection_hash,
        ):
            await org_client.invoke_function(
                FunctionCallRequest(
                    call_target="opg_constructor",
                    object_id=None,
                    object_projection_graph_id=org_opg.id,
                    function_id=create_fn_id,
                    args=[],
                    kwargs={"actor_id": provider.actor_id},
                    actor_id=provider.actor_id,
                    commit=True,
                    publish=False,
                )
            )

    # Ensure membership edges (idempotent instance function; should no-op when already present).
    create_member_fn_id = _resolve_function_id(
        class_config=Organization.ensure_class_config(), function_name="create_member"
    )
    prev_ctx = org_client.get_context()
    org_client.set_context(
        AwareApiContext(
            environment_id=prev_ctx.environment_id,
            process_id=prev_ctx.process_id,
            thread_id=prev_ctx.thread_id,
            branch_id=plan.provider_org.organization_id,
            projection_hash=org_opg.projection_hash,
        )
    )
    try:
        for member in plan.members:
            role_raw = member.role.strip().lower() or "member"
            allowed_roles = {r.value for r in OrganizationMemberRole}
            if role_raw not in allowed_roles:
                raise ValueError(
                    f"Invalid organization member role: {role_raw!r} (allowed={sorted(allowed_roles)})"
                )
            await org_client.invoke_function(
                FunctionCallRequest(
                    call_target="instance",
                    object_id=plan.provider_org.organization_id,
                    object_projection_graph_id=None,
                    function_id=create_member_fn_id,
                    args=[],
                    kwargs={
                        "identity_id": member.member_identity.identity_id,
                        "role": role_raw,
                    },
                    actor_id=provider.actor_id,
                    commit=True,
                    publish=False,
                )
            )
    finally:
        org_client.set_context(prev_ctx)

    if include_economy:
        # Economy seeding v0 (provider primitives: wallet, finance entity, contract).
        opgs_by_name = {
            (o.name or "").strip(): o for o in desc.opgs if (o.name or "").strip()
        }

        def require_opg(name: str):
            opg = opgs_by_name.get(name)
            if opg is None:
                available = sorted(opgs_by_name.keys())
                raise RuntimeError(
                    f"Missing required OPG: {name!r} (available={available})"
                )
            return opg

        wallet_opg = require_opg("Wallet")
        finance_entity_opg = require_opg("FinanceEntity")
        smart_contract_config_opg = require_opg("SmartContractConfig")
        smart_contract_opg = require_opg("SmartContract")

        # Wallet lane (deterministic).
        address, wallet_public_key, wallet_private_key_encrypted, wallet_id = (
            _economy_wallet_seed(identity_id=provider.identity_id)
        )
        wallet_head = await org_client.get_lane_head(
            branch_id=wallet_id, projection_hash=wallet_opg.projection_hash
        )
        if wallet_head.commit_id is None:
            from aware_economy_ontology.wallet.wallet import Wallet

            wallet_build_fn_id = _resolve_function_id(
                class_config=Wallet.ensure_class_config(), function_name="build"
            )
            with _lane_context(
                client=org_client,
                branch_id=wallet_id,
                projection_hash=wallet_opg.projection_hash,
            ):
                await org_client.invoke_function(
                    FunctionCallRequest(
                        call_target="opg_constructor",
                        object_id=None,
                        object_projection_graph_id=wallet_opg.id,
                        function_id=wallet_build_fn_id,
                        args=[],
                        kwargs={
                            "address": address,
                            "public_key": wallet_public_key,
                            "private_key_encrypted": wallet_private_key_encrypted,
                        },
                        actor_id=provider.actor_id,
                        commit=True,
                        publish=False,
                    )
                )

        # FinanceEntity lane (deterministic).
        provider_finance_entity_id = plan.economy.provider_finance_entity_id
        fe_head = await org_client.get_lane_head(
            branch_id=provider_finance_entity_id,
            projection_hash=finance_entity_opg.projection_hash,
        )
        if fe_head.commit_id is None:
            from aware_economy_ontology.finance.finance_entity import FinanceEntity

            fe_build_fn_id = _resolve_function_id(
                class_config=FinanceEntity.ensure_class_config(), function_name="build"
            )
            with _lane_context(
                client=org_client,
                branch_id=provider_finance_entity_id,
                projection_hash=finance_entity_opg.projection_hash,
            ):
                await org_client.invoke_function(
                    FunctionCallRequest(
                        call_target="opg_constructor",
                        object_id=None,
                        object_projection_graph_id=finance_entity_opg.id,
                        function_id=fe_build_fn_id,
                        args=[],
                        kwargs={
                            "identity_id": provider.identity_id,
                            "wallet_id": wallet_id,
                        },
                        actor_id=provider.actor_id,
                        commit=True,
                        publish=False,
                    )
                )

        # SmartContractConfig.
        scc_id = stable_smart_contract_config_id(
            name=spec.economy.smart_contract_config_name,
            type=spec.economy.smart_contract_type,
        )
        scc_head = await org_client.get_lane_head(
            branch_id=scc_id, projection_hash=smart_contract_config_opg.projection_hash
        )
        if scc_head.commit_id is None:
            from aware_economy_ontology.smart_contract.smart_contract_config import (
                SmartContractConfig,
            )

            scc_build_fn_id = _resolve_function_id(
                class_config=SmartContractConfig.ensure_class_config(),
                function_name="build",
            )
            with _lane_context(
                client=org_client,
                branch_id=scc_id,
                projection_hash=smart_contract_config_opg.projection_hash,
            ):
                await org_client.invoke_function(
                    FunctionCallRequest(
                        call_target="opg_constructor",
                        object_id=None,
                        object_projection_graph_id=smart_contract_config_opg.id,
                        function_id=scc_build_fn_id,
                        args=[],
                        kwargs={
                            "name": spec.economy.smart_contract_config_name,
                            "description": f"Seeded by kernel ops ({plan.spec_id})",
                            "type": spec.economy.smart_contract_type,
                            "smart_contract_schema": {},
                        },
                        actor_id=provider.actor_id,
                        commit=True,
                        publish=False,
                    )
                )

        # SmartContract instance.
        contract_id = stable_smart_contract_id(
            smart_contract_config_id=scc_id,
            blockchain_address=spec.economy.smart_contract_address,
        )
        contract_head = await org_client.get_lane_head(
            branch_id=contract_id, projection_hash=smart_contract_opg.projection_hash
        )
        if contract_head.commit_id is None:
            from aware_economy_ontology.smart_contract.smart_contract import (
                SmartContract,
            )

            contract_build_fn_id = _resolve_function_id(
                class_config=SmartContract.ensure_class_config(),
                function_name="build_via_smart_contract_config",
            )
            with _lane_context(
                client=org_client,
                branch_id=contract_id,
                projection_hash=smart_contract_opg.projection_hash,
            ):
                await org_client.invoke_function(
                    FunctionCallRequest(
                        call_target="opg_constructor",
                        object_id=None,
                        object_projection_graph_id=smart_contract_opg.id,
                        function_id=contract_build_fn_id,
                        args=[],
                        kwargs={
                            "smart_contract_config_id": scc_id,
                            "blockchain_address": spec.economy.smart_contract_address,
                            "status": "active",
                            "arguments": {},
                        },
                        actor_id=provider.actor_id,
                        commit=True,
                        publish=False,
                    )
                )

    await org_client.close()
    return plan


__all__ = ["apply_kernel_seed", "BootContext", "KernelSeedPlan"]
