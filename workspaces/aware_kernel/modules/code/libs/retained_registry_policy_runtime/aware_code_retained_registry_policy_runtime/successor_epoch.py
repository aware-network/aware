"""Continue one original command host after its paired successor publication.

The transfer and catalog remain owned by their original Code and Workspace
runtimes. This entrance only replaces Code's current, epoch-bound view; it does
not bootstrap a host, publish a catalog, or manufacture a planning result.
"""

from dataclasses import replace

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
)

from . import catalog_completion_transfer as transfers
from . import declaration_host
from . import direct_epoch_tracking as epochs
from . import direct_host


def adopt_committed_successor_epoch(host, transfer_runtime, transfer, *, expected):
    """Advance the exact original host under its Workspace parent exclusion.

    A sealed transfer is historical evidence. Only the original Workspace
    owner can attest that its target is still the current committed pair.
    """
    if type(host) is not direct_host.DirectValidationHost:
        raise TypeError("exact original Code host required")
    runtime = transfers._runtime(transfer_runtime)
    if runtime.host is not host:
        raise ContractViolation("completion transfer belongs to another host")
    _, record = transfers._transfer(transfer_runtime, transfer)
    old = epochs._BINDINGS.get(host)
    state = direct_host._HOSTS.get(host)
    if (
        state is None
        or old is None
        or state is not old.state
        or runtime.binding is not old
        or record.binding is not old
        or record.status != "sealed"
        or state.pending_successor is not transfer
        or state.source_rail != "declaration_v3"
    ):
        raise ContractViolation("current v3 predecessor transfer required")

    # Source and catalog reads must finish before taking the original guard.
    state.check(read_catalog=False, check_catalog=False)
    declaration_host._validate_declaration_source(
        host, successor_transition=True
    )
    transfer_runtime.validate_committed_catalog_completion_transfer(
        transfer, expected=expected
    )
    publication = record.publication
    if runtime.current.call(
        record.preparation, expected=publication.successor
    ) is not None:
        raise ContractViolation("successor currentness validator returned a value")
    admission = runtime.catalog_reader.call(
        record.preparation, expected=publication.successor
    )
    resolver = CodeSemanticContractCatalogResolver(admission)
    catalog = resolver.catalog
    if catalog.catalog_root_digest != publication.successor.code_catalog_digest:
        raise ContractViolation("committed successor Code catalog differs")
    retained = state.stage_retention
    if retained is None:
        raise ContractViolation("original selected stage pair required")
    successor_stages = replace(
        retained,
        resolver=resolver,
        catalog_digest=catalog.catalog_root_digest,
        current_catalog=admission,
    )
    successor_stages.validate()
    retained_products = state.product_retention
    successor_products = (
        retained_products.successor(resolver, admission)
        if retained_products is not None else None
    )
    declaration_host._validate_declaration_source(
        host, successor_transition=True
    )
    old.tracker.epoch(record.preparation, publication.successor)
    successor = epochs._Binding(
        state,
        old.participant,
        record.preparation,
        publication.successor,
        old.tracker,
        old.acquire,
        old.release,
        old.parent_binding,
        admission,
    )

    with epochs._guard(old) as guard:
        epochs._original(old, host, guard)
        if runtime.successor_guard.call(
            guard, record.preparation, transfer, expected=publication
        ) is not None:
            raise ContractViolation("successor guard validator returned a value")
        with old.tracker.lock:
            if old.tracker.uses:
                raise ContractViolation("predecessor still has running uses")
        with direct_host._LOCK:
            if (
                direct_host._HOSTS.get(host) is not state
                or state.closed
                or epochs._BINDINGS.get(host) is not old
                or runtime.binding is not old
                or record.status != "sealed"
            ):
                raise ContractViolation("successor epoch changed during adoption")
            from . import product_execution

            product_execution._retire_selected_input_host(host, old, exclusion_pending=True)
            state.catalog_resolver = resolver
            state.catalog_digest = catalog.catalog_root_digest
            state.current_catalog = admission
            state.stage_retention = successor_stages
            state.product_retention = successor_products
            state.pending_successor = None
            epochs._BINDINGS[host] = successor
            runtime.binding = successor

    product_execution._dispose_retired_selected_inputs(host)

    # Old policy handles retain their predecessor binding. The new selected
    # policy and planning context are issued through the unchanged public host
    # entrances, which now see only this current epoch view.
    state.check(read_catalog=False)
    return None
