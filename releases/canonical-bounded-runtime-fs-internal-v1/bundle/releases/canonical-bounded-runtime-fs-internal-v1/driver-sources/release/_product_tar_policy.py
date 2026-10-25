"""Private product header/PAX policy at the original tar dispatch hook.

No framing grammar, IO owner, checksum/catalog verdict or feeder mounting.
The original parser still allocates a bounded PAX payload/raw-record list;
this source does not claim a pre-allocation bound on that list's record count.
"""

from __future__ import annotations

import tarfile

_PROC = vars(tarfile.TarInfo)["_proc_member"]
_PAX = vars(tarfile.TarInfo)["_proc_pax"]
HEADERS = 16384
PAX_BYTES = 16384
PAX_TOTAL = 1048576
PAX_DEPTH = 8
PAX_RECORDS = 64
DECODED_BYTES = 671088640


def _path(value):
    if (
        type(value) is not str
        or not value
        or len(value) > 4096
        or len(value.encode("utf-8", "strict")) > 4096
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or any(part in ("", ".", "..") for part in value.split("/"))
        or "\\" in value
    ):
        raise ValueError("product_canonical_effective_path_required")
    return value


class ProductHeaderError(RuntimeError):
    def __init__(self, policy, item, archive, phase, returned, cause):
        super().__init__("private_product_header_" + phase)
        self.original_item = item
        self.phase = phase
        self.original_archive = archive
        self.original_return = returned
        self.header_prefix = tuple(policy.headers)
        self.original_return_prefix = tuple(policy.returns)
        self.pax_bytes = policy.pax_bytes
        self.primary_cause = cause
        self.catalog_verified = False
        self.cleanup = "not_observed"
        self.authorizes_retry = False


class _PathHeaders(dict):
    """Observe original parser assignments; no PAX record grammar duplicated."""

    __slots__ = ("policy", "records")

    def __init__(self, policy):
        super().__init__()
        self.policy = policy
        self.records = 0

    def copy(self):
        return _PathHeaders(self.policy)

    def __setitem__(self, key, value):
        if self.records >= PAX_RECORDS:
            raise ValueError("product_pax_record_capacity")
        self.records += 1
        if key != "path" or self.policy.path_seen:
            raise ValueError("product_pax_path_only_no_duplicate")
        _path(value)
        self.policy.path_seen = True
        super().__setitem__(key, value)


class _ProductHeaderPolicy:
    def __init__(self):
        self.headers = []
        self.returns = []
        self.pax_bytes = 0
        self.depth = 0
        self.path_seen = False

    def tarinfo_type(self):
        policy = self

        class ProductTarInfo(tarfile.TarInfo):
            __slots__ = ()

            def _proc_member(self, archive):
                return policy.process(self, archive)

        return ProductTarInfo

    def process(self, item, archive):
        phase = "header"
        returned = None
        entered = False
        previous = None
        try:
            if (
                vars(tarfile.TarInfo)["_proc_member"] is not _PROC
                or vars(tarfile.TarInfo)["_proc_pax"] is not _PAX
            ):
                raise ValueError("original_tar_dispatch_required")
            if len(self.headers) >= HEADERS:
                raise ValueError("product_raw_header_capacity")
            # Snapshot before original PAX application mutates the next item.
            self.headers.append((item, item.name, item.type, item.size, item.offset))
            if item.type not in (
                tarfile.REGTYPE,
                tarfile.AREGTYPE,
                tarfile.DIRTYPE,
                tarfile.XHDTYPE,
            ):
                raise ValueError("product_header_type_refused")
            if type(item.size) is not int or not 0 <= item.size <= DECODED_BYTES:
                raise ValueError("product_header_size_refused")
            if item.type == tarfile.DIRTYPE and item.size != 0:
                raise ValueError("product_directory_body_refused")
            if item.type == tarfile.XHDTYPE or self.depth:
                # Original writers use ././@PaxHeader and may truncate the
                # following raw name mid-component. Neither is an effective
                # member path; validate that only after original PAX applies.
                if (
                    type(item.name) is not str
                    or not item.name
                    or len(item.name.encode("utf-8", "strict")) > 4096
                    or any(ord(char) < 32 or ord(char) == 127 for char in item.name)
                ):
                    raise ValueError("product_raw_extension_name_refused")
            else:
                _path(item.name)
            if item.type == tarfile.XHDTYPE:
                if (
                    not 0 < item.size <= PAX_BYTES
                    or self.pax_bytes + item.size > PAX_TOTAL
                    or self.depth >= PAX_DEPTH
                ):
                    raise ValueError("product_pax_capacity")
                # Before original _proc_pax reads/allocates its extension body.
                self.pax_bytes += item.size
                if self.depth == 0:
                    self.path_seen = False
                self.depth += 1
                entered = True
                previous = archive.pax_headers
                if previous:
                    raise ValueError("product_global_pax_context_refused")
                archive.pax_headers = _PathHeaders(self)
            phase = "original_dispatch"
            returned = _PROC(item, archive)
            self.returns.append(returned)
            phase = "effective_header"
            if type(returned) is not type(item):
                raise ValueError("original_product_tarinfo_required")
            if entered or not self.depth:
                _path(returned.name)
            if returned.type not in (
                tarfile.REGTYPE,
                tarfile.AREGTYPE,
                tarfile.DIRTYPE,
            ):
                raise ValueError("product_effective_type_refused")
            return returned
        except BaseException as cause:
            raise ProductHeaderError(
                self, item, archive, phase, returned, cause
            ) from cause
        finally:
            if entered:
                archive.pax_headers = previous
                self.depth -= 1
