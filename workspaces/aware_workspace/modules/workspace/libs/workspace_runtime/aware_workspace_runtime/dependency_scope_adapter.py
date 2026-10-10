"""Separate preliminary and per-use v2 readers; fixed origin trust is external."""

import inspect

from aware_code_semantic_contract_runtime.dependency_scope_closure_codec_v2 import (
    encode_dependency_scope_closure_v2,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
)

from .dependency_scope_admission import WorkspaceDependencyScopeRuntime
from .dependency_scope_declarations import refuse


class WorkspaceCodeDependencyScopeAdapter:
    def __init__(self, *, runtime: WorkspaceDependencyScopeRuntime):
        if type(runtime) is not WorkspaceDependencyScopeRuntime:
            raise TypeError("original dependency source runtime required")
        self._runtime = runtime
        self._reader = runtime.read_preliminary_closure
        self._descriptor = inspect.getattr_static(runtime, "read_preliminary_closure")
        self._operation_reader = runtime.read_dependency_scope_closure
        self._operation_descriptor = inspect.getattr_static(
            runtime, "read_dependency_scope_closure"
        )

    def _origin(self):
        if (
            not inspect.ismethod(self._reader)
            or self._reader.__self__ is not self._runtime
            or self._reader.__func__ is not self._descriptor
            or inspect.getattr_static(self._runtime, "read_preliminary_closure")
            is not self._descriptor
        ):
            refuse("dependency_projection_reader_changed")

    def read_preliminary_dependency_scope_projection(
        self, source
    ) -> CodeRetainedDependencyScopeClosureV2:
        self._origin()
        result = self._reader(source)
        self._origin()
        if type(result) is not CodeRetainedDependencyScopeClosureV2:
            refuse("dependency_projection_version_changed")
        encode_dependency_scope_closure_v2(result)
        return result

    def read_dependency_scope_closure(
        self, source, *, expected
    ) -> CodeRetainedDependencyScopeClosureV2:
        def check():
            self._origin()
            if (
                not inspect.ismethod(self._operation_reader)
                or self._operation_reader.__self__ is not self._runtime
                or self._operation_reader.__func__ is not self._operation_descriptor
                or inspect.getattr_static(
                    self._runtime, "read_dependency_scope_closure"
                )
                is not self._operation_descriptor
            ):
                refuse("dependency_operation_reader_changed")

        check()
        result = self._operation_reader(source, expected=expected)
        check()
        if type(result) is not CodeRetainedDependencyScopeClosureV2:
            refuse("dependency_projection_version_changed")
        encode_dependency_scope_closure_v2(result)
        return result
