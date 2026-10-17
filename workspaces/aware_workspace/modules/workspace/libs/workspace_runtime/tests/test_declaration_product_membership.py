"""Initial participation from original declaration/source and owner contribution.

Source-factory mechanics use Attention; no package-authority completion or
execution is fabricated. The public CLI separately uses installed intake.
"""

import re
import sys
from contextlib import asynccontextmanager
from dataclasses import fields
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import ContractViolation
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import declaration_product_membership as membership
from aware_workspace_runtime import direct_command_composition as composition
from test_current_head_two_stage_host import (
    real_environment_factory as _environment_factory,
)
from test_direct_cli_selected_host import _proposal, sources
from test_direct_cli_selected_host import factory as _factory
from test_observed_semantic_issuers import PROVIDER, occurrence
from test_single_product_command_composition import _attention_repository, _coordinates

factory = _factory


async def test_membership_metadata_window_reduces_captures_and_closes_before_projection(
    tmp_path, factory,
):
    from aware_workspace_runtime import source_observation as source

    async with prepared(tmp_path, factory) as (_, command, selected, _, original, entry):
        issuer = command.sources.declaration_scope_runtime
        state = membership._state(original)
        capture = source.WorkspaceSourceObservationRuntime.revalidate_declarations.__code__
        reads = {
            getattr(type(issuer), name).__code__: name
            for name in ("read_selected_package_source", "read_declaration_scope",
                         "read_selected_participant_view", "inspect_inputs")
        }
        captures = []
        windows = []

        def profile(frame, event, arg):
            if event == "call" and frame.f_code is capture:
                captures.append(True)
            if event == "call" and frame.f_code in reads:
                windows.append((reads[frame.f_code], issuer._semantic_source_window is not None))
            if event == "call" and frame.f_code is membership.project_declared_product.__code__:
                assert issuer._semantic_source_window is None

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            issuer.read_selected_package_source(selected)
            issuer.read_declaration_scope(state.declaration)
            issuer.read_selected_participant_view(state.declaration, selected)
            issuer.inspect_inputs(selected)
            separate = len(captures)
            captures.clear()
            windows.clear()
            original.validate_catalog_entry(entry)
            shared = len(captures)
        finally:
            sys.setprofile(previous)
        assert 0 < shared < separate
        assert {name for name, active in windows if active} == set(reads.values())
        assert issuer._semantic_source_window is None


@asynccontextmanager
async def _membership_retirement_proof(tmp_path, factory):
    completed = False
    try:
        async with prepared(tmp_path, factory) as value:
            yield value
            completed = True
    except SourceObservationUnavailable:
        # An intentionally retired original declaration must also refuse the
        # command fixture's final currentness check. Do not suppress body errors.
        if not completed:
            raise


@pytest.mark.parametrize("method", ["_read_product_projection_inputs", "read_selected_participant_view", "inspect_inputs"])
@pytest.mark.parametrize("location", ["instance", "class"])
@pytest.mark.parametrize("mode", ["return", "raise", "restore"])
async def test_membership_metadata_rejects_changed_original_readers_without_dispatch(
    tmp_path, factory, monkeypatch, method, location, mode,
):
    async with prepared(tmp_path, factory) as (_, command, _, _, original, entry):
        issuer = command.sources.declaration_scope_runtime
        state = membership._state(original)
        holder = issuer if location == "instance" else type(issuer)
        descriptor = getattr(type(issuer), method)
        calls = []

        def restore():
            if location == "instance":
                delattr(holder, method)
            else:
                setattr(holder, method, descriptor)

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == "restore":
                restore()
            if mode == "raise":
                raise AssertionError("substituted membership reader executed")

        monkeypatch.setattr(holder, method, hostile)
        try:
            with pytest.raises((RuntimeError, SourceObservationUnavailable)):
                original.validate_catalog_entry(entry)
        finally:
            restore()
        assert not calls and state.terminal
        assert issuer._semantic_source_window is None
        with pytest.raises(RuntimeError, match="unavailable"):
            original.validate_catalog_entry(entry)


@pytest.mark.parametrize("change", ["source", "detached", "original", "record", "interrupt"])
async def test_membership_metadata_window_preserves_terminal_checks_and_cleanup(
    tmp_path, factory, change,
):
    from aware_workspace_runtime import declaration_scope_admission as admission

    async with _membership_retirement_proof(tmp_path, factory) as (_, command, _, _, original, entry):
        issuer = command.sources.declaration_scope_runtime
        state = membership._state(original)
        target = type(issuer).inspect_inputs.__code__
        changed = []
        restore = []

        def profile(frame, event, arg):
            if (event != "return" or frame.f_code is not target or changed
                or issuer._semantic_source_window is None):
                return
            changed.append(True)
            window = issuer._semantic_source_window
            if change == "interrupt":
                raise KeyboardInterrupt("membership metadata interrupted")
            if change == "source":
                evidence = window.record.source_record[2]
                relative = next(item.relative_path for item in evidence.bodies
                                if item.relative_path.endswith(".aware"))
                path = Path(issuer._source._session.binding.root_path) / evidence.package_root / relative
                body = path.read_bytes()
                restore.append(lambda: path.write_bytes(body))
                path.write_bytes(body + b"\nchanged inside membership metadata window\n")
            elif change == "record":
                record = window.record.declaration_record
                old = record.digest
                restore.append(lambda: object.__setattr__(record, "digest", old))
                object.__setattr__(record, "digest", admission.ContentDigest.of_bytes(b"coherent replacement"))
            else:
                projection = (window.closure if change == "detached"
                              else issuer._checked_declaration_origin(window.record.declaration_record).projection)
                old = projection.consumer_scope_key
                restore.append(lambda: object.__setattr__(projection, "consumer_scope_key", old))
                object.__setattr__(projection, "consumer_scope_key", "forged")

        previous = sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises((SourceObservationUnavailable, KeyboardInterrupt, BaseExceptionGroup)):
                original.validate_catalog_entry(entry)
        finally:
            sys.setprofile(previous)
            for action in restore:
                action()
        assert changed and state.terminal
        assert issuer._semantic_source_window is None
        with pytest.raises(RuntimeError, match="unavailable"):
            original.validate_catalog_entry(entry)


@pytest.fixture(scope="module")
def meta_factory():
    from aware_code_semantic_contract_runtime import selected_provider as selected
    from aware_meta_contract_runtime_provider.profile import META_OBSERVABLE_INSPECT_KEY
    from aware_meta_contract_runtime_provider.selected_factory import (
        construct_meta_observable_identity_read_factory_product_v2,
    )

    # These are source-grade original factory mechanics, not installation.
    key = META_OBSERVABLE_INSPECT_KEY
    existing = selected._FACTORY_PROVIDER_KEYS.get(key)
    if existing is not None:
        yield existing
        return
    original = selected._admit_selected_provider_factory(
        factory_ref="proof:workspace.meta.inspect.original.v1", provider_key=key,
        selection_factory=construct_meta_observable_identity_read_factory_product_v2,
    )
    state = selected._factory_state(original)
    try:
        yield original
    finally:
        if selected._FACTORY_PROVIDER_KEYS.get(key) is original:
            del selected._FACTORY_PROVIDER_KEYS[key]
        if selected._FACTORY_REFS.get(state.factory_ref) is original:
            del selected._FACTORY_REFS[state.factory_ref]
        if selected._FACTORIES.get(id(original), (None,))[0] is original:
            del selected._FACTORIES[id(original)]


@pytest.fixture(scope="module")
def environment_stage_factory():
    return _environment_factory.__wrapped__()


def _meta_inspect_repository(root):
    from aware_meta_contract_runtime_provider.profile import (
        META_OBSERVABLE_INSPECT_KEY,
        meta_observable_inspect_profile,
    )

    # Names, roots and manifest matcher below are disposable authored nominees.
    # Meta supplies the actual provider/profile/catalog, not these declarations.
    key, profile = META_OBSERVABLE_INSPECT_KEY, meta_observable_inspect_profile()
    consumer = root / "consumer/modules/main"
    package = consumer / "ontology"
    package.mkdir()
    (package / "aware.ontology.toml").write_text(
        'aware_ontology=1\n[ontology]\npackage_name="sample_meta"\n'
        'fqn_prefix="sample_meta"\n[build]\nsources_dir="."\n'
        'include_paths=["**/*.aware"]\nexclude_paths=[]\n'
    )
    (package / "source.aware").write_text("authored source retained by Workspace")
    admission = occurrence("sample_meta").replace(
        'value={module_id="main",package_id="provider",',
        'value={scope={kind="local"},module_id="main",package_id="provider",',
    ).replace(
        'registration_key="example"', 'registration_key="meta_inspect"'
    ).replace('value="1.0"', 'value="1"').replace(
        'value=["sample_meta.a","sample_meta.b"]', 'value=["sample_meta.Blob"]'
    )
    body = PROVIDER.replace('provider_key="demo"', f'provider_key="{key}"')
    body = body.replace('role="demo.provider"', 'role="aware_meta.provider"')
    body = body.replace('module="demo.provider"', 'module="aware_meta_contract_runtime_provider.selected_factory"')
    body = body.replace('capabilities=["materialize"]', 'capabilities=["inspect"]')
    body = body.replace('key="example"', 'key="meta_inspect"')
    body = body.replace("example_toml", "aware_ontology_toml")
    body = body.replace("aware.example.toml", "aware.ontology.toml")
    body = body.replace('semantic_package_family="example"', 'semantic_package_family="ontology"')
    body = body.replace('semantic_package_kind="example"', 'semantic_package_kind="ontology"')
    body = body.replace('role="example",name="example"', 'role="aware_meta.provider",name="meta_observable_identity"')
    body = body.replace("contract:example", "contract:" + key)
    body = re.sub(
        r"profiles=\[.*?\n\]",
        'profiles=[{stage="graph_product",profile_ref="' + profile.profile_ref
        + '",profile_version="' + profile.version + '",profile_digest="'
        + profile.digest.to_wire() + '"}]', body, flags=re.DOTALL,
    )
    (consumer / "provider").mkdir()
    (consumer / "provider/pyproject.toml").write_bytes(b"declared owner distribution")
    (consumer / "aware.module.toml").write_text(
        'aware=3\n[[packages]]\nid="ontology"\nkind="ontology"\n'
        'manifest="ontology/aware.ontology.toml"\nvisibility="module"\n'
        + admission + body
    )


@pytest.mark.parametrize("with_stage", [False, True])
async def test_original_meta_inspect_joins_one_command_and_retires(
    tmp_path, meta_factory, environment_stage_factory, with_stage,
):
    from aware_code_semantic_contract_runtime.stage_contribution import (
        read_selected_provider_stage_contribution,
    )
    from aware_meta_contract_runtime_provider.profile import (
        META_OBSERVABLE_INSPECT_KEY,
        META_SOURCE_CLOSURE_REF,
    )
    from aware_workspace_materialize_transport import (
        WorkspaceMaterializeCommandProposalV3,
    )

    async with sources(tmp_path, _meta_inspect_repository) as (root, _, _, borrowed, _, _):
        proposal = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="workspace-materialize-attempt:original-meta-inspect-catalog",
            participant_checkout_root=str(root),
            workspace_manifest_name="consumer/aware.workspace.toml",
            package_address=("Consumer", "main", "ontology"), plan_only=True,
        )
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=proposal,
        ) as (command, _, selected):
            with composition.compose_direct_workspace_selected_host(
                factory_admission=environment_stage_factory if with_stage else None,
                product_factory_admissions=(meta_factory,), session=borrowed._session,
                store=borrowed._store, workspace_manifest_path="consumer/aware.workspace.toml",
                command_resources=command, selected_package_sources=(selected,),
                **_coordinates(),
            ) as host:
                assert host.staged.command is command
                assert bool(host.staged.stage_runtime_bindings) is with_stage
                assert (host.staged.contribution is not None) is with_stage
                product = host.staged.product_contributions[0]
                original = products.read_selected_provider_product_contribution(product)
                assert original.binding.provider_key == META_OBSERVABLE_INSPECT_KEY
                assert original.profile.operation_kinds == ("inspect",)
                catalog = products.read_selected_provider_product_catalog_contribution(product)
                assert catalog.entries[0].manifest_contracts == (META_SOURCE_CLOSURE_REF,)
                entry = host.catalog_pair.workspace.package("package:sample_meta@1")
                assert entry.package_family == "ontology"
                assert entry.package_role == "aware_meta.provider"
                assert entry.owned_semantic_root_refs == ("sample_meta.Blob",)
                assert entry.participation_policy.allowed_operation_kinds == ("inspect",)
                correspondence = host.catalog_pair.source_correspondences[0]
                correspondence.validate_catalog_entry(entry)
                with command.catalog_host._command_parent.guarded() as guard:
                    correspondence.check_catalog_entry_locked(entry, guard)
                if with_stage:
                    stage = host.staged.contribution
                    assert len(read_selected_provider_stage_contribution(stage)) == 2
            with pytest.raises(ContractViolation):
                products.read_selected_provider_product_contribution(product)
            with pytest.raises(ContractViolation):
                host.catalog_pair.workspace.package(entry.package.package_ref)
            if with_stage:
                with pytest.raises(ContractViolation):
                    read_selected_provider_stage_contribution(stage)
            composition._require_live_direct_workspace_command(command)
        with pytest.raises((RuntimeError, SourceObservationUnavailable)):
            correspondence.validate_catalog_entry(entry)


@asynccontextmanager
async def prepared(tmp_path, factory):
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(  # noqa: SIM117 - preserve original command outside staged cleanup
            session=borrowed._session, store=borrowed._store, proposal=_proposal(root)
        ) as (command, _, selected):
            with composition._compose_direct_workspace_staged_command_resources(
                product_factory_admissions=(factory,), session=borrowed._session,
                store=borrowed._store, workspace_manifest_path="consumer/aware.workspace.toml",
                source_rail="declaration_v3", command_resources=command,
            ) as staged:
                product = staged.product_contributions[0]
                products.produce_selected_provider_product_catalog_contribution(product)
                correspondence, entry = membership.capture_declaration_product_correspondence(
                    issuer=command.sources.declaration_scope_runtime,
                    declaration=command.sources.declaration_scope,
                    selected=selected, product=product,
                )
                yield root, command, selected, product, correspondence, entry


async def test_inspect_correspondence_does_not_promote_materialize_product(tmp_path, factory):
    async with prepared(tmp_path, factory) as (_, command, selected, product, original, entry):
        with pytest.raises(ContractViolation, match="inspect-only"):
            membership.capture_declaration_inspect_product_correspondence(
                issuer=command.sources.declaration_scope_runtime,
                declaration=command.sources.declaration_scope, selected=selected, product=product,
            )
        original.validate_catalog_entry(entry)
        assert entry.participation_policy.allowed_operation_kinds == ("materialize",)


@pytest.mark.parametrize("kind", ["inspect", "foreign", None])
async def test_operation_kind_substitution_cannot_upgrade_original_correspondence(tmp_path, factory, kind):
    async with prepared(tmp_path, factory) as (_, _, _, _, original, entry):
        state = membership._state(original)
        state.operation_kind = kind
        with pytest.raises((ContractViolation, RuntimeError)):
            original.validate_catalog_entry(entry)
        state.operation_kind = "materialize"
        with pytest.raises(RuntimeError):
            original.validate_catalog_entry(entry)


async def test_original_initial_membership_preserves_declared_package_and_owner(
    tmp_path, factory
):
    async with sources(tmp_path, _attention_repository) as (root, _, _, borrowed, _, _):
        with composition._compose_direct_workspace_command_source(
            session=borrowed._session, store=borrowed._store, proposal=_proposal(root)
        ) as (command, _, selected):
            with composition.compose_direct_workspace_selected_host(
                product_factory_admissions=(factory,), session=borrowed._session,
                store=borrowed._store, workspace_manifest_path="consumer/aware.workspace.toml",
                command_resources=command, selected_package_sources=(selected,),
                **_coordinates(),
            ) as host:
                pair = host.catalog_pair
                entry = pair.workspace.package("package:sample_attention@1")
                assert entry.package_family == "attention"
                assert entry.package_role == "aware_attention.provider"
                assert entry.owned_semantic_root_refs == ("sample_attention.a", "sample_attention.b")
                assert entry.authored_dependencies == ()
                assert entry.source_authority_ref.startswith("workspace-selected-source:")
                assert entry.participation_policy.allowed_terminal_output_roles == (
                    "attention_definition_manifest",
                )
                assert len(pair.source_correspondences) == 1
                correspondence = pair.source_correspondences[0]
                correspondence.validate_catalog_entry(entry)
                expected = command.catalog_host.read_initial_publication()
                assert expected.membership_catalog_digest == pair.workspace.catalog.catalog_root_digest
                with command.catalog_host._command_parent.guarded() as guard:
                    correspondence.check_catalog_entry_locked(entry, guard)
            with pytest.raises(ContractViolation):
                pair.workspace.package(entry.package.package_ref)
        with pytest.raises((RuntimeError, SourceObservationUnavailable)):
            correspondence.validate_catalog_entry(entry)


@pytest.mark.parametrize("phase", ["full", "locked"])
async def test_copied_changed_entry_is_terminal_but_equal_portable_entry_is_not_authority(
    tmp_path, factory, phase
):
    async with prepared(tmp_path, factory) as (_, command, _, _, correspondence, entry):
        values = {field.name: getattr(entry, field.name) for field in fields(entry)}
        values.pop("entry_digest")
        values.pop("source_identity_digest")
        changed = type(entry).create(**(values | {"source_authority_ref": "foreign:source"}))
        with pytest.raises(RuntimeError):
            if phase == "full":
                correspondence.validate_catalog_entry(changed)
            else:
                with command.catalog_host._command_parent.guarded() as guard:
                    correspondence.check_catalog_entry_locked(changed, guard)
        with pytest.raises(RuntimeError, match="unavailable"):
            correspondence.validate_catalog_entry(entry)


async def test_source_change_rejects_and_restoration_cannot_resume(tmp_path, factory):
    async with prepared(tmp_path, factory) as (root, _, _, _, correspondence, entry):
        source = root / "consumer/modules/main/attention/source.aware"
        original = source.read_bytes()
        source.write_bytes(original + b"\nchanged\n")
        with pytest.raises(SourceObservationUnavailable):
            correspondence.validate_catalog_entry(entry)
        source.write_bytes(original)
        with pytest.raises(RuntimeError, match="unavailable"):
            correspondence.validate_catalog_entry(entry)


@pytest.mark.parametrize("name", ["read_selected_package_source", "read_declaration_scope", "inspect_inputs"])
async def test_substituted_original_method_never_dispatches_and_restoration_is_terminal(
    tmp_path, factory, monkeypatch, name
):
    async with prepared(tmp_path, factory) as (_, command, _, _, correspondence, entry):
        issuer = command.sources.declaration_scope_runtime
        calls = []

        def hostile(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("must not execute")

        with monkeypatch.context() as changes:
            changes.setattr(issuer, name, hostile)
            with pytest.raises(RuntimeError, match="substituted"):
                correspondence.validate_catalog_entry(entry)
        # monkeypatch restores a bound-method instance alias. Restore the
        # original descriptor lookup before the command's final source check.
        vars(issuer).pop(name, None)
        assert calls == []
        with pytest.raises(RuntimeError, match="unavailable"):
            correspondence.validate_catalog_entry(entry)


async def test_product_retirement_rejects_before_initial_publication(tmp_path, factory):
    # Explicit early retirement also makes the original assembly's attempted
    # second cleanup refuse. Retain that refusal rather than suppressing it.
    with pytest.raises(ContractViolation, match="unavailable"):
        async with prepared(tmp_path, factory) as (_, _, _, product, correspondence, entry):
            products.close_selected_provider_product_contribution(product)
            with pytest.raises(ContractViolation):
                correspondence.validate_catalog_entry(entry)
            with pytest.raises(RuntimeError, match="unavailable"):
                correspondence.validate_catalog_entry(entry)


async def test_foreign_guard_is_terminal(tmp_path, factory):
    async with prepared(tmp_path, factory) as (_, _, _, _, correspondence, entry):
        with pytest.raises((RuntimeError, SourceObservationUnavailable)):
            correspondence.check_catalog_entry_locked(entry, object())
        with pytest.raises(RuntimeError, match="unavailable"):
            correspondence.validate_catalog_entry(entry)


async def test_unregistered_foreign_correspondence_does_not_revoke_original(tmp_path, factory):
    async with prepared(tmp_path, factory) as (_, _, _, _, correspondence, entry):
        foreign = object.__new__(membership.WorkspaceDeclarationProductCorrespondence)
        with pytest.raises(RuntimeError, match="unavailable"):
            foreign.validate_catalog_entry(entry)
        correspondence.validate_catalog_entry(entry)


async def test_registered_restamping_is_terminal_without_foreign_behavior(tmp_path, factory):
    calls = []

    class Foreign:
        __slots__ = ("__weakref__",)

        def __eq__(self, other):
            calls.append(other)
            raise AssertionError("foreign equality must not execute")

        def __hash__(self):
            calls.append("hash")
            raise AssertionError("foreign hash must not execute")

    async with prepared(tmp_path, factory) as (_, _, _, _, correspondence, entry):
        original = type(correspondence)
        correspondence.__class__ = Foreign
        with pytest.raises(TypeError):
            membership.validate_declaration_product_correspondence(correspondence, entry)
        correspondence.__class__ = original
        assert calls == []
        with pytest.raises(RuntimeError, match="unavailable"):
            correspondence.validate_catalog_entry(entry)


@pytest.mark.parametrize("phase", ["full", "locked"])
async def test_correspondence_method_substitution_cannot_dispatch(tmp_path, factory, monkeypatch, phase):
    async with prepared(tmp_path, factory) as (_, command, _, _, correspondence, entry):
        calls = []

        def hostile(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("substituted validation must not execute")

        name = "validate_catalog_entry" if phase == "full" else "check_catalog_entry_locked"
        with monkeypatch.context() as changes:
            changes.setattr(type(correspondence), name, hostile)
            with pytest.raises(RuntimeError, match="substituted"):
                if phase == "full":
                    membership.validate_declaration_product_correspondence(correspondence, entry)
                else:
                    with command.catalog_host._command_parent.guarded() as guard:
                        membership.check_declaration_product_correspondence_locked(correspondence, entry, guard)
        assert calls == []
        with pytest.raises(RuntimeError, match="unavailable"):
            correspondence.validate_catalog_entry(entry)
