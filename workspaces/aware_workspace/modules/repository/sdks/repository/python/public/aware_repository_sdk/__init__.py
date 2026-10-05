"""Repository preparation only; Issue and publication have their existing owners."""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Protocol

OPERATION_REF = "repository_sdk.prepare_repository"


@dataclass(frozen=True, slots=True)
class RepositoryPrepareRequest:
    repository_root: str
    create_if_missing: bool = False
    dry_run: bool = False

    def __post_init__(self):
        if type(self.repository_root) is not str or not Path(self.repository_root).is_absolute():
            raise ValueError("absolute_repository_root_required")
        if ".." in Path(self.repository_root).parts:
            raise ValueError("repository_parent_traversal_refused")
        if type(self.create_if_missing) is not bool or type(self.dry_run) is not bool:
            raise TypeError("repository_preparation_flags_must_be_boolean")


@dataclass(frozen=True, slots=True)
class RepositoryPrepareResult:
    outcome: str
    repository_root: str
    head: str | None = None
    diagnostics: tuple[str, ...] = ()
    operation_ref: str = OPERATION_REF
    authority_mode: str = "filesystem"

    def __post_init__(self):
        if self.outcome not in {"created", "existing", "planned", "refused"}:
            raise ValueError("repository_preparation_outcome_invalid")
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))

    def to_wire(self):
        return asdict(self)


class RepositoryPrepareProvider(Protocol):
    def prepare_repository(self, request: RepositoryPrepareRequest) -> RepositoryPrepareResult: ...


class RepositorySdkOperationClient:
    def __init__(self, *, provider: RepositoryPrepareProvider):
        self._provider = provider

    def prepare_repository(self, request: RepositoryPrepareRequest) -> RepositoryPrepareResult:
        if type(request) is not RepositoryPrepareRequest:
            raise TypeError("RepositoryPrepareRequest_required")
        result = self._provider.prepare_repository(request)
        if type(result) is not RepositoryPrepareResult or result.operation_ref != OPERATION_REF:
            raise TypeError("RepositoryPrepareResult_required")
        return result
