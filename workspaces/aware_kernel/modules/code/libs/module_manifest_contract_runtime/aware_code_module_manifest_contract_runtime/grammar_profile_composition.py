"""Authored profile/data correspondence inside the original owner boundary.

The future Policy constructor supplies the original catalog and registered
Workspace input. These synchronous helpers authenticate neither a detached
input's origin nor its lifetime. They perform no IO, registration, admission,
release, native assembly, provider invocation or retry.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    CodeGrammarSourceRoleSelectionV1,
    encode_grammar_source_role_selection,
)
from aware_code_semantic_contract_runtime.grammar_profile_codec import (
    CodeGrammarProfileSelectionCodec,
    CodeGrammarSyntaxBindingCodec,
    grammar_profile_selection_body,
    grammar_syntax_binding_body,
)
from aware_code_semantic_contract_runtime.grammar_profile_contract import (
    MAX_GRAMMAR_BODY_BYTES,
    MAX_GRAMMAR_CONTRIBUTIONS,
    CodeGrammarAnchorRequirementV1,
    CodeGrammarContributionBindingV1,
    CodeGrammarDeclarationSourceV1,
    CodeGrammarProviderBindingV2,
    CodeGrammarSyntaxBindingV2,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    read_grammar_declaration_context,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputJoinedProductionInput,
)
from aware_code_semantic_contract_runtime.source_origin import (
    SemanticInputSourceOrigin,
    decode_source_origin,
    source_occurrence_ref,
)

from .grammar_profile_source import (
    GrammarProfileSourceError,
    _read_grammar_v2_product_nomination,
    parse_grammar_provider_module,
    parse_registered_grammar_profile,
)
from .models import AwareModulePackageSemanticContractSyntaxSpec
from .profile_models import (
    CodeSemanticContractProfileManifestSpecV2,
    CodeSemanticContractProfileProviderSpecV2,
)
from .syntax_declaration import syntax_declaration_digest
from .v3_models import AwareModuleSpecV3

if TYPE_CHECKING:
    from aware_language_parsed_document_contract import (
        SyntaxContributionV1,
        SyntaxSourceBindingV1,
    )

from aware_code_semantic_contract_runtime.grammar_input_codecs import (
    validate_grammar_source_role_selection,
)
from aware_code_semantic_contract_runtime.profile import (
    SemanticContractProfileDeclaration,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProductionInput,
)

from .grammar_profile_source import (
    MAX_GRAMMAR_PROFILE_PROVIDERS,
)


def _produce_profile_selection(
    input: SemanticInputProductionInput,
    *,
    selection: CodeGrammarSourceRoleSelectionV1,
    profile: SemanticContractProfileDeclaration,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
    stage: str,
) -> SemanticBody:
    """Interpret the exact selected table against a complete original catalog.

    Occurrences are explicit selectors in authored provider order, not display
    labels or authority. The complete registered profile supplies its own ref,
    version, contracts and graph; none is inferred from TOML or the selector.
    The original registered executor must validate source/context currentness
    before and after this helper and retain its result through the original host.
    A manufactured self-consistent input remains data, even with a live catalog.
    """
    if type(input) is not SemanticInputProductionInput:
        raise TypeError("exact grammar production input required")
    if type(selection) is not CodeGrammarSourceRoleSelectionV1:
        raise TypeError("exact grammar source selection required")
    if type(profile) is not SemanticContractProfileDeclaration:
        raise TypeError("exact complete grammar interpretation profile required")
    if type(catalog) is not CodeSemanticContractCatalogResolver:
        raise TypeError("original Code catalog resolver required")
    if (
        type(provider_occurrences) is not tuple
        or len(provider_occurrences) > MAX_GRAMMAR_PROFILE_PROVIDERS
        or any(type(row) is not str for row in provider_occurrences)
    ):
        raise TypeError("exact bounded provider occurrence tuple required")

    # Close the existing input, original shared budget and selection graph
    # before any parser/catalog callback. No new source window or budget exists.
    validate_grammar_source_role_selection(selection, input=input)
    if selection.stage != stage or input.package_identity.package.package_kind not in (
        "code",
        "ontology",
        "sdk",
    ):
        raise ContractViolation("grammar profile role/package differs")
    profile.__post_init__()
    group, closure = read_grammar_declaration_context(input)
    publication = next(
        row
        for row in closure.local_profiles
        if row.owning_scope_key == selection.profile_source.scope_key
        and row.profile_key == selection.profile_key
    )
    authored = parse_registered_grammar_profile(
        publication.manifest.body, profile_key=selection.profile_key
    )
    authored_keys = tuple(row.provider_key for row in authored.providers)
    is_v2 = type(authored) is CodeSemanticContractProfileManifestSpecV2
    if (
        len(provider_occurrences) != len(authored.providers)
        or set(authored_keys) != {row.provider_key for row in profile.providers}
        or len(authored_keys) != len(profile.providers)
    ):
        raise ContractViolation(
            "complete authored/registered provider inventory differs"
        )

    members = {row.occurrence_ref: row for row in group.members}
    scopes = {row.scope_key: row for row in closure.scopes}
    before = []
    for declared, occurrence_ref in zip(
        authored.providers, provider_occurrences, strict=True
    ):
        member = members.get(occurrence_ref)
        if member is None:
            raise ContractViolation("explicit grammar provider occurrence unavailable")
        origin = decode_source_origin(bytes.fromhex(member.origin_body_hex))
        occurrence = origin.occurrence
        if (
            occurrence.scope_key != selection.profile_source.scope_key
            or occurrence.module_id != declared.module_id
        ):
            raise ContractViolation("authored provider occurrence scope/module differs")
        scope = scopes[occurrence.scope_key]
        module = next(
            row
            for row in scope.projection.modules
            if row.module_id == declared.module_id
        )
        parsed_module, package = parse_grammar_provider_module(
            module.manifest.body,
            package_id=occurrence.package_id,
            provider_key=declared.provider_key,
        )
        retained = next(
            row
            for row in scope.projection.packages
            if row.module_id == occurrence.module_id
            and row.package_id == occurrence.package_id
        )
        manifest_path = str(
            PurePosixPath(module.manifest.relative_path).parent / package.manifest
        )
        if (
            package.kind != retained.package_kind
            or manifest_path != retained.manifest.relative_path
        ):
            raise ContractViolation(
                "authored package differs from enclosing occurrence"
            )
        if is_v2:
            if (
                type(parsed_module) is not AwareModuleSpecV3
                or type(declared) is not CodeSemanticContractProfileProviderSpecV2
            ):
                raise GrammarProfileSourceError(
                    "exact V3 product declaration required",
                    reason="syntax_provider_declaration_mismatch",
                )
            if (
                occurrence.package_id != declared.package_id
                or occurrence.repository_binding_ref != closure.repository_binding_ref
                or occurrence.package_root
                != ("" if retained.package_root == "." else retained.package_root)
                or occurrence.outer_manifest_path != retained.manifest_relative_path
            ):
                raise ContractViolation(
                    "authored V2 qualified package occurrence differs"
                )
            nomination = _read_grammar_v2_product_nomination(
                parsed_module, declared=declared
            )
            if (
                profile.profile_ref,
                profile.version,
                profile.digest.value,
            ) != nomination:
                raise ContractViolation("authored V2 full product nomination differs")
            catalog.validate_catalog()
            products = tuple(
                row
                for row in catalog.catalog.entries
                if row.semantic_provider_key == declared.provider_key
                and (
                    row.profile_declaration.profile_ref,
                    row.profile_declaration.version,
                    row.profile_declaration.digest.value,
                )
                == nomination
                and len(row.profile_declaration.providers) == 1
                and row.profile_declaration.providers[0].provider_key
                == declared.provider_key
            )
            catalog.validate_catalog()
            if len(products) != 1 or products[0].profile_declaration != profile:
                raise ContractViolation(
                    "complete original V2 product is absent or ambiguous"
                )
        binding = catalog.read_profile_binding(
            profile=profile, semantic_provider_key=declared.provider_key
        )
        before.append(binding)

    result = grammar_profile_selection_body(profile)
    # The catalog owner checks its retained full closure on every read. Compare
    # full bindings as well, preserving all execution and planner coordinates.
    for declared, original in zip(authored.providers, before, strict=True):
        if (
            catalog.read_profile_binding(
                profile=profile, semantic_provider_key=declared.provider_key
            )
            != original
        ):
            raise ContractViolation(
                "original grammar catalog changed during interpretation"
            )
    validate_grammar_source_role_selection(selection, input=input)
    return result


def produce_grammar_profile_selection(
    input: SemanticInputProductionInput,
    *,
    selection: CodeGrammarSourceRoleSelectionV1,
    profile: SemanticContractProfileDeclaration,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
) -> SemanticBody:
    """Original profile-only entrance; no new stage or execution fallback."""
    return _produce_profile_selection(
        input,
        selection=selection,
        profile=profile,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
        stage="profile_selection",
    )


def validate_grammar_profile_selection_result(
    result: SemanticBody,
    *,
    input: SemanticInputProductionInput,
    selection: CodeGrammarSourceRoleSelectionV1,
    profile: SemanticContractProfileDeclaration,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
) -> None:
    """Reconstruct full source correspondence; never admit a copied result.

    Byte equality cannot prove retention or source origin. The original host
    separately validates its nominal registration/result/use before and after
    this data check. No returned body, digest or restored source renews that use.
    """
    if type(result) is not SemanticBody:
        raise TypeError("exact grammar profile body required")
    if type(result.canonical_body) is not bytes:
        raise TypeError("exact grammar profile bytes required")
    result.__post_init__()
    decoded = CodeGrammarProfileSelectionCodec().decode(result.canonical_body)
    canonical = grammar_profile_selection_body(decoded)
    if result != canonical:
        raise ContractViolation("complete grammar profile result coordinate differs")
    expected = produce_grammar_profile_selection(
        input,
        selection=selection,
        profile=profile,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
    )
    if result != expected:
        raise ContractViolation(
            "grammar profile result differs from selected source/catalog"
        )


def _source_projection(
    origin: SemanticInputSourceOrigin, path: str
) -> SyntaxSourceBindingV1:
    from aware_language_parsed_document_contract import (
        SyntaxAssemblyContractError,
        SyntaxSourceBindingV1,
    )

    rows = tuple(row for row in origin.sources if row.source.relative_path == path)
    if len(rows) != 1:
        raise SyntaxAssemblyContractError(
            "original contribution/scanner source unavailable",
            code="syntax_contribution_source_missing",
        )
    row = rows[0]
    address = source_occurrence_ref(origin.occurrence, path)
    if row.occurrence_ref != address:
        raise ContractViolation("original source occurrence address differs")
    return SyntaxSourceBindingV1(
        origin.occurrence.occurrence_ref,
        address,
        origin.package.package_ref,
        path,
        row.source.coordinate.size_bytes,
        row.source.coordinate.digest.value,
    )


def produce_grammar_source_binding(
    input: SemanticInputJoinedProductionInput,
    *,
    selection: CodeGrammarSourceRoleSelectionV1,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
    observed_contributions: tuple[tuple[str, str, SemanticBody], ...],
) -> SemanticBody:
    return _produce_source_binding(
        input,
        selection=selection,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
        observed_contributions=observed_contributions,
    )


def reconstruct_grammar_source_binding(
    input: SemanticInputJoinedProductionInput,
    *,
    selection: CodeGrammarSourceRoleSelectionV1,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
) -> SemanticBody:
    """Code output data reconstruction; registered execution owns admission.

    Every selected authored contribution must have no dependencies. A nonempty
    inventory refuses intact; it is never emptied or filtered to obtain success.
    """
    return _produce_source_binding(
        input,
        selection=selection,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
        observed_contributions=None,
        rebuilding=True,
    )


def reconstruct_grammar_local_dependency_binding(
    input: SemanticInputJoinedProductionInput,
    *,
    selection: CodeGrammarSourceRoleSelectionV1,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
) -> SemanticBody:
    """Portable local dependency correspondence, never source admission.

    Dependencies must name complete selected contributions in the same package
    occurrence. The original registered owner authenticates the whole source
    input and lifetime. Group membership/edges alone cannot admit foreign targets.
    The existing dependency-free entrance keeps its refusal behavior.
    """
    return _produce_source_binding(
        input,
        selection=selection,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
        observed_contributions=None,
        rebuilding=True,
        local_dependencies=True,
    )


def reconstruct_grammar_group_dependency_binding(
    input: SemanticInputJoinedProductionInput,
    *,
    selection: CodeGrammarSourceRoleSelectionV1,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
) -> SemanticBody:
    """Complete selected grouped dependency data, never an admission port.

    The original registered producer authenticates the Workspace grouped input,
    its retained results, target edges and lifetime before and after this helper.
    Portable edges alone cannot grant execution. Each cross-occurrence target
    must be a complete selected contribution reached by a direct grouped edge;
    this does not invent materialized-product demands or invoke assembly.
    """
    return _produce_source_binding(
        input,
        selection=selection,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
        observed_contributions=None,
        rebuilding=True,
        grouped_dependencies=True,
    )


def _produce_source_binding(
    input: SemanticInputJoinedProductionInput,
    *,
    selection: CodeGrammarSourceRoleSelectionV1,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
    observed_contributions: tuple[tuple[str, str, SemanticBody], ...] | None,
    rebuilding: bool = False,
    local_dependencies: bool = False,
    grouped_dependencies: bool = False,
) -> SemanticBody:
    """Preserve original observed coordinates after complete data correspondence.

    The joined predecessor and observed bodies are portable data, not original
    registrations. This validates their bytes/coordinates against the supplied
    original source projections; the host must separately verify provenance,
    retained-result ownership, admitted dependency evidence and currentness.
    """
    from aware_language_parsed_document_contract import (
        SyntaxAssemblyContractError,
        SyntaxContractRefV1,
        SyntaxContributionSourceV1,
        decode_syntax_assembly_value,
        encode_syntax_assembly_value,
    )
    from aware_language_syntax_assembly import reconstruct_syntax_contribution

    if type(input) is not SemanticInputJoinedProductionInput:
        raise TypeError("exact joined grammar input required")
    input.__post_init__()
    if type(selection) is not CodeGrammarSourceRoleSelectionV1:
        raise TypeError("exact grammar source selection required")
    if (
        len(input.predecessors) != 1
        or input.predecessors[0].role != "code.profile_selection"
    ):
        raise ContractViolation("one complete profile predecessor required")
    previous = input.predecessors[0]
    predecessor_snapshot = (
        canonical_json_bytes(previous.coordinate.to_wire()),
        previous.canonical_body,
        input.predecessor_closure_digest.value,
    )
    ordinary_digest = input.ordinary.input_digest.value
    profile = CodeGrammarProfileSelectionCodec().decode(previous.canonical_body)
    if previous.coordinate != grammar_profile_selection_body(profile).coordinate:
        raise ContractViolation("complete profile predecessor coordinate differs")
    if not rebuilding and (
        type(observed_contributions) is not tuple
        or not (1 <= len(observed_contributions) <= MAX_GRAMMAR_CONTRIBUTIONS)
    ):
        raise TypeError("exact bounded observed contribution tuple required")
    observed: dict[tuple[str, str], SemanticBody] = {}
    observed_snapshots: dict[tuple[str, str], tuple[bytes, bytes]] = {}
    total = len(encode_grammar_source_role_selection(selection)) + sum(
        len(row.canonical_body)
        for row in (
            *input.ordinary.sources,
            *input.ordinary.context_bodies,
            *input.predecessors,
        )
    )
    for row in observed_contributions or ():
        if type(row) is not tuple or len(row) != 3:
            raise TypeError("exact observed occurrence/path/body row required")
        occurrence, path, body = row
        if (
            type(occurrence) is not str
            or type(path) is not str
            or type(body) is not SemanticBody
        ):
            raise TypeError("exact observed contribution fields required")
        body.__post_init__()
        total += len(body.canonical_body)
        if (occurrence, path) in observed:
            raise ContractViolation("duplicate observed contribution source")
        observed[occurrence, path] = body
        observed_snapshots[occurrence, path] = (
            canonical_json_bytes(body.coordinate.to_wire()),
            body.canonical_body,
        )
    if total > MAX_GRAMMAR_BODY_BYTES:
        raise ContractViolation("joined grammar aggregate byte budget exceeded")
    keys = tuple(observed)
    if keys != tuple(sorted(keys, key=lambda key: (key[0].encode(), key[1].encode()))):
        raise ContractViolation("observed contribution inventory must be ordered")

    _ = _produce_profile_selection(
        input.ordinary,
        selection=selection,
        profile=profile,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
        stage="syntax_binding",
    )
    group, closure = read_grammar_declaration_context(input.ordinary)
    publication = next(
        row
        for row in closure.local_profiles
        if row.owning_scope_key == selection.profile_source.scope_key
        and row.profile_key == selection.profile_key
    )
    authored = parse_registered_grammar_profile(
        publication.manifest.body, profile_key=selection.profile_key
    )
    members = {row.occurrence_ref: row for row in group.members}
    scopes = {row.scope_key: row for row in closure.scopes}
    providers = {row.provider_key: row for row in profile.providers}
    provider_bindings = []
    contribution_bindings = []
    anchors: dict[bytes, CodeGrammarAnchorRequirementV1] = {}
    contributions: dict[str, tuple[str, SyntaxContributionV1]] = {}
    selected_sources: set[tuple[str, str]] = set()

    for declared, occurrence_ref in zip(
        authored.providers, provider_occurrences, strict=True
    ):
        member = members[occurrence_ref]
        origin = decode_source_origin(bytes.fromhex(member.origin_body_hex))
        scope = scopes[origin.occurrence.scope_key]
        module = next(
            row
            for row in scope.projection.modules
            if row.module_id == declared.module_id
        )
        _, package = parse_grammar_provider_module(
            module.manifest.body,
            package_id=origin.occurrence.package_id,
            provider_key=declared.provider_key,
        )
        declaration = package.semantic_contract
        if type(declaration) is not AwareModulePackageSemanticContractSyntaxSpec:
            raise ContractViolation("original syntax declaration variant differs")
        syntax = declaration.syntax
        provider = providers[declared.provider_key]
        owner = SyntaxContractRefV1(
            provider.provider_contract.key,
            provider.provider_contract.version,
            provider.provider_contract.schema_digest.value,
        )
        manifest = module.manifest
        provider_bindings.append(
            CodeGrammarProviderBindingV2(
                occurrence_ref,
                declared.module_id,
                declared.provider_key,
                provider.provider_contract,
                CodeGrammarDeclarationSourceV1(
                    closure.repository_binding_ref,
                    scope.scope_key,
                    "module",
                    manifest.relative_path,
                    manifest.body_ref,
                    manifest.content_digest,
                    len(manifest.body),
                ),
                ContentDigest(syntax_declaration_digest(syntax)),
            )
        )
        for anchor in syntax.anchors:
            expected_refs = tuple(
                ref
                for role in provider.consumed_roles
                if role.role == anchor.role
                for ref in role.accepted_contracts
                if (ref.key, ref.version, ref.schema_digest.value)
                == (
                    anchor.consumer_contract.key,
                    anchor.consumer_contract.version,
                    anchor.consumer_contract.schema_digest,
                )
            )
            if len(expected_refs) != 1:
                raise ContractViolation(
                    "anchor differs from complete registered consumer role"
                )
            value = CodeGrammarAnchorRequirementV1(
                declared.provider_key,
                expected_refs[0],
                anchor.role,
                anchor.rule_name,
                anchor.field_path,
                anchor.required,
                anchor.top_level,
            )
            key = canonical_json_bytes(value.to_wire())
            if key in anchors:
                raise ContractViolation("duplicate complete grammar anchor requirement")
            anchors[key] = value

        raw_sources = {
            row.relative_path: bytes.fromhex(row.body_hex) for row in member.sources
        }
        for path in syntax.contributions:
            source_key = occurrence_ref, path
            if source_key in selected_sources:
                raise ContractViolation("one authored source selected more than once")
            selected_sources.add(source_key)
            source = _source_projection(origin, path)
            if path not in raw_sources or (
                not rebuilding and source_key not in observed
            ):
                raise SyntaxAssemblyContractError(
                    "selected contribution source/result missing",
                    code="syntax_contribution_source_missing",
                )
            raw = raw_sources[path]
            payload = decode_syntax_assembly_value(
                raw, expected_type=SyntaxContributionSourceV1
            )
            if type(payload) is not SyntaxContributionSourceV1:
                raise ContractViolation("original Language source root differs")
            account = [(source, raw)]
            if payload.scanner is not None:
                scanner = payload.scanner.source_binding
                original_scanner = _source_projection(origin, scanner.relative_path)
                if (
                    original_scanner != scanner
                    or scanner.relative_path not in raw_sources
                ):
                    raise SyntaxAssemblyContractError(
                        "scanner differs from complete original source",
                        code="syntax_contribution_source_missing",
                    )
                account.append((original_scanner, raw_sources[scanner.relative_path]))
            reconstructed = reconstruct_syntax_contribution(
                authored_source=source,
                owner_contract=owner,
                source_bodies=tuple(
                    sorted(
                        account,
                        key=lambda row: (
                            row[0].occurrence_ref.encode(),
                            row[0].relative_path.encode(),
                        ),
                    )
                ),
            )
            if rebuilding:
                if reconstructed.dependencies and not (
                    local_dependencies or grouped_dependencies
                ):
                    raise ContractViolation(
                        "original selected syntax dependency admission required"
                    )
                if len(observed) >= MAX_GRAMMAR_CONTRIBUTIONS:
                    raise ContractViolation("Code contribution inventory exceeds bound")
                from .grammar_contribution_output import (
                    grammar_contribution_output_body,
                )

                body = grammar_contribution_output_body(reconstructed)
                total += len(body.canonical_body)
                if total > MAX_GRAMMAR_BODY_BYTES:
                    raise ContractViolation(
                        "joined grammar aggregate byte budget exceeded"
                    )
                observed[source_key] = body
                observed_snapshots[source_key] = (
                    canonical_json_bytes(body.coordinate.to_wire()),
                    body.canonical_body,
                )
            if (
                encode_syntax_assembly_value(reconstructed)
                != observed[source_key].canonical_body
            ):
                raise ContractViolation(
                    "observed contribution differs from original Language reconstruction"
                )
            if reconstructed.contribution_ref in contributions:
                raise SyntaxAssemblyContractError(
                    "contribution label selects distinct original sources",
                    code="syntax_contribution_occurrence_ambiguous",
                )
            contributions[reconstructed.contribution_ref] = (
                occurrence_ref,
                reconstructed,
            )
            contribution_bindings.append(
                CodeGrammarContributionBindingV1(
                    occurrence_ref, path, observed[source_key].coordinate
                )
            )

    if selected_sources != set(observed):
        raise ContractViolation(
            "observed contributions are not the complete selected source bijection"
        )
    edges = {
        (row.owner_occurrence_ref, row.target_occurrence_ref)
        for row in group.dependency_edges
    }
    _validate_selected_contribution_dependencies(
        contributions, edges, local_only=rebuilding and local_dependencies
    )
    # Cycle refusal is source-namespace validation, not Language dependency-first
    # grammar traversal. No assembly request or fake generator is manufactured.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(label: str) -> None:
        if label in visiting:
            raise SyntaxAssemblyContractError("syntax dependency cycle")
        if label in visited:
            return
        visiting.add(label)
        for dependency in contributions[label][1].dependencies:
            visit(dependency.contribution_ref)
        visiting.remove(label)
        visited.add(label)

    for label in contributions:
        visit(label)

    bindings = tuple(
        sorted(
            contribution_bindings,
            key=lambda row: (row.occurrence_ref.encode(), row.relative_path.encode()),
        )
    )
    result = grammar_syntax_binding_body(
        CodeGrammarSyntaxBindingV2(
            selection.profile_key,
            profile.profile_ref,
            profile.version,
            profile.digest,
            selection.profile_source,
            tuple(provider_bindings),
            tuple(
                sorted(
                    (row.contribution_coordinate for row in bindings),
                    key=lambda row: canonical_json_bytes(row.to_wire()),
                )
            ),
            bindings,
            tuple(anchors[key] for key in sorted(anchors)),
            previous.coordinate,
        )
    )
    _ = _produce_profile_selection(
        input.ordinary,
        selection=selection,
        profile=profile,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
        stage="syntax_binding",
    )
    input.__post_init__()
    if (
        input.ordinary.input_digest.value != ordinary_digest
        or input.predecessors[0] is not previous
        or (
            canonical_json_bytes(previous.coordinate.to_wire()),
            previous.canonical_body,
            input.predecessor_closure_digest.value,
        )
        != predecessor_snapshot
    ):
        raise ContractViolation(
            "joined source/predecessor data changed during reconstruction"
        )
    for key, body in observed.items():
        body.__post_init__()
        if (
            canonical_json_bytes(body.coordinate.to_wire()),
            body.canonical_body,
        ) != observed_snapshots[key]:
            raise ContractViolation(
                "observed contribution changed during reconstruction"
            )
    return result


def _validate_selected_contribution_dependencies(
    contributions: dict[str, tuple[str, SyntaxContributionV1]],
    edges: set[tuple[str, str]],
    *,
    local_only: bool,
) -> None:
    """Data closure of the original selected inventory, never a target grant."""
    from aware_language_parsed_document_contract import SyntaxAssemblyContractError

    for occurrence, contribution in contributions.values():
        for dependency in contribution.dependencies:
            target = contributions.get(dependency.contribution_ref)
            if target is None:
                raise SyntaxAssemblyContractError(
                    "selected dependency contribution missing",
                    code="syntax_contribution_source_missing",
                )
            target_occurrence, value = target
            if local_only and occurrence != target_occurrence:
                raise ContractViolation(
                    "original cross-occurrence syntax target admission required"
                )
            if (dependency.version, dependency.digest) != (value.version, value.digest):
                raise SyntaxAssemblyContractError(
                    "complete dependency version/digest differs"
                )
            if (
                occurrence != target_occurrence
                and (occurrence, target_occurrence) not in edges
            ):
                raise ContractViolation(
                    "cross-occurrence syntax dependency lacks grouped provenance"
                )


def validate_grammar_source_binding_result(
    result: SemanticBody,
    *,
    input: SemanticInputJoinedProductionInput,
    selection: CodeGrammarSourceRoleSelectionV1,
    catalog: CodeSemanticContractCatalogResolver,
    provider_occurrences: tuple[str, ...],
    observed_contributions: tuple[tuple[str, str, SemanticBody], ...],
) -> None:
    """Full data correspondence; original host owns nominal result validation."""
    if type(result) is not SemanticBody:
        raise TypeError("exact Code syntax body required")
    result.__post_init__()
    decoded = CodeGrammarSyntaxBindingCodec().decode(result.canonical_body)
    if result != grammar_syntax_binding_body(decoded):
        raise ContractViolation("complete Code syntax result coordinate differs")
    expected = produce_grammar_source_binding(
        input,
        selection=selection,
        catalog=catalog,
        provider_occurrences=provider_occurrences,
        observed_contributions=observed_contributions,
    )
    if result != expected:
        raise ContractViolation(
            "Code syntax result differs from original supplied sources/results"
        )


__all__ = [
    "produce_grammar_profile_selection",
    "validate_grammar_profile_selection_result",
    "produce_grammar_source_binding",
    "reconstruct_grammar_source_binding",
    "reconstruct_grammar_local_dependency_binding",
    "reconstruct_grammar_group_dependency_binding",
    "validate_grammar_source_binding_result",
]
