"""Original command/catalog/source attachment; test bootstrap is not installed authority."""

from contextlib import ExitStack, asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aware_code_module_manifest_contract_runtime import grammar_factory
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import (
    grammar_role_attachment as attachment,
)
from aware_code_retained_registry_policy_runtime import grammar_role_cleanup as cleanup
from aware_code_semantic_contract_runtime import selected_provider
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.grammar_source_group import (
    GRAMMAR_SOURCE_GROUP_REF,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_REF,
)
from aware_code_semantic_contract_runtime.source_selection import (
    SOURCE_SELECTION_REF,
    SemanticSelectedSource,
    SemanticSourceSelection,
    source_selection_body,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as workspace
from aware_workspace_runtime.declaration_scope_admission import (
    WorkspaceSelectedSourceInputV1,
)
from test_dependency_scope_admission import fixture as repository
from test_materialization_declaration_selection import _author_v3_repository


@pytest.fixture(scope="module")
def grammar_admissions():
    # Original issuer and real factories, but a test bootstrap—not an installed release.
    return tuple(
        selected_provider._admit_selected_provider_factory(
            factory_ref=fn.__module__ + ":" + fn.__name__,
            provider_key=fn().binding.provider_key,
            selection_factory=fn,
        )
        for fn in (
            grammar_factory.construct_grammar_profile_selection_product,
            grammar_factory.construct_grammar_syntax_binding_product,
        )
    )


def authored_repository(root):
    # Use the existing real V3 fixture author, under its original paths.
    (root / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="demo"\nworkspaces_dir="workspaces"\n'
        '[[workspaces]]\nhandle="Kernel"\npath="kernel"\n'
        '[[workspaces]]\nhandle="Network"\npath="network"\n'
    )
    for name in ("kernel", "network"):
        module = root / f"workspaces/{name}/modules/main"
        package = module / "package"
        package.mkdir(parents=True)
        (package / "aware.example.toml").write_bytes(b"original manifest")
        (package / "body.bin").write_bytes(b"original source")
        if name == "network":
            (package / "child").mkdir()
            (package / "child/aware.example.toml").write_bytes(b"original child")
        (module / "aware.module.toml").write_text("aware=3\n")
        (root / f"workspaces/{name}/aware.workspace.toml").write_text(
            f'aware=2\n[workspace]\nhandle="{name.title()}"\n'
            '[[workspace.modules]]\nid="main"\npath="modules/main"\n'
        )
    _author_v3_repository(root)


@asynccontextmanager
async def original_case(tmp_path, admissions):
    async with repository(tmp_path, authored_repository) as (
        root,
        _,
        _,
        borrowed,
        _,
        _,
    ):
        digest = ContentDigest.of_bytes(
            b"grammar command source proof, not installed bootstrap"
        )
        implementation = SemanticImplementationCoordinate("test.grammar.host", digest)
        configuration = SemanticConfigurationCoordinate("test.grammar.host", digest)
        with workspace.compose_direct_workspace_selected_host(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            composition_implementation=implementation,
            composition_configuration=configuration,
            policy_implementation=implementation,
            policy_configuration=configuration,
            product_factory_admissions=admissions,
        ) as paired:
            command = paired.staged.command
            source = command.sources
            issuer = source.declaration_scope_runtime
            observation = source.observation_runtime.observe_selected_package(
                declaration=source.declaration_observation,
                workspace_manifest_path="workspaces/network/aware.workspace.toml",
                module_id="main",
                package_id="example",
            )
            selected = issuer.bind_selected_package_source(
                declaration=source.declaration_scope, selected=observation
            )
            with ExitStack() as stack:
                evidence = issuer.inspect_selected_package_evidence(selected)
                raw_ref = SemanticContractRef(
                    "test.original.raw", "1", ContentDigest.of_bytes(b"raw")
                )
                raw = tuple(
                    inputs.SemanticInputSourceCoordinate(
                        row.relative_path,
                        SemanticValueCoordinate(
                            "raw_source",
                            raw_ref,
                            row.body_ref,
                            ContentDigest(row.content_digest),
                            row.size_bytes,
                        ),
                    )
                    for row in evidence.bodies
                )
                expected = stack.enter_context(
                    issuer.original_pre_request_input(
                        selected,
                        use_ref="original-selection",
                        stage="test_selection",
                        source_coordinates=raw,
                    )
                )
                context = issuer.inspect_inputs(selected)[0]
                host = inputs.SemanticInputProducerHost()
                stack.callback(host.close)
                contracts = (
                    inputs.SemanticInputSourceContract("selected_raw", raw_ref),
                )

                async def choose(value):
                    return source_selection_body(
                        SemanticSourceSelection(
                            context.package,
                            context.source_identity_digest,
                            value.input_digest,
                            (),
                            tuple(
                                SemanticSelectedSource(
                                    "selected_raw",
                                    raw_ref,
                                    row.source.relative_path,
                                    row.source.coordinate.digest,
                                )
                                for row in value.sources
                            ),
                        ),
                        role="selection",
                    )

                registration = inputs.register_semantic_input_producer(
                    host,
                    declaration=inputs.SemanticInputProducerDeclaration(
                        "test.original.selection",
                        "test.original.selection.v1",
                        implementation,
                        configuration,
                        (inputs.SemanticInputSourceContract("raw_source", raw_ref),),
                        "selection",
                        SOURCE_SELECTION_REF,
                    ),
                    producer=choose,
                    validator=issuer,
                    validator_entrance=issuer.validate_semantic_input_source,
                    reader=issuer,
                    reader_entrance=issuer.read_semantic_input_sources,
                    retain_result=True,
                )
                body = await inputs.execute_registered_semantic_input(
                    host, registration, source_admission=selected, expected=expected
                )
                carrier = WorkspaceSelectedSourceInputV1(
                    selected, host, registration, expected, body, contracts
                )
                contexts = (
                    inputs.SemanticInputContextContract(
                        "declaration_scope", RETAINED_DECLARATION_SCOPE_V3_REF
                    ),
                    inputs.SemanticInputContextContract(
                        "grammar_source_group", GRAMMAR_SOURCE_GROUP_REF
                    ),
                )
                uses = tuple(
                    stack.enter_context(
                        issuer.original_grouped_selected_source_input(
                            root=carrier,
                            participants=(),
                            dependency_edges=(),
                            use_ref="grammar-" + stage,
                            stage=stage,
                            source_contracts=contracts,
                            context_contracts=contexts,
                        )
                    )
                    for stage in ("profile_selection", "syntax_binding")
                )
                yield SimpleNamespace(
                    root=root,
                    paired=paired,
                    command=command,
                    issuer=issuer,
                    selected=selected,
                    carrier=carrier,
                    expected=uses,
                )


def capture(case, **options):
    return attachment._capture_grammar_source_role_attachment(
        code_host=case.paired.code_host,
        profile_expected=options.get("profile_expected", case.expected[0]),
        syntax_expected=options.get("syntax_expected", case.expected[1]),
    )


async def test_original_command_catalog_and_source_attachment(
    tmp_path, grammar_admissions
):
    async with original_case(tmp_path, grammar_admissions) as case:
        value = capture(case)
        assert value.methods[0].receiver is case.issuer
        # Product-only composition is not a retained planning-operation grant.
        assert case.issuer._planning_validator is None
        assert case.issuer._authority_validator is None
        assert value.expectations[0].source_identity is case.selected
        assert value.binding.tracker.parent is case.command.invocation_parent
        assert (
            value.state.catalog_resolver._admission
            is case.paired.catalog_pair.code_admission
        )
        attachment._validate_grammar_source_role_attachment(
            case.paired.code_host, value
        )
        ticket = value.cleanup_custody.ticket
        receipt = cleanup.dispose_grammar_role_cleanup(ticket)
        assert receipt.completion == "verified"
        assert not direct._HOSTS[case.paired.code_host].closed
        assert cleanup.dispose_grammar_role_cleanup(ticket) is receipt


async def test_foreign_source_identity_refuses_before_attachment(
    tmp_path, grammar_admissions
):
    async with original_case(tmp_path, grammar_admissions) as case:
        expected = replace(case.expected[1], source_identity=object())
        with pytest.raises(ContractViolation):
            capture(case, syntax_expected=expected)
        assert direct._HOSTS[case.paired.code_host].grammar_attachment is None


async def test_original_source_mutation_and_restoration_are_terminal(
    tmp_path, grammar_admissions
):
    with pytest.raises(SourceObservationUnavailable):
        async with original_case(tmp_path, grammar_admissions) as case:
            value = capture(case)
            path = case.root / "workspaces/network/modules/main/package/body.bin"
            original = path.read_bytes()
            path.write_bytes(b"changed original source")
            with pytest.raises((SourceObservationUnavailable, ContractViolation)):
                attachment._validate_grammar_source_role_attachment(
                    case.paired.code_host, value
                )
            path.write_bytes(original)
            with pytest.raises((SourceObservationUnavailable, ContractViolation)):
                attachment._validate_grammar_source_role_attachment(
                    case.paired.code_host, value
                )
            assert value.retired
            cleanup.dispose_grammar_role_cleanup(value.cleanup_custody.ticket)


async def test_copied_expectation_cannot_gain_original_group_identity(
    tmp_path, grammar_admissions
):
    async with original_case(tmp_path, grammar_admissions) as case:
        with pytest.raises(SourceObservationUnavailable):
            capture(case, profile_expected=replace(case.expected[0]))
        value = direct._HOSTS[case.paired.code_host].grammar_attachment
        assert value.retired
        case.issuer.validate_semantic_input_source(
            case.selected, expected=case.expected[0]
        )
        receipt = cleanup.dispose_grammar_role_cleanup(value.cleanup_custody.ticket)
        assert receipt.completion == "unverified"


async def test_foreign_command_parent_cannot_attach(tmp_path, grammar_admissions):
    async with original_case(tmp_path, grammar_admissions) as case:
        foreign = object()
        with pytest.raises(ContractViolation, match="another command parent"):
            capture(
                case,
                profile_expected=replace(case.expected[0], operation_identity=foreign),
                syntax_expected=replace(case.expected[1], operation_identity=foreign),
            )
        assert direct._HOSTS[case.paired.code_host].grammar_attachment is None


async def test_original_source_entrance_substitution_never_dispatches(
    tmp_path, grammar_admissions, monkeypatch
):
    async with original_case(tmp_path, grammar_admissions) as case:
        value = capture(case)
        calls = []

        def foreign(*args, **kwargs):
            calls.append(True)
            raise AssertionError("foreign owner dispatched")

        with monkeypatch.context() as patch:
            patch.setattr(type(case.issuer), "validate_semantic_input_source", foreign)
            with pytest.raises(ContractViolation, match="entrance substituted"):
                attachment._validate_grammar_source_role_attachment(
                    case.paired.code_host, value
                )
        assert calls == []
        assert value.retired
        cleanup.dispose_grammar_role_cleanup(value.cleanup_custody.ticket)
