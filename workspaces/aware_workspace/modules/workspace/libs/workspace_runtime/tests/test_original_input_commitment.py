"""Dormant Source prototype: independent immutable original input fields."""
import sys
from contextlib import contextmanager, suppress
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    semantic_input_expectation_integrity as integrity,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as owner
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    PACKAGE_CONTEXT_INPUT_REF,
)
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable
from test_v3_source_admission import _pre_request_source


def open_input(issuer, selected, coordinates, use_ref):
    return issuer.original_pre_request_input(
        selected,use_ref=use_ref,stage='pre_request',source_coordinates=coordinates,
        context_contracts=(owner.SemanticInputContextContract('package_context',PACKAGE_CONTEXT_INPUT_REF),),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize('field',['body','identity','source','use'])
async def test_coherent_record_and_digest_restamp_rejects(tmp_path,field):
    async with _pre_request_source(tmp_path,with_local_provider=True) as (_,_,issuer,selected,coordinates):
        session=open_input(issuer,selected,coordinates,'coherent')
        expected=session.__enter__()
        record=next(row for row in issuer._pre_request_inputs.values() if row.expected is expected)
        original_digest=expected.input_digest
        original_record_digest=record.input_digest
        body=expected.context_bodies[0]
        target,name,changed={
            'body':(body,'canonical_body',b'changed'),
            'identity':(expected.package_identity,'package_name','changed'),
            'source':(expected.source_coordinates[0],'relative_path','changed.bin'),
            'use':(expected,'use_ref','changed'),
        }[field]
        before=getattr(target,name)
        object.__setattr__(target,name,changed)
        # A real constructor may reject a mismatched inner body digest. It is
        # enough to restamp both surrounding commitments to the same new value.
        forged=ContentDigest.of_bytes(b'coherently restamped')
        object.__setattr__(expected,'input_digest',forged)
        record.input_digest=forged.value
        try:
            with pytest.raises((ContractViolation,SourceObservationUnavailable,BaseExceptionGroup)):
                issuer.validate_semantic_input_source(selected,expected=expected)
        finally:
            object.__setattr__(target,name,before)
            object.__setattr__(expected,'input_digest',original_digest)
            record.input_digest=original_record_digest
        assert not record.live
        with pytest.raises((ContractViolation,SourceObservationUnavailable)):
            issuer.validate_semantic_input_source(selected,expected=expected)
        with suppress(ContractViolation,SourceObservationUnavailable,BaseExceptionGroup):
            session.__exit__(None,None,None)
        assert not issuer._pre_request_inputs and not issuer._pre_request_origins
        with open_input(issuer,selected,coordinates,'unrelated') as other:
            issuer.validate_semantic_input_source(selected,expected=other)


@pytest.mark.asyncio
@pytest.mark.parametrize('mode',['return','raise','restore'])
@pytest.mark.parametrize('target',['alias','code'])
async def test_original_code_comparison_substitution_zero_calls(tmp_path,monkeypatch,mode,target):
    async with _pre_request_source(tmp_path,with_local_provider=True) as (_,_,issuer,selected,coordinates):
        session=open_input(issuer,selected,coordinates,'substitution')
        expected=session.__enter__()
        genuine=integrity.validate_semantic_input_expectation_coordinate
        original_code=genuine.__code__
        calls=[]
        def hostile(*args,**kwargs):
            calls.append(True)
            if mode=='restore':
                integrity.validate_semantic_input_expectation_coordinate = genuine
                genuine.__code__=original_code
            if mode=='raise':raise RuntimeError('foreign comparison')
        if target=='alias':
            monkeypatch.setattr(integrity,'validate_semantic_input_expectation_coordinate',hostile)
        else:
            genuine.__code__=hostile.__code__.replace(co_freevars=original_code.co_freevars)
        try:
            with pytest.raises((ContractViolation,SourceObservationUnavailable,BaseExceptionGroup)):
                issuer.validate_semantic_input_source(selected,expected=expected)
        finally:
            genuine.__code__=original_code
            monkeypatch.setattr(integrity, 'validate_semantic_input_expectation_coordinate', genuine)
        assert calls==[]
        with pytest.raises((ContractViolation,SourceObservationUnavailable)):
            issuer.validate_semantic_input_source(selected,expected=expected)
        with suppress(ContractViolation,SourceObservationUnavailable,BaseExceptionGroup):
            session.__exit__(None,None,None)
        assert not issuer._pre_request_origins


@pytest.mark.asyncio
async def test_closing_source_read_cannot_hide_late_context_mutation(tmp_path):
    async with _pre_request_source(tmp_path,with_local_provider=True) as (_,_,issuer,selected,coordinates):
        session=open_input(issuer,selected,coordinates,'closing')
        expected=session.__enter__()
        code=type(issuer._source).revalidate_selected_package.__code__
        body=expected.context_bodies[0];before=body.canonical_body;reads=0
        def profile(frame,event,result):
            nonlocal reads
            if frame.f_code is code and event=='return':
                reads+=1
                if reads==2:object.__setattr__(body,'canonical_body',b'late')
        previous=sys.getprofile()
        try:
            sys.setprofile(profile)
            with pytest.raises((ContractViolation,SourceObservationUnavailable,BaseExceptionGroup)):
                issuer.validate_semantic_input_source(selected,expected=expected)
        finally:
            sys.setprofile(previous)
            object.__setattr__(body,'canonical_body',before)
        assert reads>=2
        with suppress(ContractViolation,SourceObservationUnavailable,BaseExceptionGroup):
            session.__exit__(None,None,None)
        assert not issuer._pre_request_inputs and not issuer._pre_request_origins


@pytest.mark.asyncio
@pytest.mark.parametrize('entrance',['source','validation_scope','checkpoint_scope'])
async def test_replaced_input_index_retires_original_family(tmp_path,entrance):
    async with _pre_request_source(tmp_path,with_local_provider=True) as (_,_,issuer,selected,coordinates):
        session=open_input(issuer,selected,coordinates,'index-replaced')
        expected=session.__enter__()
        key,original=next((key,row) for key,row in issuer._pre_request_inputs.items() if row.expected is expected)
        clone=replace(original)
        issuer._pre_request_inputs[key]=clone
        try:
            with pytest.raises((ContractViolation,SourceObservationUnavailable,BaseExceptionGroup)):
                if entrance=='source':
                    issuer.validate_semantic_input_source(selected,expected=expected)
                elif entrance=='validation_scope':
                    with contextmanager(issuer.semantic_input_validation_scope)(selected,expected=expected):
                        raise AssertionError('substituted family entered owner scope')
                else:
                    with contextmanager(issuer.semantic_input_checkpoint_validation_scope)(selected,expected=expected,expectations=(expected,)):
                        raise AssertionError('substituted family entered checkpoint scope')
        finally:
            issuer._pre_request_inputs[key]=original
        assert not original.live
        with pytest.raises((ContractViolation,SourceObservationUnavailable)):
            issuer.validate_semantic_input_source(selected,expected=expected)
        with suppress(ContractViolation,SourceObservationUnavailable,BaseExceptionGroup):
            session.__exit__(None,None,None)
        assert not issuer._pre_request_inputs and not issuer._pre_request_origins
        with open_input(issuer,selected,coordinates,'unrelated-after-index') as other:
            issuer.validate_semantic_input_source(selected,expected=other)


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['return', 'raise', 'restore'])
async def test_late_record_descriptor_substitution_never_dispatches(tmp_path, mode):
    async with _pre_request_source(tmp_path, with_local_provider=True) as (_, _, issuer, selected, coordinates):
        session = open_input(issuer, selected, coordinates, 'late-descriptor')
        expected = session.__enter__()
        kind = type(issuer)
        original = kind._pre_request_record
        validating = kind._validate_semantic_input_source.__code__
        selected_check = kind.validate_selected_package_source.__code__
        calls = []
        injected = False

        def hostile(*args, **kwargs):
            calls.append(True)
            if mode == 'restore':
                kind._pre_request_record = original
            if mode == 'raise':
                raise RuntimeError('foreign terminal record lookup')

        def observe(frame, event, result):
            nonlocal injected
            if (not injected and event == 'return' and frame.f_code is selected_check
                    and frame.f_back is not None and frame.f_back.f_code is validating):
                injected = True
                kind._pre_request_record = hostile

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            with pytest.raises((ContractViolation, SourceObservationUnavailable, BaseExceptionGroup)):
                issuer.validate_semantic_input_source(selected, expected=expected)
        finally:
            sys.setprofile(previous)
            kind._pre_request_record = original
        assert injected
        assert calls == []
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            issuer.validate_semantic_input_source(selected, expected=expected)
        with suppress(ContractViolation, SourceObservationUnavailable, BaseExceptionGroup):
            session.__exit__(None, None, None)
        assert not issuer._pre_request_inputs and not issuer._pre_request_origins
        with open_input(issuer, selected, coordinates, 'unrelated-after-descriptor') as other:
            issuer.validate_semantic_input_source(selected, expected=other)
