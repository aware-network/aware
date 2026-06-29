from __future__ import annotations

from collections import defaultdict

from aware_reactivity.policy.contracts import (
    ReactivityModulePolicyProvider,
    ReactivityPolicyDeclaration,
    ReactivityPolicyInstallRequest,
    ReactivityPolicyInstallResult,
    ReactivityPolicyInstaller,
    ReactivityPolicyRef,
)


class ReactivityPolicyCoordinator:
    """
    Runtime-first coordinator for module-owned reactivity policy declarations/installers.

    Contract:
    - Modules own domain policy declarations.
    - Coordinator resolves declarations deterministically by (module_id, policy_key, version).
    - Installer execution is explicit and idempotency is delegated to installer logic.
    """

    def __init__(
        self,
        *,
        providers: list[ReactivityModulePolicyProvider] | None = None,
        installer: ReactivityPolicyInstaller | None = None,
    ) -> None:
        self._providers: list[ReactivityModulePolicyProvider] = []
        self._declaration_index: dict[ReactivityPolicyRef, ReactivityPolicyDeclaration] = {}
        self._versions_by_policy: dict[tuple[str, str], set[int]] = defaultdict(set)
        self._installer = installer

        for provider in providers or []:
            self.register_provider(provider=provider)

    def register_provider(self, *, provider: ReactivityModulePolicyProvider) -> None:
        self._providers.append(provider)
        for declaration in provider.list_policy_declarations():
            normalized = declaration.normalized()
            ref = normalized.ref
            if ref in self._declaration_index and self._declaration_index[ref] != normalized:
                raise ValueError(
                    "conflicting policy declaration for " f"{ref.module_id}:{ref.policy_key}:v{ref.version}"
                )
            self._declaration_index[ref] = normalized
            self._versions_by_policy[(ref.module_id, ref.policy_key)].add(ref.version)

    def set_installer(self, *, installer: ReactivityPolicyInstaller | None) -> None:
        self._installer = installer

    def list_policy_declarations(
        self,
        *,
        module_id: str | None = None,
    ) -> list[ReactivityPolicyDeclaration]:
        entries = list(self._declaration_index.values())
        if module_id is not None:
            wanted = module_id.strip()
            entries = [entry for entry in entries if entry.ref.module_id == wanted]
        return sorted(
            entries,
            key=lambda entry: (
                entry.ref.module_id,
                entry.ref.policy_key,
                entry.ref.version,
            ),
        )

    def resolve(
        self,
        *,
        module_id: str,
        policy_key: str,
        version: int | None = None,
    ) -> ReactivityPolicyDeclaration:
        normalized_module = module_id.strip()
        normalized_key = policy_key.strip()
        if version is None:
            versions = self._versions_by_policy.get((normalized_module, normalized_key), set())
            if not versions:
                raise KeyError(f"unknown reactivity policy: {normalized_module}:{normalized_key}")
            version = max(versions)
        ref = ReactivityPolicyRef(
            module_id=normalized_module,
            policy_key=normalized_key,
            version=int(version),
        )
        declaration = self._declaration_index.get(ref)
        if declaration is None:
            raise KeyError("unknown reactivity policy version: " f"{ref.module_id}:{ref.policy_key}:v{ref.version}")
        return declaration

    async def ensure(
        self,
        *,
        module_id: str,
        policy_key: str,
        request: ReactivityPolicyInstallRequest,
        version: int | None = None,
    ) -> ReactivityPolicyInstallResult:
        if self._installer is None:
            raise RuntimeError("reactivity policy installer is not configured")
        declaration = self.resolve(
            module_id=module_id,
            policy_key=policy_key,
            version=version,
        )
        return await self._installer.ensure(
            declaration=declaration,
            request=request,
        )
