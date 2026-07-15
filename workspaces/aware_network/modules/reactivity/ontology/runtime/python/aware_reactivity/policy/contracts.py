from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ReactivityPolicyRef:
    module_id: str
    policy_key: str
    version: int

    def normalized(self) -> ReactivityPolicyRef:
        return ReactivityPolicyRef(
            module_id=self.module_id.strip(),
            policy_key=self.policy_key.strip(),
            version=int(self.version),
        )


@dataclass(frozen=True, slots=True)
class ReactivityPolicyDeclaration:
    ref: ReactivityPolicyRef
    condition_name: str
    condition_description: str
    event_name: str
    event_description: str
    tags: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def normalized(self) -> ReactivityPolicyDeclaration:
        normalized_tags = tuple(tag.strip() for tag in self.tags if isinstance(tag, str) and tag.strip())
        normalized_metadata = dict(self.metadata)
        return ReactivityPolicyDeclaration(
            ref=self.ref.normalized(),
            condition_name=self.condition_name.strip(),
            condition_description=self.condition_description.strip(),
            event_name=self.event_name.strip(),
            event_description=self.event_description.strip(),
            tags=normalized_tags,
            metadata=normalized_metadata,
        )


@dataclass(frozen=True, slots=True)
class ReactivityPolicyInstallRequest:
    actor_id: UUID
    branch_id: UUID | None = None
    projection_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ReactivityPolicyInstallResult:
    declaration: ReactivityPolicyDeclaration
    condition_config_id: UUID
    event_config_id: UUID
    event_config_condition_config_id: UUID
    action_config_id: UUID | None = None
    event_config_action_config_id: UUID | None = None


class ReactivityModulePolicyProvider(Protocol):
    def list_policy_declarations(self) -> list[ReactivityPolicyDeclaration]: ...


class ReactivityPolicyInstaller(Protocol):
    async def ensure(
        self,
        *,
        declaration: ReactivityPolicyDeclaration,
        request: ReactivityPolicyInstallRequest,
    ) -> ReactivityPolicyInstallResult: ...
