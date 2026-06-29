from __future__ import annotations

from uuid import uuid4

import pytest

from aware_reactivity.policy import (
    ReactivityModulePolicyProvider,
    ReactivityPolicyCoordinator,
    ReactivityPolicyDeclaration,
    ReactivityPolicyInstallRequest,
    ReactivityPolicyInstallResult,
    ReactivityPolicyInstaller,
    ReactivityPolicyRef,
)


class _Provider(ReactivityModulePolicyProvider):
    def __init__(self, declarations: list[ReactivityPolicyDeclaration]) -> None:
        self._declarations = declarations

    def list_policy_declarations(self) -> list[ReactivityPolicyDeclaration]:
        return list(self._declarations)


class _Installer(ReactivityPolicyInstaller):
    async def ensure(
        self,
        *,
        declaration: ReactivityPolicyDeclaration,
        request: ReactivityPolicyInstallRequest,
    ) -> ReactivityPolicyInstallResult:
        _ = request
        seed = uuid4()
        return ReactivityPolicyInstallResult(
            declaration=declaration,
            condition_config_id=seed,
            event_config_id=seed,
            event_config_condition_config_id=seed,
            action_config_id=None,
            event_config_action_config_id=None,
        )


def _declaration(*, module_id: str, key: str, version: int) -> ReactivityPolicyDeclaration:
    return ReactivityPolicyDeclaration(
        ref=ReactivityPolicyRef(
            module_id=module_id,
            policy_key=key,
            version=version,
        ),
        condition_name=key,
        condition_description=f"{key} condition",
        event_name=key,
        event_description=f"{key} event",
    )


def test_policy_coordinator_resolves_latest_version() -> None:
    coordinator = ReactivityPolicyCoordinator(
        providers=[
            _Provider(
                [
                    _declaration(
                        module_id="conversation",
                        key="conversation.message.created",
                        version=1,
                    ),
                    _declaration(
                        module_id="conversation",
                        key="conversation.message.created",
                        version=2,
                    ),
                ]
            )
        ]
    )

    resolved = coordinator.resolve(
        module_id="conversation",
        policy_key="conversation.message.created",
    )
    assert resolved.ref.version == 2


def test_policy_coordinator_rejects_conflicting_duplicate_declaration() -> None:
    a = ReactivityPolicyDeclaration(
        ref=ReactivityPolicyRef(
            module_id="conversation",
            policy_key="conversation.created",
            version=1,
        ),
        condition_name="conversation.created",
        condition_description="a",
        event_name="conversation.created",
        event_description="a",
    )
    b = ReactivityPolicyDeclaration(
        ref=ReactivityPolicyRef(
            module_id="conversation",
            policy_key="conversation.created",
            version=1,
        ),
        condition_name="conversation.created",
        condition_description="b",
        event_name="conversation.created",
        event_description="b",
    )
    coordinator = ReactivityPolicyCoordinator()
    coordinator.register_provider(provider=_Provider([a]))
    with pytest.raises(ValueError):
        coordinator.register_provider(provider=_Provider([b]))


@pytest.mark.asyncio
async def test_policy_coordinator_ensure_calls_installer() -> None:
    declaration = _declaration(
        module_id="conversation",
        key="conversation.created",
        version=1,
    )
    coordinator = ReactivityPolicyCoordinator(
        providers=[_Provider([declaration])],
        installer=_Installer(),
    )

    result = await coordinator.ensure(
        module_id="conversation",
        policy_key="conversation.created",
        request=ReactivityPolicyInstallRequest(
            actor_id=uuid4(),
        ),
    )

    assert result.declaration.ref.module_id == "conversation"
    assert result.declaration.ref.policy_key == "conversation.created"
