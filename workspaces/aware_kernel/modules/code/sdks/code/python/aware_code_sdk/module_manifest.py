from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

from aware_code_sdk.dto import (
    CodeSemanticManifestResolutionDescriptor,
    FindCodeSemanticManifestResolutionRequest,
)
from aware_code_sdk.manifest_resolution import CodeSdkManifestResolutionProvider


class CodeSdkModuleManifestProvider(Protocol):
    """Resolve and load `aware.module.toml` through Code semantic contracts."""

    def load_module_spec(self, *, toml_path: str | Path) -> object: ...


@dataclass(frozen=True, slots=True)
class SemanticContractCodeSdkModuleManifestProvider:
    manifest_resolution_provider: CodeSdkManifestResolutionProvider

    def load_module_spec(self, *, toml_path: str | Path) -> object:
        resolved_toml_path = Path(toml_path).expanduser().resolve()
        descriptor = _module_manifest_resolution_descriptor(
            provider=self.manifest_resolution_provider,
        )
        module = import_module(descriptor.loader_module)
        loader = cast(object, getattr(module, descriptor.loader_name))
        if not callable(loader):
            loader_ref = f"{descriptor.loader_module}.{descriptor.loader_name}"
            message = (
                f"Code semantic manifest resolver returned non-callable module "
                f"loader: {loader_ref}"
            )
            raise TypeError(message)
        return loader(toml_path=resolved_toml_path)


def _module_manifest_resolution_descriptor(
    *,
    provider: CodeSdkManifestResolutionProvider,
) -> CodeSemanticManifestResolutionDescriptor:
    response = provider.find_manifest_resolution(
        FindCodeSemanticManifestResolutionRequest(
            provider_key="aware_code",
            manifest_kind="aware_module_toml",
            filename="aware.module.toml",
            workspace_manifest_kind="module",
        )
    )
    if not response.success:
        message = (
            f"Code SDK failed to resolve aware.module.toml manifest ownership: "
            f"{response.error or 'unknown error'}"
        )
        raise LookupError(message)
    matches = tuple(response.matches)
    if not matches:
        raise LookupError(
            "Code SDK semantic contract did not resolve aware.module.toml"
        )
    return matches[0].manifest_resolution


__all__ = [
    "CodeSdkModuleManifestProvider",
    "SemanticContractCodeSdkModuleManifestProvider",
]
