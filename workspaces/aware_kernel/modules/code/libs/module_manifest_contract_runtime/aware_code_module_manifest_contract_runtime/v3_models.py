"""Portable qualified v3 address meaning, never admitted Workspace membership."""

from dataclasses import dataclass

from .models import AwareModuleSpec
from .v2_models import PackageDeclarationV2


@dataclass(frozen=True, slots=True)
class QualifiedModuleAddress:
    scope_kind: str
    workspace_handle: str | None
    module_id: str
    package_id: str
    registration_key: str | None = None

    @property
    def ordering_key(self) -> tuple[bytes, bytes, bytes, bytes, bytes]:
        """Scope participates in identity; no name-only cross-scope deduplication."""
        return (
            self.scope_kind.encode("utf-8"),
            (self.workspace_handle or "").encode("utf-8"),
            self.module_id.encode("utf-8"),
            self.package_id.encode("utf-8"),
            (self.registration_key or "").encode("utf-8"),
        )


@dataclass(frozen=True, slots=True)
class AwareModuleSpecV3(AwareModuleSpec):
    """Full module meaning, sharing unchanged declaration fields with v2."""

    package_declarations: tuple[PackageDeclarationV2, ...] = ()
