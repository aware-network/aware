import asyncio
import json

import pytest
from aware_ontology_object_facade_client.history import (
    ObjectHistoryContext,
    ObjectHistoryCoverage,
    ObjectHistoryCursor,
    ObjectHistoryDemand,
    ObjectHistoryError,
    ObjectHistoryGroup,
    ObjectHistoryPage,
    ObjectHistoryTransition,
    decode_object_history,
)


class _UnusedHistoryReads:
    async def read_page(self, **kwargs) -> ObjectHistoryPage:
        raise AssertionError("unexpected page dispatch")

    async def read_group(self, cursor) -> ObjectHistoryGroup:
        raise AssertionError("unexpected group dispatch")

    async def read_transition(self, group, demand) -> ObjectHistoryTransition:
        raise AssertionError("unexpected transition dispatch")

    async def wait(self, **kwargs) -> None:
        raise AssertionError("unexpected wait dispatch")


def test_strict_owner_roundtrip_and_direct_reinitialization_refusal():
    value = ObjectHistoryDemand(
        "subject:one", "example.Type", ("example.Type.x",), (), "projection:one"
    )
    assert (
        decode_object_history(value.canonical_bytes()).canonical_bytes()
        == value.canonical_bytes()
    )
    body = value.canonical_bytes()
    object.__setattr__(value, "subject_ref", "subject:other")
    with pytest.raises(ObjectHistoryError):
        value.__post_init__()
    object.__setattr__(value, "subject_ref", "subject:one")
    with pytest.raises(ObjectHistoryError):
        value.canonical_bytes()
    assert ObjectHistoryDemand.from_canonical_bytes(body).subject_ref == "subject:one"


@pytest.mark.parametrize("bad", [True, 1.0, "1", -1])
def test_direct_and_decoded_exact_unsigned_cursor(bad):
    with pytest.raises(ObjectHistoryError):
        ObjectHistoryCursor(b"opaque", "sha256:" + "a" * 64, bad)
    raw = [
        "aware.ontology.object-history.v1",
        1,
        "cursor",
        ["", "sha256:" + "a" * 64, bad],
    ]
    with pytest.raises(ObjectHistoryError):
        decode_object_history(json.dumps(raw, separators=(",", ":")).encode())


def test_nested_restamping_and_bool_integer_wire_refuse():
    demand = ObjectHistoryDemand(
        "subject:one", "example.Type", ("field:x",), (), "projection:one"
    )
    value = ObjectHistoryCoverage(demand, True, True, "sha256:" + "a" * 64)
    raw = json.loads(value.canonical_bytes())
    raw[3][1] = 1
    with pytest.raises(ObjectHistoryError):
        decode_object_history(json.dumps(raw, separators=(",", ":")).encode())
    object.__setattr__(demand, "type_ref", "example.Foreign")
    with pytest.raises(ObjectHistoryError):
        value.canonical_bytes()
    with pytest.raises(ObjectHistoryError):
        value.canonical_bytes()


def test_context_close_releases_only_its_injected_port_borrow():
    class Port(_UnusedHistoryReads):
        def __init__(self):
            self.closed = 0

        def close(self):
            self.closed += 1

    port = Port()
    context = ObjectHistoryContext(port=port)
    context.close()
    context.close()
    assert port.closed == 1
    with pytest.raises(ObjectHistoryError):
        asyncio.run(context.read_group(None))


def test_coalesced_wakes_and_cancelled_wait_do_not_invent_delivery_or_progress():
    async def run():
        cursor = ObjectHistoryCursor(b"comparison", "sha256:" + "a" * 64, 1)
        waiting = asyncio.Event()

        class Port(_UnusedHistoryReads):
            def __init__(self):
                self.after = []
                self.wakes = 0
                self.closes = 0

            async def read_page(self, **kwargs):
                self.after.append(kwargs["after"].canonical_bytes())
                return ObjectHistoryPage(cursor, cursor, cursor, (), b"comparison")

            async def wait(self, **kwargs):
                assert kwargs["after"].canonical_bytes() == cursor.canonical_bytes()
                self.wakes += 1
                if self.wakes == 3:
                    waiting.set()
                    await asyncio.Event().wait()

            def close(self):
                self.closes += 1

        port = Port()
        context = ObjectHistoryContext(port=port)
        stream = context.stream(after=cursor)
        task = asyncio.create_task(anext(stream))
        await asyncio.wait_for(waiting.wait(), timeout=1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await stream.aclose()
        assert port.after == [cursor.canonical_bytes()] * 3
        assert port.closes == 0
        context.close()
        assert port.closes == 1

    asyncio.run(run())
