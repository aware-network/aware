"""Pure selected-closure checks and qualified indexing; never policy grants.

Original Workspace validation remains necessary. Profile-package membership and
legacy-to-live provider correspondence must be supplied by their owning admission
join before registry policy can consume these portable relationships.
"""

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    CodeRetainedDependencyScopeClosure,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec import (
    encode_dependency_scope_closure,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec_v2 import (
    encode_dependency_scope_closure_v2,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDependencyScopeClosureV3,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    encode_retained_declaration_scope,
)


def validate_selected_scope_graph(closure: CodeRetainedDependencyScopeClosure) -> None:
    """Require canonical complete portable graph, exact local selectors and a DAG."""
    encode_dependency_scope_closure(closure)
    _validate_graph(closure)


def validate_selected_scope_graph_v2(
    closure: CodeRetainedDependencyScopeClosureV2,
) -> None:
    """Validate v2 portable closure and the same graph law without v1 conversion."""
    encode_dependency_scope_closure_v2(closure)
    _validate_graph(closure)


def validate_selected_scope_graph_v3(
    closure: CodeRetainedDependencyScopeClosureV3,
) -> None:
    """Validate declaration-only v3 bytes and the existing qualified graph law."""
    encode_retained_declaration_scope(closure)
    _validate_graph(closure)


def _validate_graph(closure):
    scopes = {s.scope_key: s for s in closure.scopes}
    handles = [s.workspace_handle for s in closure.scopes]
    if len(handles) != len(set(handles)):
        raise ContractViolation("ambiguous selected Workspace handles")
    graph = {key: set() for key in scopes}
    for edge in closure.edges:
        for restriction in (
            edge.channel,
            edge.revision,
            edge.profile_key,
            edge.semantic_contract_provider_keys,
        ):
            if restriction.state != "present" or not restriction.value:
                raise ContractViolation("complete nonempty edge restrictions required")
        handle = scopes[edge.target_scope_key].workspace_handle
        if (
            edge.dependency_kind != "workspace"
            or edge.dependency_source != f"workspace://{handle}"
            or edge.channel.value != "local"
            or edge.revision.value != "workspace-revision:local"
            or edge.profile_package_ref
            != f"workspace://{handle}#{edge.profile_key.value}"
        ):
            raise ContractViolation("unsupported or inconsistent dependency selector")
        graph[edge.declaring_scope_key].add(edge.target_scope_key)
    visiting = set()
    visited = set()

    def visit(key):
        if key in visiting:
            raise ContractViolation(f"selected provider-import cycle at {key}")
        if key in visited:
            return
        visiting.add(key)
        for target in sorted(graph[key]):
            if target in visiting:
                witnesses = tuple(
                    (
                        e.declaring_scope_key,
                        e.declaration.dependency_index,
                        e.declaration.profile_package_index,
                        e.target_scope_key,
                    )
                    for e in closure.edges
                    if e.declaring_scope_key == key and e.target_scope_key == target
                )
                raise ContractViolation(
                    f"selected provider-import cycle edges: {witnesses!r}"
                )
            visit(target)
        visiting.remove(key)
        visited.add(key)

    visit(closure.consumer_scope_key)
    if visited != set(scopes):
        raise ContractViolation("unreachable selected dependency scope")


def qualified_package_index(closure: CodeRetainedDependencyScopeClosure):
    """Index by scope/module/package; returned portable rows are not membership.

    Do not use this index to infer profile entitlement, an original admission or
    execution readiness. No package lookup drops its declaring scope coordinate.
    """
    validate_selected_scope_graph(closure)
    return {
        (scope.scope_key, package.module_id, package.package_id): package
        for scope in closure.scopes
        for package in scope.projection.packages
    }
