"""Pure lower derivation. Portable records never grant original host authority."""
from __future__ import annotations

import builtins
import hashlib
import importlib as _native_importlib
import importlib.util as _native_import_util
import json
import sys
from types import CellType, FunctionType, ModuleType
from typing import Any

from . import codec, owner_values as values, wire

# An absent native artifact selects the portable installation profile. Other
# loader failures propagate; an admitted native refusal never selects fallback.
if __package__ is None:
    raise ImportError
try:
    _native_scan_module = _native_importlib.import_module(__package__ + "._preparation_scan")
except ModuleNotFoundError as _native_import_error:
    if _native_import_error.name != __package__ + "._preparation_scan":
        raise
    if _native_import_util.find_spec(__package__ + "._preparation_scan") is not None:
        raise
    _native_scan_module = None


class PreparationError(ValueError):
    """Closed pure-data refusal; never an issuer observation or Result."""

    def __init__(self, code: str = "malformed", reason: str = "preparation_invalid") -> None:
        self.code, self.reason = code, reason
        super().__init__(reason)


_CONTEXT_KEYS = ("branch_ref", "retained_revision_ref", "provider_ref", "provider_generation",
    "topology_digest", "schema_digest", "schema_slice_digest", "object_abi_digest",
    "application_authority_digest", "selection_profile_digest", "base_operational_digest")
_ACTIVATION_KEYS = ("branch_ref", "actor_ref", "projection_ref", "operation_ref", "idempotency_key",
    "object_abi_digest", "application_authority_body", "expected_revision_ref")
_preparation_check: Any = None


def _native_inputs(value: object) -> None:
    # Owning native visitor uses exact slot descriptors and identity dispatch,
    # including every supplied nested P1 operand, before behavior can run.
    values._attempt_native(value)


def _validate_context(context: Any) -> dict[str, Any]:
    check = _preparation_check
    check_code = check.__code__
    binding_failure = PreparationError()
    _native_inputs(context)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    context = values.attempt_require_exact_keys(context, _CONTEXT_KEYS, path="derivation_context")
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    for name in _CONTEXT_KEYS:
        if name.endswith("digest"):
            values.attempt_require_sha256(context[name], name)
        else:
            values._attempt_text(context[name], name)
        if check.__code__ is not check_code:
            raise binding_failure
        check()
    return context




def _validate_activation(activation: Any) -> dict[str, Any]:
    check = _preparation_check
    check_code = check.__code__
    binding_failure = PreparationError()
    _native_inputs(activation)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    activation = values.attempt_require_exact_keys(activation, _ACTIVATION_KEYS, path="activation_preimage")
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    for name in ("branch_ref", "actor_ref", "projection_ref", "operation_ref", "idempotency_key"):
        values._attempt_text(activation[name], name)
        if check.__code__ is not check_code:
            raise binding_failure
        check()
    values.attempt_require_sha256(activation["object_abi_digest"], "object_abi_digest")
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    if activation["expected_revision_ref"] is not None:
        values._attempt_text(activation["expected_revision_ref"], "expected_revision_ref")
        if check.__code__ is not check_code:
            raise binding_failure
        check()
    authority = values.attempt_require_exact_keys(activation["application_authority_body"],
        ("application_ref", "implementation_digest", "authority_digest"), path="application_authority_body")
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    values._attempt_validate_authority(authority, application=True)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    actual = values.digest_payload(values.OBJECT_APPLICATION_AUTHORITY_CONTRACT,
        {key: value for key, value in authority.items() if key != "authority_digest"})
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    if actual != authority["authority_digest"]:
        raise PreparationError("binding_mismatch", "application_authority_digest_mismatch")
    return activation




def _validate_selection_membership(*, activation_preimage: Any, derivation_context: Any,
                                   selection_profile: Any) -> None:
    check = _preparation_check
    check_code = check.__code__
    binding_failure = PreparationError()
    _native_inputs(selection_profile)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    activation = _validate_activation(activation_preimage)
    context = _validate_context(derivation_context)
    if type(selection_profile) is not values.OntologyObjectExecutableSelectionProfile:
        raise PreparationError("binding_mismatch", "selection_context_mismatch")
    profile: dict[str, Any] = selection_profile.to_wire()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    # Complete owning revalidation of detached records, without provenance marks.
    raw = selection_profile.canonical_bytes()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    values.OntologyObjectExecutableSelectionProfile.from_canonical_bytes(raw)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    facts = profile["selection_facts_body"]
    if (facts["provider_key"] != context["provider_ref"]
        or facts["provider_generation"] != context["provider_generation"]
        or profile["branch_ref"] != activation["branch_ref"]
        or context["branch_ref"] != activation["branch_ref"]
        or profile["object_abi_digest"] != activation["object_abi_digest"]
        or context["object_abi_digest"] != activation["object_abi_digest"]
        or profile["application_authority_digest"] != activation["application_authority_body"]["authority_digest"]
        or profile["application_authority_digest"] != context["application_authority_digest"]
        or profile["profile_digest"] != context["selection_profile_digest"]
        or any(profile[name] != context[name] for name in ("topology_digest", "schema_digest", "schema_slice_digest"))):
        raise PreparationError("binding_mismatch", "selection_context_mismatch")
    for name, rule_name, reason in (
        ("actor_ref", "actor_rule_body", "selection_actor_refused"),
        ("projection_ref", "projection_rule_body", "selection_projection_refused"),
        ("operation_ref", "operation_rule_body", "selection_operation_refused"),
        ("idempotency_key", "idempotency_rule_body", "selection_idempotency_refused")):
        field, rule = activation[name], facts[rule_name]
        if (type(field) is not str or not field or field.strip() != field
            or (rule["kind"] == "one_of" and field not in rule["values"])):
            raise PreparationError("binding_mismatch", reason)


    # Deliberately no expected/current revision equality: historical recovery
    # consumes this membership law without issuing a new selection.


def _derive_selection_data(*, activation_preimage: Any, derivation_context: Any,
                           selection_profile: Any) -> tuple[dict[str, Any], dict[str, Any], Any]:
    check = _preparation_check
    check_code = check.__code__
    binding_failure = PreparationError()
    _validate_selection_membership(activation_preimage=activation_preimage,
        derivation_context=derivation_context, selection_profile=selection_profile)
    activation, context = activation_preimage, derivation_context
    if activation["expected_revision_ref"] is not None and activation["expected_revision_ref"] != context["retained_revision_ref"]:
        raise PreparationError("source_stale", "selection_operational_base_stale")
    profile: dict[str, Any] = selection_profile.to_wire()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    facts = profile["selection_facts_body"]
    authority = {name: facts[source] for name, source in (
        ("admission_provider_key", "provider_key"), ("admission_provider_generation", "provider_generation"),
        ("authority_ref", "authority_ref"), ("executable_root_digest", "executable_root_digest"),
        ("vm_implementation_digest", "vm_implementation_digest"), ("capability_catalog_digest", "capability_catalog_digest"))}
    authority["base_operational_digest"] = context["base_operational_digest"]
    authority["authority_digest"] = values.digest_payload(values.OBJECT_EXECUTABLE_AUTHORITY_CONTRACT, authority)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    activation_digest = values.attempt_digest_wire("aware.ontology.object-activation-request.v1", activation)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    execution = dict(activation_request_digest=activation_digest, provider_key=context["provider_ref"],
        provider_generation=context["provider_generation"], topology_digest=context["topology_digest"],
        schema_digest=context["schema_digest"], schema_slice_digest=context["schema_slice_digest"],
        base_operational_digest=context["base_operational_digest"])
    execution_digest = values.attempt_digest_wire("aware.ontology.object-execution-admission-request.v1", execution)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    admission = values._attempt_build_portable_value(values.OntologyObjectExecutableSelectionAdmission,
        selection_profile_body=selection_profile, selection_profile_digest=profile["profile_digest"],
        activation_request_digest=activation_digest, execution_admission_request_digest=execution_digest,
        retained_revision_ref=context["retained_revision_ref"], current_base_operational_digest=context["base_operational_digest"],
        executable_authority_body=authority, executable_authority_digest=authority["authority_digest"],
        selection_disposition="selected")
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    return authority, execution, admission




def _derive_attempt_data(*, activation_preimage: Any, derivation_context: Any,
                        selection_admission: Any, precontact_profile: Any) -> tuple[Any, Any]:
    check = _preparation_check
    check_code = check.__code__
    binding_failure = PreparationError()
    _native_inputs(selection_admission)
    _native_inputs(precontact_profile)
    activation = _validate_activation(activation_preimage)
    context = _validate_context(derivation_context)
    if type(selection_admission) is not values.OntologyObjectExecutableSelectionAdmission or type(precontact_profile) is not values.OntologyObjectPrecontactRecoveryProfile:
        raise PreparationError("binding_mismatch", "selection_context_mismatch")
    selection: dict[str, Any] = selection_admission.to_wire()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    profile: dict[str, Any] = precontact_profile.to_wire()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    _validate_selection_membership(activation_preimage=activation, derivation_context=context,
        selection_profile=selection_admission.selection_profile_body)
    # Owning record codecs validate digests AND semantics before consumption.
    raw = selection_admission.canonical_bytes()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    values.OntologyObjectExecutableSelectionAdmission.from_canonical_bytes(raw)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    raw = precontact_profile.canonical_bytes()
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    values.OntologyObjectPrecontactRecoveryProfile.from_canonical_bytes(raw)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    executable = selection["executable_authority_body"]
    activation_digest = values.attempt_digest_wire("aware.ontology.object-activation-request.v1", activation)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    execution = dict(activation_request_digest=activation_digest, provider_key=context["provider_ref"],
        provider_generation=context["provider_generation"], topology_digest=context["topology_digest"],
        schema_digest=context["schema_digest"], schema_slice_digest=context["schema_slice_digest"],
        base_operational_digest=context["base_operational_digest"])
    execution_digest = values.attempt_digest_wire("aware.ontology.object-execution-admission-request.v1", execution)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    if (selection["activation_request_digest"] != activation_digest
        or selection["execution_admission_request_digest"] != execution_digest
        or selection["retained_revision_ref"] != context["retained_revision_ref"]
        or selection["current_base_operational_digest"] != context["base_operational_digest"]
        or profile["provider_key"] != context["provider_ref"]
        or profile["provider_generation"] != context["provider_generation"]
        or profile["executable_authority_digest"] != executable["authority_digest"]):
        raise PreparationError("binding_mismatch", "precontact_profile_mismatch")
    coordinate = dict(schema="aware.ontology.object-operation-attempt-coordinate.v1",
        activation_request_digest=activation_digest, execution_admission_request_digest=execution_digest,
        provider_profile_digest=profile["profile_digest"])
    attempt_ref = "ontology-object-attempt:" + values.attempt_digest_wire(
        "aware.ontology.object-operation-attempt-coordinate.v1.digest", coordinate)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    recovery_coordinate = dict(coordinate, schema="aware.ontology.object-operation-recovery-coordinate.v1", attempt_ref=attempt_ref)
    recovery_ref = "ontology-object-recovery:" + values.attempt_digest_wire(
        "aware.ontology.object-operation-recovery-coordinate.v1.digest", recovery_coordinate)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    attempt = values._attempt_build_portable_value(values.OntologyObjectOperationAttempt,
        provider_profile_digest=profile["profile_digest"], provider_key=context["provider_ref"],
        provider_generation=context["provider_generation"], branch_ref=activation["branch_ref"],
        actor_ref=activation["actor_ref"], projection_ref=activation["projection_ref"], operation_ref=activation["operation_ref"],
        idempotency_key=activation["idempotency_key"], object_abi_digest=activation["object_abi_digest"],
        application_authority_body=activation["application_authority_body"],
        application_authority_digest=activation["application_authority_body"]["authority_digest"],
        executable_authority_body=executable, executable_authority_digest=executable["authority_digest"],
        topology_digest=context["topology_digest"], schema_digest=context["schema_digest"],
        schema_slice_digest=context["schema_slice_digest"], base_operational_digest=context["base_operational_digest"],
        expected_revision_ref=activation["expected_revision_ref"], activation_request_digest=activation_digest,
        execution_admission_request_digest=execution_digest, attempt_ref=attempt_ref, recovery_ref=recovery_ref)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    admission = values._attempt_build_portable_value(values.OntologyObjectOperationAttemptAdmission,
        attempt_body=attempt, attempt_digest=attempt.attempt_digest, provider_profile_digest=profile["profile_digest"],
        object_abi_digest=activation["object_abi_digest"], application_authority_digest=activation["application_authority_body"]["authority_digest"],
        executable_authority_digest=executable["authority_digest"], execution_admission_request_digest=execution_digest,
        preparation_disposition="prepared_without_provider_contact", provider_begin_count=0, provider_read_count=0,
        provider_action_count=0, provider_seal_count=0, provider_write_count=0, provider_recovery_count=0)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    return attempt, admission




def _validate_base(body: object) -> dict[str, Any]:
    check = _preparation_check
    check_code = check.__code__
    binding_failure = PreparationError()
    _native_inputs(body)
    raw = codec._body(body, wire.PREPARATION_BASE_CONTRACT)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    base = codec._obj(codec.decode_canonical(raw))
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    codec._wrapper(base, wire.PREPARATION_BASE_CONTRACT, codec._V4_OPERATION)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    return base




def _validate_origin(body: object, facts: dict[str, Any]) -> dict[str, Any]:
    check = _preparation_check
    check_code = check.__code__
    binding_failure = PreparationError()
    _native_inputs(body)
    raw = codec._body(body, "aware.ontology.facade-origin.v1")
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    origin = codec._obj(codec.decode_canonical(raw))
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    codec._wrapper(origin, "aware.ontology.facade-origin.v1", codec._V4_OPERATION)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    if origin["origin"] != facts["origin"]:
        raise PreparationError("binding_mismatch", "origin_mismatch")
    return origin




def _validate_facts(body: object) -> dict[str, Any]:
    check = _preparation_check
    check_code = check.__code__
    binding_failure = PreparationError()
    _native_inputs(body)
    raw = codec._body(body, wire.FACTS_CONTRACT)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    facts = codec._obj(codec.decode_canonical(raw))
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    codec._wrapper(facts, wire.FACTS_CONTRACT, codec._V4_OPERATION)
    if check.__code__ is not check_code:
        raise binding_failure
    check()
    base = _validate_base(facts["preparation_base_body"])
    operation = facts["operation"]
    for name in ("branch_ref", "provider_ref", "provider_generation", "object_abi_digest", "base_operational_digest"):
        if base[name] != operation[name]:
            raise PreparationError("binding_mismatch", "base_operation_mismatch")
    if operation["expected_revision_ref"] is not None and operation["expected_revision_ref"] != base["retained_revision_ref"]:
        raise PreparationError("source_stale", "selection_operational_base_stale")
    # The owning topology decoder is not qualified in this unit. Do not treat
    # matching framing hashes as positive lower-body semantic admission.
    return facts




def _encode_bundle(value: object) -> wire.Body:
    # Enabling this producer requires a separately accepted owning topology
    # decoder. Keep a second refusal here so no helper can mint a partial bundle.
    _native_inputs(value)
    raise PreparationError("unsupported_profile", "topology_decoder_unqualified")


def prepare_operation(*, facts_body: wire.Body, origin_body: wire.Body) -> wire.Body:
    _native_inputs(facts_body)
    _native_inputs(origin_body)
    facts = _validate_facts(facts_body)
    _validate_origin(origin_body, facts)
    raise PreparationError("unsupported_profile", "topology_decoder_unqualified")


def _install_preparation_dispatch(operation: Any = None) -> Any:
    """Definition-time guards with a one-use seal after receiver definition.

    No consumer-supplied verifier enters prepare_operation. The private decorator
    is used by the three scoped host methods to retain their actual helpers and
    constructors before the module becomes callable. Host bootstrap then seals
    both completed receiver classes; callable entrances refuse an unsealed or
    foreign receiver. The seal cannot rebaseline retained classes after import.
    """
    native_type, get, class_get = type, object.__getattribute__, type.__getattribute__
    if native_type(operation) is tuple:
        # Called only after the two owning classes are complete. Existing
        # decorated methods retain their genuine check functions in cells;
        # authenticate the wrapper/check code before invoking the one-use seal.
        installer_code = get(_install_preparation_dispatch, "__code__")
        check_code = next(c for c in installer_code.co_consts
                          if native_type(c) is native_type(installer_code) and c.co_name == "check")
        protect_code = next(c for c in installer_code.co_consts
                            if native_type(c) is native_type(installer_code) and c.co_name == "protect")
        wrapper_code = next(c for c in protect_code.co_consts
                            if native_type(c) is native_type(installer_code) and c.co_name == "protected")
        for owner in operation:
            if native_type(owner) is not type:
                raise PreparationError("malformed", "receiver_owner_must_be_exact_class")
            for target in class_get(owner, "__dict__").values():
                if native_type(target) is FunctionType and get(target, "__code__") is wrapper_code:
                    cells = dict(zip(get(target, "__code__").co_freevars, get(target, "__closure__"), strict=True))
                    verifier = get(cells["check"], "cell_contents")
                    if native_type(verifier) is not FunctionType or get(verifier, "__code__") is not check_code:
                        raise PreparationError("malformed", "receiver_seal_binding_mismatch")
                    verifier(_owners=operation)
        return None
    if operation is not None and native_type(operation) is not FunctionType:
        raise PreparationError("malformed", "host_definition_must_be_exact_function")
    native_id, length, native_tuple, native_zip, native_any = id, len, tuple, zip, any
    native_map = map
    get_dict, dict_items, dict_keys = dict.get, dict.items, dict.keys
    function_kind, module_kind = FunctionType, ModuleType
    host_type_bank = (type, str, dict, list, tuple, set, frozenset,
                      FunctionType, ModuleType, classmethod, staticmethod, property, sys.modules)
    allocate, initialize, assign = BaseException.__new__, BaseException.__init__, object.__setattr__
    exception_dictionary = BaseException.__dict__["__dict__"].__get__
    put_dictionary = dict.__setitem__
    refusal_allocate, refusal_initialize = allocate, initialize
    refusal_dictionary, refusal_put = exception_dictionary, put_dictionary
    unwind = BaseException
    primitive_namespace = get(builtins, "__dict__")
    primitive_items = native_tuple(dict_items(primitive_namespace))
    primitive_keys = native_tuple(dict_keys(primitive_namespace))
    host = operation is not None
    namespace: Any = get(operation, "__globals__") if host else globals()
    protected: Any = None
    error_kind = namespace["OntologyObjectOperationError"] if host else PreparationError
    codec_error = codec.WireError
    original_functions, wrapped_functions = [], []
    module_rows, class_rows, function_rows, data_rows = (), (), (), ()
    regex_cache_rows = ()
    host_bindings, execution_namespace = (), namespace
    receiver_owner = None
    receiver_rows: Any = ()
    receiver_function_rows: Any = ()
    receiver_data_rows: Any = ()

    def refuse(code="malformed", reason="preparation_binding_mismatch", *, framing=False):
        # Admit and retain every dispatch primitive before the first native
        # return. Rejected bindings are never used to construct their refusal.
        allocating, initializing = allocate, initialize
        dictionary, putting = exception_dictionary, put_dictionary
        if (allocating is not refusal_allocate or initializing is not refusal_initialize
                or dictionary is not refusal_dictionary or putting is not refusal_put):
            return binding_failure
        failure = allocating(codec_error if framing else error_kind)
        initializing(failure, code if framing else reason)
        # Invoke the retained native base slot directly. Attribute assignment
        # and ordinary __dict__ lookup can dispatch replaced class descriptors.
        fields = dictionary(failure)
        putting(fields, "code", code)
        if not framing:
            putting(fields, "reason", reason)
        return failure

    binding_failure = refuse()

    def state(value):
        kind = native_type(value)
        if kind is dict:
            return (native_id(kind), native_tuple((native_id(k), native_id(v)) for k, v in dict_items(value)))
        if kind is list or kind is tuple or kind is frozenset or kind is set:
            return (native_id(kind), native_tuple(native_id(item) for item in value))
        return (native_id(kind), native_id(value))

    state_code, refuse_code = get(state, "__code__"), get(refuse, "__code__")
    dictionary_kind_id, string_kind_id = native_id(dict), native_id(str)

    def check(receiver=None, *, _owners=None):
        nonlocal receiver_owner, receiver_rows, receiver_function_rows, receiver_data_rows
        # The native owner binds this one literal before any guard is installed.
        # Its actual callable then lives in the immutable authenticated CodeObject.
        native_entry: Any = "__aware_native_preparation_scan_anchor_v1__"
        native_state_entry: Any = "__aware_native_preparation_state_anchor_v1__"
        # Snapshot the new iterator dispatch before admission. Later cell or
        # namespace changes cannot replace this invocation's native callable.
        mapping = native_map
        zipping = native_zip
        # Keep native kind/length dispatch local for the complete scans. Admit
        # both snapshots against the original bank before their first use.
        kind_of = native_type
        size_of = length
        # Retain post-scan dependencies before native admission. Its return
        # cannot replace this invocation's receiver inspection or refusal path.
        post_host, post_failure = host, binding_failure
        post_namespace, post_check = namespace, check
        post_check_code = check_code
        post_host_bindings, post_execution_namespace = (
            host_bindings,
            execution_namespace,
        )
        post_receiver_rows = receiver_rows
        post_receiver_function_rows, post_receiver_data_rows = (
            receiver_function_rows,
            receiver_data_rows,
        )
        post_operation, post_protected, post_receiver_owner = (
            operation,
            protected,
            receiver_owner,
        )
        if post_host is not True and post_host is not False:
            raise post_failure
        host_context = None
        if post_host:
            bank = host_type_bank
            if bank.__class__ is not ().__class__:
                raise post_failure
            host_context = (
                *bank,
                post_host,
                post_host_bindings,
                post_namespace,
                post_execution_namespace,
                post_receiver_rows,
                post_receiver_function_rows,
                post_receiver_data_rows,
                post_operation,
                post_protected,
                post_receiver_owner,
                post_check_code,
                post_check,
                post_failure,
            )
        if native_entry.__class__ is "".__class__:
            # The literal's immutable native type belongs to the admitted checker
            # code, so a later captured binding change cannot select indexed reads.
            tuple_kind: Any = ().__class__
            # The literal's native metatype cannot be replaced through a captured
            # binding. Reject a changed kind callable before foundation dispatch.
            if kind_of is not tuple_kind.__class__:
                raise binding_failure
            # These immutable names belong to this admitted checker code. Identity
            # selects an exact native field without trusting a mutable lookup name.
            name_field, qualname_field, module_field, annotations_field = (
                "__name__", "__qualname__", "__module__", "__annotations__")
            if get(state, "__code__") is not state_code or get(refuse, "__code__") is not refuse_code:
                raise binding_failure
            current_primitives = native_tuple(dict_keys(primitive_namespace))
            # Retained native ids admit keys before equality or built-in lookup.
            for key in current_primitives:
                if native_id(native_type(key)) != string_kind_id:
                    raise binding_failure
            if current_primitives != primitive_keys:
                raise binding_failure
            admitted_mapping = admitted_identity = admitted_zipping = None
            admitted_type = admitted_length = None
            value_error = runtime_error = None
            dictionary_kind = immutable_set_kind = None
            for name, expected in primitive_items:
                if get_dict(primitive_namespace, name) is not expected:
                    raise binding_failure
                if name == "map":
                    admitted_mapping = expected
                elif name == "id":
                    admitted_identity = expected
                elif name == "zip":
                    admitted_zipping = expected
                elif name == "ValueError":
                    value_error = expected
                elif name == "RuntimeError":
                    runtime_error = expected
                elif name == "dict":
                    dictionary_kind = expected
                elif name == "frozenset":
                    immutable_set_kind = expected
                elif name == "type":
                    admitted_type = expected
                elif name == "len":
                    admitted_length = expected
            identity = native_id
            # Compare against the bank's original values, never a mutable namespace
            # reread after admission. Both dispatches stay local throughout the scan.
            if (admitted_mapping is None or admitted_identity is None
                    or admitted_zipping is None
                    or value_error is None or runtime_error is None
                    or dictionary_kind is None or immutable_set_kind is None
                    or mapping is not admitted_mapping
                    or identity is not admitted_identity
                    or zipping is not admitted_zipping):
                raise binding_failure
            if (admitted_type is None or admitted_length is None
                    or kind_of is not admitted_type or size_of is not admitted_length):
                raise binding_failure
            for module, names, items, absent in module_rows:
                if native_type(module) is not module_kind:
                    raise binding_failure
                ns = get(module, "__dict__")
                current = native_tuple(dict_keys(ns))
                for key in current:
                    if native_type(key) is not str:
                        raise binding_failure
                if current != names:
                    raise binding_failure
                for name, expected in items:
                    if get_dict(ns, name) is not expected:
                        raise binding_failure
                for name in absent:
                    if name in ns:
                        raise binding_failure
            for module, name, expected_id in regex_cache_rows:
                cache = get_dict(get(module, "__dict__"), name)
                if native_type(cache) is not dict or native_id(cache) != expected_id:
                    raise binding_failure
            for cls, expected_type, bases, mro, metadata, items, names in (*class_rows, *(row[2] for row in receiver_rows)):
                if native_type(cls) is not expected_type or class_get(cls, "__bases__") is not bases or class_get(cls, "__mro__") is not mro:
                    raise binding_failure
                for name, expected in metadata:
                    if class_get(cls, name) is not expected:
                        raise binding_failure
                ns = class_get(cls, "__dict__")
                if native_tuple(ns) != names:
                    raise binding_failure
                for name, expected in items:
                    if ns.get(name) is not expected:
                        raise binding_failure
            # Retain both immutable table references before the first row scan.
            # Native tuple groups preserve row order without flattening their rows.
            for function_group in (function_rows, receiver_function_rows):
                if kind_of(function_group) is not tuple_kind:
                    raise binding_failure
                for (target, code, defaults, kwdefaults, attributes, metadata,
                     cells) in function_group:
                    # Exact native functions and cells have immutable native slot
                    # descriptors. Admit their kind before direct access; foreign rows
                    # must refuse before any attribute behavior can run.
                    if kind_of(target) is not function_kind:
                        raise binding_failure
                    if (target.__code__ is not code or target.__defaults__ is not defaults
                        or target.__kwdefaults__ is not kwdefaults):
                        raise binding_failure
                    # The original dictionary remains in the complete data table below.
                    # Fresh identity here permits one content check, rather than two.
                    # Replacing the dictionary still requires the original full state.
                    current_attributes = target.__dict__
                    if ((kind_of(current_attributes) is not dict
                            or current_attributes is not attributes[0])
                            and state(current_attributes) != attributes[1]):
                        raise binding_failure
                    for name, expected in metadata:
                        # Only original code-derived names select immutable native
                        # function slots. Every row still compares its retained value;
                        # other names keep the admitted native accessor and full lookup.
                        if name is name_field:
                            if target.__name__ is not expected:
                                raise binding_failure
                        elif name is qualname_field:
                            if target.__qualname__ is not expected:
                                raise binding_failure
                        elif name is module_field:
                            if target.__module__ is not expected:
                                raise binding_failure
                        elif name is annotations_field:
                            if target.__annotations__ is not expected:
                                raise binding_failure
                        elif get(target, name) is not expected:
                            raise binding_failure
                    for cell, expected in cells:
                        if (kind_of(cell) is not CellType
                                or cell.cell_contents is not expected):
                            raise binding_failure
            # Retain both immutable table references before the first row scan.
            # Native tuple groups preserve row order without flattening their rows.
            for data_group in (data_rows, receiver_data_rows):
                if kind_of(data_group) is not tuple_kind:
                    raise binding_failure
                for value, expected in data_group:
                    if expected[0] == dictionary_kind_id:
                        # Compare every retained native key/value identity directly.
                        # No transient fingerprint tuples, foreign hashing/equality,
                        # or strong references replacing the retained integer ids.
                        if kind_of(value) is not dictionary_kind:
                            raise binding_failure
                        item_count = size_of(value)
                        if item_count != size_of(expected[1]):
                            raise binding_failure
                        if not item_count:
                            # Fresh exact-kind and length checks fully admit an empty
                            # dictionary; there are no key/value identities to scan.
                            continue
                        # Exact dictionaries have immutable native iterator/value
                        # descriptors. Retain the key map so each key identity is read
                        # before fetching its mutable value. Read the value identity
                        # directly before either comparison, without a second map.
                        try:
                            for key_id, item_id, (expected_key, expected_item) in zipping(
                                    mapping(identity, value), value.values(),
                                    expected[1], strict=True):
                                item_id = identity(item_id)
                                if key_id != expected_key or item_id != expected_item:
                                    raise binding_failure
                        except (value_error, runtime_error):
                            # Dictionary mutation while creating/consuming the two
                            # native views remains a binding refusal.
                            raise binding_failure from None
                    elif ((kind := kind_of(value)) is native_tuple
                            or kind is list or kind is frozenset or kind is set):
                        # Admit each exact native container before iterating. Retained
                        # children still have their own complete rows below; compare
                        # every element identity without a Python generator/fingerprint.
                        identities = expected[1]
                        if (native_id(kind) != expected[0]
                                or kind_of(identities) is not tuple_kind
                                or (item_count := size_of(value)) != size_of(identities)):
                            raise binding_failure
                        # Exact tuples and their admitted expectation tuples cannot
                        # change size or items during these native indexed reads.
                        # Observe every identity in order, with the same comparisons;
                        # mutable containers keep strict iterator cardinality below.
                        if kind is tuple_kind and item_count <= 3:
                            if not item_count:
                                continue
                            if identity(value[0]) != identities[0]:
                                raise binding_failure
                            if item_count == 1:
                                continue
                            if identity(value[1]) != identities[1]:
                                raise binding_failure
                            if item_count == 2:
                                continue
                            if identity(value[2]) != identities[2]:
                                raise binding_failure
                            continue
                        if kind is tuple_kind or kind is immutable_set_kind:
                            # The container and expectation tuple are exact, admitted
                            # and immutable. Read every
                            # original item identity directly, retaining the original
                            # integer comparison and strict cardinality refusal while
                            # avoiding a separate native map iterator for larger tuples
                            # and frozensets. The frozen kind is retained from the
                            # original admitted bank before the complete scans.
                            try:
                                for item, expected_id in zipping(
                                        value, identities, strict=True):
                                    if identity(item) != expected_id:
                                        raise binding_failure
                            except value_error:
                                raise binding_failure from None
                            continue
                        try:
                            for item_id, expected_id in native_zip(
                                    mapping(identity, value), identities, strict=True):
                                if item_id != expected_id:
                                    raise binding_failure
                        except value_error:
                            # A mutable sequence can change length after admission.
                            # Native zip's cardinality refusal remains a binding refusal.
                            raise binding_failure from None
                    elif state(value) != expected:
                        raise binding_failure
            field_read = get
            dictionary_read = get_dict
            type_read = class_get
            identity_of = native_id
            tuple_of = native_tuple
            any_of = native_any
            dictionary_keys = dict_keys
            dictionary_items = dict_items
            fingerprint: Any = state
        elif native_entry.__class__ is ().__new__.__class__:
            field_read = get
            dictionary_read = get_dict
            type_read = class_get
            identity_of = native_id
            tuple_of = native_tuple
            any_of = native_any
            dictionary_keys = dict_keys
            dictionary_items = dict_items
            if native_state_entry.__class__ is not ().__new__.__class__:
                raise binding_failure
            if post_host:
                admitted = native_entry(
                    post_check,
                    post_check_code,
                    mapping,
                    zipping,
                    kind_of,
                    size_of,
                    field_read,
                    dictionary_read,
                    type_read,
                    identity_of,
                    tuple_of,
                    any_of,
                    dictionary_keys,
                    dictionary_items,
                    host_context,
                )
            else:
                admitted = native_entry(
                    post_check,
                    post_check_code,
                    mapping,
                    zipping,
                    kind_of,
                    size_of,
                    field_read,
                    dictionary_read,
                    type_read,
                    identity_of,
                    tuple_of,
                    any_of,
                    dictionary_keys,
                    dictionary_items,
                )
            if admitted is not True:
                raise post_failure
            fingerprint = native_state_entry
        else:
            raise binding_failure
        if post_host:
            if host_context is None:
                raise post_failure
            post_kind_of = kind_of
            (
                post_type,
                post_str,
                post_dict,
                post_list,
                post_tuple,
                post_set,
                post_frozenset,
                post_function,
                post_module,
                post_classmethod,
                post_staticmethod,
                post_property,
                post_modules,
            ) = host_context[:13]
            if (
                post_kind_of(post_namespace) is not post_dict
                or post_kind_of(post_execution_namespace) is not post_dict
            ):
                raise post_failure
            for name, present, expected in post_host_bindings:
                if (name in post_namespace) is not present or dictionary_read(
                    post_namespace, name
                ) is not expected:
                    raise post_failure
            if (
                dictionary_read(post_execution_namespace, "_preparation_check")
                is not post_check
            ):
                raise post_failure
            for owner_namespace, name, row in post_receiver_rows:
                if dictionary_read(owner_namespace, name) is not row[0]:
                    raise post_failure
            if _owners is not None:
                if post_kind_of(_owners) is not tuple_of or not _owners:
                    raise post_failure
                added_rows, added_functions, added_data = [], [], []
                already = {identity_of(row[2][0]) for row in post_receiver_rows}
                for owner in _owners:
                    if post_kind_of(owner) is not post_type:
                        raise post_failure
                    owner_name = type_read(owner, "__name__")
                    module_name = type_read(owner, "__module__")
                    if (
                        post_kind_of(owner_name) is not post_str
                        or post_kind_of(module_name) is not post_str
                    ):
                        raise post_failure
                    if (module_name, owner_name) not in (
                        ("aware_ontology_runtime.object_runtime", "OntologyRuntime"),
                        (
                            "aware_ontology_runtime.object_source_provider",
                            "_OntologyObjectCompositionPrecontactAdmission",
                        ),
                    ):
                        raise post_failure
                    owner_module = dictionary_read(post_modules, module_name)
                    if post_kind_of(owner_module) is not post_module:
                        raise post_failure
                    owner_namespace = field_read(owner_module, "__dict__")
                    if dictionary_read(owner_namespace, owner_name) is not owner:
                        raise post_failure
                    if identity_of(owner) in already:
                        continue
                    items = tuple_of(type_read(owner, "__dict__").items())
                    if any_of(post_kind_of(name) is not post_str for name, _ in items):
                        raise post_failure
                    operation_qualname = field_read(post_operation, "__qualname__")
                    operation_name = field_read(post_operation, "__name__")
                    if (
                        post_kind_of(operation_qualname) is not post_str
                        or post_kind_of(operation_name) is not post_str
                    ):
                        raise post_failure
                    if operation_qualname.split(".")[0] == owner_name:
                        if (
                            type_read(owner, "__dict__").get(operation_name)
                            is not post_protected
                        ):
                            raise post_failure
                        post_receiver_owner = owner
                    row = (
                        owner,
                        post_kind_of(owner),
                        type_read(owner, "__bases__"),
                        type_read(owner, "__mro__"),
                        tuple_of(
                            (name, type_read(owner, name))
                            for name in ("__name__", "__qualname__", "__module__")
                        ),
                        items,
                        tuple_of(name for name, _ in items),
                    )
                    added_rows.append((owner_namespace, owner_name, row))
                    pending, seen, containers = [], post_set(), post_set()
                    for _, descriptor in items:
                        if (
                            post_kind_of(descriptor) is post_classmethod
                            or post_kind_of(descriptor) is post_staticmethod
                        ):
                            pending.append(field_read(descriptor, "__func__"))
                        elif post_kind_of(descriptor) is post_property:
                            pending.extend(
                                value
                                for name in ("fget", "fset", "fdel")
                                if (value := field_read(descriptor, name)) is not None
                            )
                        elif post_kind_of(descriptor) is post_function:
                            pending.append(descriptor)

                    def retain_receiver_data(value):
                        kind = post_kind_of(value)
                        if (
                            kind is not post_dict
                            and kind is not post_list
                            and kind is not post_tuple
                            and kind is not post_frozenset
                            and kind is not post_set
                        ):
                            return
                        if identity_of(value) in containers:
                            return
                        containers.add(identity_of(value))
                        added_data.append((value, fingerprint(value)))
                        contents = (
                            (item for pair in dictionary_items(value) for item in pair)
                            if kind is post_dict
                            else value
                        )
                        for item in contents:
                            retain_receiver_data(item)

                    while pending:
                        target = pending.pop()
                        if (
                            post_kind_of(target) is not post_function
                            or identity_of(target) in seen
                        ):
                            continue
                        seen.add(identity_of(target))
                        # Each guarded entrance authenticates its own post_check code.
                        # Setup tables of the other guards finish sealing below;
                        # capturing those evolving control cells would be stale.
                        if field_read(target, "__code__") is post_check_code:
                            continue
                        cells = tuple_of(
                            (cell, field_read(cell, "cell_contents"))
                            for cell in field_read(target, "__closure__") or ()
                        )
                        defaults, kwdefaults = (
                            field_read(target, "__defaults__"),
                            field_read(target, "__kwdefaults__"),
                        )
                        added_functions.append(
                            (
                                target,
                                field_read(target, "__code__"),
                                defaults,
                                kwdefaults,
                                (
                                    field_read(target, "__dict__"),
                                    fingerprint(field_read(target, "__dict__")),
                                ),
                                tuple_of(
                                    (name, field_read(target, name))
                                    for name in (
                                        "__name__",
                                        "__qualname__",
                                        "__module__",
                                        "__annotations__",
                                    )
                                ),
                                cells,
                            )
                        )
                        for value in (
                            field_read(target, "__dict__"),
                            field_read(target, "__annotations__"),
                            defaults,
                            kwdefaults,
                        ):
                            retain_receiver_data(value)
                        pending.extend(
                            value
                            for _, value in cells
                            if post_kind_of(value) is post_function
                        )
                if not added_rows:
                    raise post_failure  # No recapture/restamp after import.
                receiver_rows = post_receiver_rows + tuple_of(added_rows)
                receiver_function_rows = post_receiver_function_rows + tuple_of(
                    added_functions
                )
                receiver_data_rows = post_receiver_data_rows + tuple_of(added_data)
                receiver_owner = post_receiver_owner
                if post_receiver_owner is None:
                    raise post_failure
                return
            if (
                post_receiver_owner is None
                or post_kind_of(receiver) is not post_receiver_owner
            ):
                raise post_failure
            if post_kind_of(post_receiver_owner) is not post_type:
                raise post_failure
            if type_read(post_receiver_owner, "__dictoffset__"):
                if native_entry.__class__ is "".__class__:
                    instance = field_read(receiver, "__dict__")
                else:
                    instance = fingerprint(receiver, post_receiver_owner)
                if post_kind_of(instance) is not post_dict or any_of(
                    post_kind_of(key) is not post_str
                    for key in dictionary_keys(instance)
                ):
                    raise post_failure
                # A class descriptor post_check alone does not reject instance-level
                # shadows of the same methods/properties.
                for name, descriptor in type_read(
                    post_receiver_owner, "__dict__"
                ).items():
                    if post_kind_of(name) is not post_str:
                        raise post_failure
                    kind = post_kind_of(descriptor)
                    if (
                        kind is post_function
                        or kind is post_property
                        or kind is post_classmethod
                        or kind is post_staticmethod
                    ) and name in instance:
                        raise post_failure
        else:
            if kind_of(post_namespace) is not {}.__class__:
                raise post_failure
            if dictionary_read(post_namespace, "_preparation_check") is not post_check:
                raise post_failure

    check_code = get(check, "__code__")
    def protect(target, *, framing=False, execute=None):
        original_functions.append(target)
        target_code = get(target, "__code__")
        def protected(*args, **kwargs):
            if get(refuse, "__code__") is not refuse_code:
                raise binding_failure
            if get(check, "__code__") is not check_code or get(target, "__code__") is not target_code:
                raise binding_failure
            receiver = args[0] if host and args else get_dict(kwargs, "self") if host else None
            # Propagate the guard's original typed rejection; never reconstruct
            # it through a binding that the guard rejected.
            check(receiver)
            try:
                result = (target if execute is None else execute)(*args, **kwargs)
            except unwind as error:
                if get(check, "__code__") is not check_code:
                    raise binding_failure from None
                check(receiver)
                if not host and not framing and native_type(error) is not error_kind and isinstance(error, (TypeError, ValueError)):
                    code = get(error, "code") if native_type(error) is codec_error else "malformed"
                    reason = str(error)
                    check(receiver)
                    raise refuse(code, reason) from None
                raise
            if get(check, "__code__") is not check_code:
                raise binding_failure
            check(receiver)
            return result
        for name in ("__name__", "__qualname__", "__module__", "__annotations__"):
            assign(protected, name, get(target, name))
        get(protected, "__dict__")["__wrapped__"] = target
        wrapped_functions.append(protected)
        return protected

    if host:
        # Native built-ins remain lookup dependencies even when absent globals.
        names = set(operation.__code__.co_names) | set(primitive_namespace) | {"_CapabilityRegistry"}
        host_bindings = native_tuple((name, name in namespace, get_dict(namespace, name)) for name in sorted(names))
        execution_namespace = dict(namespace)
        execution_namespace["_preparation_check"] = check
        clone = FunctionType(operation.__code__, execution_namespace, operation.__name__, operation.__defaults__, operation.__closure__)
        clone.__kwdefaults__ = operation.__kwdefaults__
        protected = protect(operation, execute=clone)
        classes = [value for name, present, value in host_bindings if present and isinstance(value, type)]
        matching_view = codec.re
        regex_module = get(matching_view, "__dict__")["_source"]
        regex_cache_rows = native_tuple((regex_module, name, native_id(value))
            for name, value in dict_items(get(regex_module, "__dict__")) if name == "_cache" or name == "_cache2")
        modules = (sys.modules[__name__], *values._topology_modules, matching_view, regex_module, get(regex_module, "__dict__")["_compiler"], get(regex_module, "__dict__")["_parser"])
    else:
        # Preserve the codec's original source and three fixed expressions.
        # After authenticated import, matching uses retained native Pattern
        # methods; no mutable Python compiler/cache helper is dispatched.
        regex_module = codec.re
        compiled_matchers = native_tuple((pattern, regex_module.compile(pattern).fullmatch)
            for pattern in (r"sha256:[0-9a-f]{64}", r"[0-9a-f]+", r"[0-9a-f]{64}"))
        regex_failure = refuse(framing=True)
        def native_fullmatch(pattern, string, flags=0):
            if native_type(pattern) is not str or native_type(string) is not str or native_type(flags) is not int or flags != 0:
                raise regex_failure
            for expression, matching in compiled_matchers:
                if pattern == expression:
                    return matching(string)
            raise regex_failure
        matching_view = module_kind(codec.__name__ + "._retained_matching")
        get(matching_view, "__dict__")["fullmatch"] = protect(native_fullmatch, framing=True)
        get(matching_view, "__dict__")["_source"] = regex_module
        get(codec, "__dict__")["re"] = matching_view
        regex_cache_rows = native_tuple((regex_module, name, native_id(value))
            for name, value in dict_items(get(regex_module, "__dict__")) if name == "_cache" or name == "_cache2")
        for name, target in native_tuple(dict_items(namespace)):
            if native_type(target) is function_kind and name != "_install_preparation_dispatch":
                namespace[name] = protect(target)
        codec_namespace: Any = get(codec, "__dict__")
        for name, target in native_tuple(dict_items(codec_namespace)):
            if native_type(target) is function_kind and target.__module__ == codec.__name__:
                codec_namespace[name] = protect(target, framing=True)
        # cast is a Python return inside the owning textual helper. Retain its
        # original implementation as well as its wrapper; _text authenticates
        # the complete owner again after either return before continuation.
        codec_namespace["cast"] = protect(codec_namespace["cast"], framing=True)
        codec_namespace["_preparation_check"] = check
        codec_namespace["_preparation_failure"] = binding_failure
        namespace["_preparation_check"] = check
        classes = [PreparationError, codec.WireError, codec._Policy, codec._OperationProfile,
                   json.JSONEncoder, json.JSONDecoder, json.JSONDecodeError, *values._attempt_classes]
        modules = (sys.modules[__name__], codec, wire, values, *values._topology_modules, json, sys.modules["json.encoder"],
                   sys.modules["json.decoder"], sys.modules["json.scanner"], hashlib,
                   matching_view, regex_module, get(regex_module, "__dict__")["_compiler"], get(regex_module, "__dict__")["_parser"])
    if _native_scan_module is not None:
        modules = (*modules, _native_scan_module)
    module_rows = native_tuple((module, native_tuple(dict_keys(vars(module))),
        native_tuple((name, value) for name, value in dict_items(vars(module))
            if not (native_any(module is cached_module and name == cache_name
                               for cached_module, cache_name, _ in regex_cache_rows))),
        native_tuple(name for name in primitive_namespace if name not in vars(module))) for module in modules)
    class_rows = native_tuple((cls, native_type(cls), class_get(cls, "__bases__"), class_get(cls, "__mro__"), native_tuple((name, class_get(cls, name)) for name in ("__name__", "__qualname__", "__module__")), items,
        native_tuple(name for name, _ in items)) for cls in classes
        for items in (native_tuple(class_get(cls, "__dict__").items()),))
    pending = [*original_functions, *wrapped_functions]
    for module in modules:
        pending.extend(value for value in vars(module).values() if native_type(value) is function_kind)
    for _, _, _, _, _, items, _ in class_rows:
        for _, value in items:
            if native_type(value) is classmethod or native_type(value) is staticmethod:
                value = value.__func__
            if native_type(value) is function_kind:
                pending.append(value)
    rows, seen = [], set()
    while pending:
        target = pending.pop()
        if target is check or native_id(target) in seen:
            continue
        seen.add(native_id(target))
        cells = native_tuple((cell, get(cell, "cell_contents")) for cell in get(target, "__closure__") or ())
        rows.append((target, get(target, "__code__"), get(target, "__defaults__"), get(target, "__kwdefaults__"), (get(target, "__dict__"), state(get(target, "__dict__"))), native_tuple((name, get(target, name)) for name in ("__name__", "__qualname__", "__module__", "__annotations__")), cells))
        pending.extend(value for _, value in cells if native_type(value) is function_kind and value is not check)
    function_rows = native_tuple(rows)
    # Retain every nested native metadata container once. Identity comparisons
    # never invoke a foreign operand and do not rebuild a recursive fingerprint
    # on every leaf return. The complete built-in namespace is checked above.
    data, container_seen = [], set()
    def retain(value):
        kind = native_type(value)
        if kind is not dict and kind is not list and kind is not tuple and kind is not frozenset and kind is not set:
            return
        if native_id(value) in container_seen or value is primitive_namespace:
            return
        container_seen.add(native_id(value))
        data.append((value, state(value)))
        contents = (item for pair in dict_items(value) for item in pair) if kind is dict else value
        for item in contents:
            retain(item)
    for _, _, items, _ in module_rows:
        for name, value in items:
            if name != "__builtins__":
                retain(value)
    for _, _, _, _, _, items, _ in class_rows:
        for _, value in items:
            retain(value)
    for target, _, defaults, kwdefaults, _, _, _ in function_rows:
        retain(get(target, "__dict__"))
        retain(get(target, "__annotations__"))
        retain(defaults)
        retain(kwdefaults)
    data_rows = native_tuple(data)
    return protected if host else None


if _native_scan_module is not None:
    # Fixed native-entry constant binding changes constants only. The same bound
    # nested code is used by ordinary guards and the original one-use host seal.
    _native_scan_module.bind_installer(_install_preparation_dispatch)
_install_preparation_dispatch()
