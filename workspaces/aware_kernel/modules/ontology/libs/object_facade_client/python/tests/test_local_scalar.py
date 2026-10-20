import asyncio
import json

import pytest
from aware_ontology_object_facade_client import LocalScalarClient, ScalarInvocationError


@pytest.mark.parametrize("field,value", [("settled", False), ("worker_cleaned", False), ("value", 42.0)])
def test_incomplete_or_foreign_success_refuses(field, value):
    class Transport:
        async def exchange(self, body):
            row = json.loads(body)
            row.update(contract="aware.ontology.local-scalar.result.v1", status="complete", value=42,
                settled=True, worker_cleaned=True, receipt={"invocation_ref":"i:1", "attempt_ref":"a:1",
                    "receipt_digest":"sha256:"+"a"*64,"outcome":"no_op"})
            row[field] = value
            return json.dumps(row).encode()
    with pytest.raises(ScalarInvocationError, match="scalar.invalid_response"):
        asyncio.run(LocalScalarClient(Transport()).invoke_scalar(object_ref="o:1",action_ref="a:1",invocation_key="k:1"))


@pytest.mark.parametrize("change", (
    {"state": "complete"}, {"revision": True}, {"state": "backend_settled"},
    {"backend_receipt": {"value": 42}}, {"journal_state": "verified_no_effect"},
    {"object_ref": "foreign"}, {"recovery_ref": "foreign"}, {"worker_cleaned": True},
))
def test_status_rejects_foreign_or_success_claims(change):
    class Transport:
        async def exchange(self, body):
            row = json.loads(body)
            row.update(contract="aware.ontology.local-scalar.status.v1", state="pending", journal_state="admitted",
                revision=1, invocation_ref="i:1", recovery_ref="a:1", backend_receipt=None)
            row.update(change)
            return json.dumps(row).encode()
    with pytest.raises(ScalarInvocationError, match="scalar.invalid_response"):
        asyncio.run(LocalScalarClient(Transport()).invocation_status(object_ref="o:1", action_ref="a:1",
            invocation_key="k:1", recovery_ref="a:1"))


@pytest.mark.parametrize("response", (b"[]", b"{", b'{"x":1,"x":1}', b"x" * 65537))
def test_status_refuses_invalid_framing(response):
    class Transport:
        async def exchange(self, body):
            return response
    with pytest.raises(ScalarInvocationError, match="scalar.invalid_response"):
        asyncio.run(LocalScalarClient(Transport()).invocation_status(object_ref="o:1", action_ref="a:1", invocation_key="k:1"))
