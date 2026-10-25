"""Fixed original preinstall source binding, not an installer or IO authority.

Only trusted original module bodies are executed. Physical source guards remain
observational; stdlib/interpreter provenance is supplied by the caller's qualified
environment. Serialized same-thread use only, not public concurrent import.
"""

from __future__ import annotations

import builtins
import hashlib
import os
import sys
import threading
import types
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

PROFILE = "original-consumer-source-binding-v1"
NAMESPACE = "_aware_release_consumer_v1"
PINS = {
    "_product_capture_mount": [
        "6142fef7363afe0970adfc32eb87bf4c35dcd4de9758c2abbe62cc630bc80671",
        9302,
    ],
    "_product_catalog_flow": [
        "790d8b419201fa9579723aa5efd2c064b2aa27c447f5056e616002f0d8d0ec37",
        13524,
    ],
    "_product_catalog_receiving": [
        "69d49c3664b3d87e3d4a7c7cb258bdd8004af11cd25bd172737251b8748fa425",
        21408,
    ],
    "_product_member_capture": [
        "5267122f481995f5fed7a846866a72dc6f34cbb61d9cbecae196faa52c26284f",
        7121,
    ],
    "_product_member_receiving": [
        "176b50011be23ab1bed6546e9af9f955abb40c8179b35bafd1841a614b125617",
        7104,
    ],
    "_product_member_replay": [
        "5d19cd678743b32e539989f9a38ed84576b48ccda29777550fdc2aed74135699",
        7226,
    ],
    "_product_nested_mount": [
        "8e379ebcbaf4e648a349192211e5488087f15edab7d7ddf6803a7601d892a581",
        15257,
    ],
    "_product_parent_member_feed": [
        "49c633a17e2ec49f3b8def24aa39a4e9944c860f1a307c0a24c063a76a2f49ed",
        12336,
    ],
    "_product_stream_catalog": [
        "9da66543935b6d2c0b5d8a27047a7e3add1222da29482e7f9b2710437aae7385",
        22395,
    ],
    "_product_stream_flow": [
        "d6af0d78f8214c7d2702ac7a0611ff6a14e477624ea680c0ef6fdf1947399ab9",
        20039,
    ],
    "_product_stream_receiving": [
        "491f1ea5563e13bc5716e878f514fef41fb070fdeaeb4356f95c430f28a857bb",
        12732,
    ],
    "_product_tar_policy": [
        "70ca30432e3b214ff9c0321679f480f9d29cd79ac68b72c820d1fc678bca660e",
        6222,
    ],
    "whole_envelope": [
        "c5d8d499c18c5fd49110a1247b7f29a2021101bbd7f0b55cfb86e0bbc0ff29da",
        45981,
    ],
}
PINS = types.MappingProxyType({name: tuple(row) for name, row in PINS.items()})
STDLIB = frozenset(
    [
        "__future__",
        "ast",
        "dataclasses",
        "gzip",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "platform",
        "re",
        "stat",
        "subprocess",
        "tarfile",
        "threading",
        "typing",
    ]
)
_IMPORT = builtins.__import__
STAGING_PROFILE = "original-consumer-staging-source-binding-v2"
STAGING_NAMESPACE = "_aware_release_consumer_v2"
STAGING_PINS = types.MappingProxyType(
    {
        "filesystem._native_bootstrap_custody": (
            "e13c7e448092395fc8f933ed128ea1dbf3076d04f97429155d9ceacd2f7e2a1c",
            27410,
        ),
        "filesystem._native_library": (
            "7f0dabba2de22b0855f68325d1853b12e5c5fccf65c2ec7d44560eae0b7542f8",
            2073,
        ),
        "filesystem.confined_entry": (
            "534d3bd65f1eccacb686829dcb0d0d5dab1ad5c555cf9c75bac3f7c66c84f7c3",
            31390,
        ),
        "filesystem.confined_mutation": (
            "ce255c78488abd4e912ef76dcaff02e8439c2f9857ba8ab0e8edfe5d5e7bedfa",
            80791,
        ),
        "filesystem.cooperative_source": (
            "f4cd84b9a74ef97af442564565eb5e955a8769e54c8cd92c7a5fba75045b4e8f",
            24318,
        ),
        "filesystem.native_bootstrap_creation": (
            "933d0a9935f5e96445194ec32d23f4a46adc5a6b0cca1e99f9d9821bc2b01145",
            22344,
        ),
        "filesystem.native_read_cleanup": (
            "8e3baee924383e7555bab7c327938a099397bb37adb77ee3a3811a132a5b8d15",
            13154,
        ),
        "filesystem.private_directory": (
            "3b15b164e0ac3b75c43ac439b253c6a744286c41b80ae38300aa2e707a94a5d0",
            83982,
        ),
        "filesystem.private_namespace": (
            "859ee2353df029d1247dcd84dc7f6aa748478486951590bbc25d83919ccaf939",
            60095,
        ),
        "filesystem.private_namespace_values": (
            "06167767b1ced5d682c44d4c6d21c4ae4c5e846b87b8e1901b35899f8c0e05c1",
            7917,
        ),
        "filesystem.private_sequence_capacity": (
            "e59fee7fab339084c71b5b1f072d82d35df4a23100a2a87aef5472f186f920dd",
            37728,
        ),
        "filesystem.retained_bootstrap": (
            "035650a21555eb5c92a35d680ec209b84316ce66817add6b5c5593d34c33ec66",
            20889,
        ),
        "filesystem.retained_file_sequence": (
            "e933a85ad8a37017b0015ff5b9ac3698011cddb9d70d24c22d36002a9f4e4985",
            55160,
        ),
        "filesystem.retained_mutation": (
            "feafda81873869daf4f29fa508e26ee1a7babb5d9cdcb8b6ecdb497562eae5b9",
            23291,
        ),
        "filesystem.staging_complete": (
            "103e1271a81e0ea3a36840e4c37e38ebfb9db8a6ad41960abc80afbf554424f2",
            23517,
        ),
        "filesystem.staging_member": (
            "75cbf5bc60e73db9edf100ad3cc4483d3c54c0221556227044e43b3cba003615",
            32775,
        ),
        "filesystem.staging_partitioned_plan": (
            "1a9733878bfd39d02b45a3c14ebeeafc78302a3e2650c708e84dd03fefdac292",
            9803,
        ),
        "filesystem.staging_plan": (
            "dbee8bceb87e40400cae4cc8466bee8d14ed0fba75df7075ae64a0d850708954",
            5148,
        ),
        "filesystem.staging_root": (
            "dbc6b2bcdc19db024c075967eaa18a0df76ce91e259f0bf607f9c34eca8326a8",
            16943,
        ),
        "release._product_bulk_consumption": (
            "fb8112173306bde83ea6503627bc92c5c00bcdf5e3b2452b3708b020bf933100",
            5410,
        ),
        "release._product_capture_mount": (
            "6142fef7363afe0970adfc32eb87bf4c35dcd4de9758c2abbe62cc630bc80671",
            9302,
        ),
        "release._product_catalog_flow": (
            "790d8b419201fa9579723aa5efd2c064b2aa27c447f5056e616002f0d8d0ec37",
            13524,
        ),
        "release._product_catalog_receiving": (
            "69d49c3664b3d87e3d4a7c7cb258bdd8004af11cd25bd172737251b8748fa425",
            21408,
        ),
        "release._product_member_capture": (
            "5267122f481995f5fed7a846866a72dc6f34cbb61d9cbecae196faa52c26284f",
            7121,
        ),
        "release._product_member_consumption": (
            "c43f91e09db24a8e173951efe1550ec13411c22b147bd3c1ceab3c631f2bb17a",
            13241,
        ),
        "release._product_member_receiving": (
            "176b50011be23ab1bed6546e9af9f955abb40c8179b35bafd1841a614b125617",
            7104,
        ),
        "release._product_member_replay": (
            "5d19cd678743b32e539989f9a38ed84576b48ccda29777550fdc2aed74135699",
            7226,
        ),
        "release._product_nested_bulk": (
            "3b5fa1a7896816cdb32c97a0c72f8a0dc69d9073933f4911baa852631d33f0e9",
            6843,
        ),
        "release._product_nested_mount": (
            "35a38fe627cc2dfc845c5426a9368234248579ce691dc94ed5939e11adcbaee8",
            15682,
        ),
        "release._product_parent_member_feed": (
            "a41933516086ccb845c286c2d46d8a797c06833d15fbbc5d72dd58c470a609d9",
            12497,
        ),
        "release._product_stream_catalog": (
            "f9f7205c0e7ded5ae6717e3d30e4682328a350062c1186d1af9752e8ae9e1cb7",
            23331,
        ),
        "release._product_stream_flow": (
            "d6af0d78f8214c7d2702ac7a0611ff6a14e477624ea680c0ef6fdf1947399ab9",
            20039,
        ),
        "release._product_stream_receiving": (
            "491f1ea5563e13bc5716e878f514fef41fb070fdeaeb4356f95c430f28a857bb",
            12732,
        ),
        "release._product_tar_policy": (
            "70ca30432e3b214ff9c0321679f480f9d29cd79ac68b72c820d1fc678bca660e",
            6222,
        ),
        "release.product_staging": (
            "2f503fc1ab158bcbc7bd01e502a016387e0b7b803b571ddd9a0a54b89de64a4a",
            14415,
        ),
        "release.whole_envelope": (
            "c5d8d499c18c5fd49110a1247b7f29a2021101bbd7f0b55cfb86e0bbc0ff29da",
            45981,
        ),
    }
)
STAGING_STDLIB = frozenset(
    [
        "__future__",
        "_thread",
        "ast",
        "asyncio",
        "base64",
        "collections",
        "contextlib",
        "ctypes",
        "dataclasses",
        "enum",
        "errno",
        "fcntl",
        "gzip",
        "hashlib",
        "importlib",
        "itertools",
        "json",
        "os",
        "pathlib",
        "platform",
        "re",
        "stat",
        "subprocess",
        "sys",
        "tarfile",
        "threading",
        "types",
        "typing",
        "unicodedata",
        "uuid",
        "weakref",
    ]
)

_RECORDS: dict[object, object] = {}
STAGING_BOUND_PROFILE = "original-consumer-staging-bound-source-binding-v3"
STAGING_BOUND_NAMESPACE = "_aware_release_consumer_v3"
STAGING_BOUND_PINS = types.MappingProxyType(
    {
        **STAGING_PINS,
        "filesystem.staging_root": (
            "e3b74fbaa8cf05b9398db319a6acd25a66189521893a81138df0e7689bed5edc",
            18310,
        ),
    }
)
COMPACT_STAGING_PROFILE = "original-consumer-compact-staging-source-binding-v4"
COMPACT_STAGING_NAMESPACE = "_aware_release_consumer_v4"
COMPACT_STAGING_PINS = types.MappingProxyType(
    {
        **STAGING_BOUND_PINS,
        "filesystem.staging_member": (
            "209fddaf5028682972af7c16bae7c2bc915a1c9b08220aa9c7004b6e31964e40",
            36397,
        ),
        "release.product_staging": (
            "cc494b88e194d5af772f6627b16db3d273a3c3c16cb34906eb3c8a7c2f3740d8",
            15367,
        ),
    }
)

RECORDED_STAGING_PROFILE = "original-consumer-recorded-staging-source-binding-v5"
RECORDED_STAGING_NAMESPACE = "_aware_release_consumer_v5"
RECORDED_STAGING_STDLIB = frozenset((*STAGING_STDLIB, "struct", "math"))
RECORDED_STAGING_PINS = types.MappingProxyType(
    {
        **COMPACT_STAGING_PINS,
        "filesystem._staging_guard_history": (
            "a4da244e15e27b2a8a04d43f2b061a2a3c4b3cedc0a391002feceeaa3f425167",
            12946,
        ),
        "filesystem.staging_root": (
            "63f0e4be34beada15d7ccad86b2c0c2a376a309f3e40b92e71750ac0dda8132f",
            20655,
        ),
        "filesystem.staging_member": (
            "8eef279eb72feddb3a7a63c369e4222c2d093f15936eb1d00ddc8bdb0fee8c4c",
            36733,
        ),
        "filesystem.staging_complete": (
            "1ad81c8d7a87b20d6d28db5263269ffb48c19fc2484247db921f5e122aa58e91",
            23848,
        ),
        "release.product_staging": (
            "c7391708074734eff33216aa536216b5d5111a9f6f4d428a152316cf5cbc8b28",
            15720,
        ),
    }
)

SEALED_STAGING_PROFILE = "original-consumer-sealed-staging-source-binding-v6"
SEALED_STAGING_NAMESPACE = "_aware_release_consumer_v6"
SEALED_STAGING_PINS = types.MappingProxyType(
    {
        **RECORDED_STAGING_PINS,
        "filesystem._staging_guard_history": (
            "1e7235b003af600268685fcb5ddafc2fcc05576b92ff87dc7cc590c64a52fa6a",
            15423,
        ),
        "filesystem.staging_complete": (
            "d5f2e45d6960a1cb704dfce01bc962f51672b21162666c6fab370e3cc0614350",
            24730,
        ),
        "filesystem.confined_entry": (
            "8f84d219cd771e0512e7c3db2332dc184d12950da8a72d9e21d4c8e4757d44d9",
            33976,
        ),
    }
)

PACKED_STAGING_PROFILE = "original-consumer-packed-staging-source-binding-v7"
PACKED_STAGING_NAMESPACE = "_aware_release_consumer_v7"
PACKED_STAGING_PINS = types.MappingProxyType(
    {
        **SEALED_STAGING_PINS,
        "filesystem._staging_guard_history": (
            "dcc5bb5845a926561c242d514e02c177b5b357b6086e18db21910b6f791404d2",
            17289,
        ),
        "filesystem.staging_complete": (
            "b71518ec403b3cc8210495e7f6b03b9c484863eee8d6e284a014c8c7ca340ca2",
            24971,
        ),
        "filesystem.confined_entry": (
            "30068cd89b6d8ade10a5590b76b83bd9cedea72d920fefa5199b88c39966c7d9",
            36224,
        ),
        "release._product_stream_flow": (
            "f681040c3d931d9ebea0b547bc67b72c5f4ca48374c2645645a2f57d4e26fa12",
            27437,
        ),
        "release._product_catalog_flow": (
            "d0be5dd6c63da4ee46673cfa6e1f95025c93a94f14b7da5a98b5d8e73f72f47c",
            13681,
        ),
        "release._product_bulk_consumption": (
            "4331a05254c77fc4ad5a02f3d1d7c3ceaa26fedf61b29f31fa9ba4d278c85a07",
            5509,
        ),
        "release._product_stream_receiving": (
            "0ca1fe0832a74c24a6bd27cccb8300aa763f7b25a04fceda4e3c87c97dafb493",
            12821,
        ),
        "release.product_staging": (
            "7868b4e3f20c3e541e7e191eb8c545ccedca1c227f8c0f429400c866a020d34d",
            15923,
        ),
    }
)


COMPRESSED_STAGING_PROFILE = "original-consumer-compressed-staging-source-binding-v8"
COMPRESSED_STAGING_NAMESPACE = "_aware_release_consumer_v8"
COMPRESSED_STAGING_STDLIB = frozenset((*RECORDED_STAGING_STDLIB, "zlib"))
COMPRESSED_STAGING_PINS = types.MappingProxyType(
    {
        **PACKED_STAGING_PINS,
        "filesystem._staging_guard_history": (
            "54557f8ead2c0646eadee91985caa720d0bae9b510a7fd56aee74bd9bf48a6b0",
            23677,
        ),
        "filesystem.staging_root": (
            "e8e3b513c9f74b170042a77ac14077fd2fe82395f16f6074cc230b41561662a6",
            20787,
        ),
        "filesystem.staging_member": (
            "991d04b563a154837f32ef61279207f28e276e79d18c8a76ecb9632d1ffb2cca",
            37125,
        ),
        "release.product_staging": (
            "8f0a999a87543347e3f8ba5a6e767a8da3816238054eb0f0c33ccb276fc69e5f",
            16327,
        ),
    }
)


BORROWED_STAGING_PROFILE = "original-consumer-borrowed-directory-source-binding-v9"
BORROWED_STAGING_NAMESPACE = "_aware_release_consumer_v9"
BORROWED_STAGING_PINS = types.MappingProxyType(
    {
        **COMPRESSED_STAGING_PINS,
        "filesystem._staging_guard_history": (
            "2fbd583871dda181df19ed57d9f74717a651652be97534991f6dc7152d870786",
            24795,
        ),
        "release._product_bulk_consumption": (
            "d12e45022bd59f162be8753aff97cdf43528f66964609dc3ecea171e31fd2458",
            7692,
        ),
        "filesystem.staging_root": (
            "00b441679ab8d38a3f088909df2d71589982230b7481d875087be869b127b414",
            26235,
        ),
        "filesystem.staging_member": (
            "c66b64b9c8034a26db42cbe277efe8a6d5cf5599e88d5e39ee940f3cb26f179b",
            37731,
        ),
        "release.product_staging": (
            "24a49a2164068bb95e730c7de5701f13dc76ed21d893180c86793d93ecd0988b",
            17065,
        ),
    }
)

RETIRED_STAGING_PROFILE = "original-consumer-retired-member-source-binding-v10"
RETIRED_STAGING_NAMESPACE = "_aware_release_consumer_v10"
RETIRED_STAGING_PINS = types.MappingProxyType(
    {
        **BORROWED_STAGING_PINS,
        "filesystem.confined_entry": (
            "44b09bab48ccb03ab124b7b199972052c0fe617b085d73a98c2971a78c9cc32a",
            36716,
        ),
        "release._product_nested_mount": (
            "1dd493f60de73c0270165681f7a7ee0cb1a6e5af7cb1a79a7448605072dae73a",
            15682,
        ),
        "release._product_capture_mount": (
            "851eddb33d55ee0da617dee59513da930dccdcafd162ceb9a31f09c111d5ef36",
            9302,
        ),
        "release._product_member_replay": (
            "38d5825f641822f62d7faaff00fe04b80595eb64c136585d02f8c22bbeb14983",
            7226,
        ),
        "release._product_catalog_receiving": (
            "7316b50d9d63136294c84c7bd42b5473b3a799324e0e5c4a1e3518e94459551c",
            21408,
        ),
        "release._product_stream_receiving": (
            "7735ebb78a4625dc1f94220904848aff4e71748a26433681f1bcec7119cf06bf",
            12821,
        ),
        "release._product_stream_catalog": (
            "62d2c44b300f1e6f174bbd561cf3118da953bfcf824a084c65b5432a2bb1773f",
            24125,
        ),
        "filesystem._staging_guard_history": (
            "16b27ef854d38d3e5af0996bf51a1ad6c44fed140729a5acaddc3c1bac4b4785",
            27960,
        ),
        "filesystem.staging_root": (
            "b79a6624877ea72ec9845a399d21b5d8965211881b9cf2d3ac6fb2b84ae9bde6",
            26663,
        ),
        "filesystem.staging_member": (
            "73fe36616fc5d0e1c536b21de6600a148450725eb1d5287f593e57b5141d1d2a",
            46152,
        ),
        "filesystem.staging_complete": (
            "505ae3efac588ec764c881c1aa8cc2eb4b80348d560f8da39f95616bdb028027",
            25244,
        ),
        "release.product_staging": (
            "0eb977215c8b87899e5fc56a1340f8e8bca6d8eca0f1dafe4d7873998e46c807",
            18897,
        ),
    }
)

RECEIPT_STAGING_STDLIB = frozenset((*COMPRESSED_STAGING_STDLIB, "array"))
RECEIPT_STAGING_PROFILE = "original-consumer-observation-receipt-source-binding-v11"
RECEIPT_STAGING_NAMESPACE = "_aware_release_consumer_v11"
RECEIPT_STAGING_PINS = types.MappingProxyType(
    {
        **RETIRED_STAGING_PINS,
        "filesystem.cooperative_source": (
            "f4cd84b9a74ef97af442564565eb5e955a8769e54c8cd92c7a5fba75045b4e8f",
            24318,
        ),
        "release._product_stream_catalog": (
            "a289cbf8e1678e9250e839930985e585431195968dea28f670f8f0a02377315c",
            24137,
        ),
        "release._product_tar_policy": (
            "aebfa34de7c14d4bedcb61b198a4460d600f503d4722f241820faacef23c8142",
            6289,
        ),
        "release._product_member_consumption": (
            "3507af069ef47298836a2eeffa68df87d6c0e898eaad1de74adb2e1722e7f3cc",
            13277,
        ),
        "filesystem.confined_mutation": (
            "edd891cdf5141977641c8881e3555c404a0b51ca5809626d3179396612f25569",
            81393,
        ),
        "filesystem._staging_guard_history": (
            "478104bfbdff61ae136ed3f8a4199fe96ea13fd60e73b311262f7880975b7e3d",
            51990,
        ),
        "filesystem.staging_root": (
            "d5a2a1b225392a6c0a0e2cfd648886f1c054d8c52011a3fa8386c958e49f2a32",
            27059,
        ),
        "filesystem.staging_member": (
            "396ba210a064d855043a14e2be55474d7d0e571fb6d6453f73c974593dc17ea6",
            58543,
        ),
        "filesystem._observation_receipt": (
            "be67af7b7d5e559f167ef3ced17103269b2ef4d833fc7714cdf13bc5be93f340",
            18149,
        ),
        "filesystem.confined_entry": (
            "ad7af5afc9d263856593d3622a44252bd98ee94c665d4516a60c03998f6ef407",
            46610,
        ),
        "filesystem.staging_plan": (
            "728264b2d2ac987db8d769ef6fcba336e36fc6a2133455d5416ddab01cbe36ad",
            6365,
        ),
        "filesystem.staging_complete": (
            "f9d47a18eab5b341ab8cf9cc196fd1d978dd826443859905e1b21c0f1efcb057",
            31396,
        ),
        "release.product_staging": (
            "3d328cdf79ca1f97d7d36b14415c43b2cf5738350bbd113ee9ea00b905225162",
            20333,
        ),
    }
)


@dataclass(frozen=True, slots=True, eq=False)
class SourceSelection:
    root: Path
    profile: str = PROFILE
    initial_modules: tuple[str, ...] | None = None


RECEIPT_INITIAL_MODULES = ("release.whole_envelope", "release.product_staging")


class SourceHandle:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original_source_enrollment_required")


@dataclass
class _Binding:
    selection: SourceSelection
    root: Path
    owner: types.ModuleType
    affinity: tuple[int, int]
    owner_binding: tuple
    pins: Mapping
    namespace: str
    stdlib: frozenset
    packages: tuple
    state: str = "capturing"
    reads: list = field(default_factory=list)
    guards: list = field(default_factory=list)
    bodies: dict = field(default_factory=dict)
    modules: dict = field(default_factory=dict)
    executing: set = field(default_factory=set)
    executed: set = field(default_factory=set)
    cleanup: list = field(default_factory=list)
    cleanup_attempted: bool = False
    initial_modules: tuple[str, ...] | None = None


class SourceBindingError(RuntimeError):
    def __init__(self, selection, handle, record, cause):
        super().__init__("original_preinstall_source_binding_failed")
        self.selection, self.handle = selection, handle
        self.original_reads = () if record is None else tuple(record.reads)
        self.original_guards = () if record is None else tuple(record.guards)
        self.enrolled_modules = () if record is None else tuple(record.modules.items())
        self.original_cleanup = () if record is None else tuple(record.cleanup)
        self.original_root = None if record is None else record.root
        self.executing_modules = (
            () if record is None else tuple(sorted(record.executing))
        )
        self.executed_modules = () if record is None else tuple(sorted(record.executed))
        self.state = "not_enrolled" if record is None else record.state
        self.cleanup_attempted = False if record is None else record.cleanup_attempted
        self.primary_cause = cause
        self.authorizes_retry = self.authorizes_installation = False
        self.cleanup = "not_observed"
        self.original_io_cleanup = "not_observed"


def _configuration(profile):
    if type(profile) is str and profile == RECEIPT_STAGING_PROFILE:
        return (
            RECEIPT_STAGING_PINS,
            RECEIPT_STAGING_NAMESPACE,
            RECEIPT_STAGING_STDLIB,
            (
                RECEIPT_STAGING_NAMESPACE,
                "aware_file_system",
                RECEIPT_STAGING_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == RETIRED_STAGING_PROFILE:
        return (
            RETIRED_STAGING_PINS,
            RETIRED_STAGING_NAMESPACE,
            COMPRESSED_STAGING_STDLIB,
            (
                RETIRED_STAGING_NAMESPACE,
                "aware_file_system",
                RETIRED_STAGING_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == BORROWED_STAGING_PROFILE:
        return (
            BORROWED_STAGING_PINS,
            BORROWED_STAGING_NAMESPACE,
            COMPRESSED_STAGING_STDLIB,
            (
                BORROWED_STAGING_NAMESPACE,
                "aware_file_system",
                BORROWED_STAGING_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == COMPRESSED_STAGING_PROFILE:
        return (
            COMPRESSED_STAGING_PINS,
            COMPRESSED_STAGING_NAMESPACE,
            COMPRESSED_STAGING_STDLIB,
            (
                COMPRESSED_STAGING_NAMESPACE,
                "aware_file_system",
                COMPRESSED_STAGING_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == PACKED_STAGING_PROFILE:
        return (
            PACKED_STAGING_PINS,
            PACKED_STAGING_NAMESPACE,
            RECORDED_STAGING_STDLIB,
            (
                PACKED_STAGING_NAMESPACE,
                "aware_file_system",
                PACKED_STAGING_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == SEALED_STAGING_PROFILE:
        return (
            SEALED_STAGING_PINS,
            SEALED_STAGING_NAMESPACE,
            RECORDED_STAGING_STDLIB,
            (
                SEALED_STAGING_NAMESPACE,
                "aware_file_system",
                SEALED_STAGING_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == RECORDED_STAGING_PROFILE:
        return (
            RECORDED_STAGING_PINS,
            RECORDED_STAGING_NAMESPACE,
            RECORDED_STAGING_STDLIB,
            (
                RECORDED_STAGING_NAMESPACE,
                "aware_file_system",
                RECORDED_STAGING_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == PROFILE:
        return PINS, NAMESPACE, STDLIB, (NAMESPACE,)
    if type(profile) is str and profile == STAGING_PROFILE:
        return (
            STAGING_PINS,
            STAGING_NAMESPACE,
            STAGING_STDLIB,
            (
                STAGING_NAMESPACE,
                "aware_file_system",
                STAGING_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == STAGING_BOUND_PROFILE:
        return (
            STAGING_BOUND_PINS,
            STAGING_BOUND_NAMESPACE,
            STAGING_STDLIB,
            (
                STAGING_BOUND_NAMESPACE,
                "aware_file_system",
                STAGING_BOUND_NAMESPACE + ".release",
            ),
        )
    if type(profile) is str and profile == COMPACT_STAGING_PROFILE:
        return (
            COMPACT_STAGING_PINS,
            COMPACT_STAGING_NAMESPACE,
            STAGING_STDLIB,
            (
                COMPACT_STAGING_NAMESPACE,
                "aware_file_system",
                COMPACT_STAGING_NAMESPACE + ".release",
            ),
        )
    raise ValueError("explicit_original_source_selection_required")


def _source_path(record, short):
    return record.root / (short.replace(".", "/") + ".py")


def _available(packages):
    if any(
        name == package or name.startswith(package + ".")
        for name in sys.modules
        for package in packages
    ):
        raise ValueError("source_namespace_already_present")


def _module_name(record, short):
    if record.namespace in (
        STAGING_NAMESPACE,
        STAGING_BOUND_NAMESPACE,
        COMPACT_STAGING_NAMESPACE,
        RECORDED_STAGING_NAMESPACE,
        SEALED_STAGING_NAMESPACE,
        PACKED_STAGING_NAMESPACE,
        COMPRESSED_STAGING_NAMESPACE,
        BORROWED_STAGING_NAMESPACE,
        RETIRED_STAGING_NAMESPACE,
        RECEIPT_STAGING_NAMESPACE,
    ) and short.startswith("filesystem."):
        return "aware_file_system." + short.split(".", 1)[1]
    return record.namespace + "." + short


def _current(record):
    pins, namespace, stdlib, packages = _configuration(record.selection.profile)
    if (
        record.affinity != (os.getpid(), threading.get_ident())
        or record.selection.root is not record.root
        or record.selection.initial_modules is not record.initial_modules
        or record.cleanup_attempted
        or pins is not record.pins
        or namespace != record.namespace
        or stdlib is not record.stdlib
        or packages != record.packages
        or any(
            getattr(record.owner, name, None) is not value
            for name, value in record.owner_binding
        )
    ):
        raise ValueError("original_source_binding_changed_or_spent")


def _record(handle):
    if type(handle) is not SourceHandle or handle not in _RECORDS:
        raise ValueError("original_source_handle_required")
    record = _RECORDS[handle]
    assert isinstance(record, _Binding)
    _current(record)
    return record


def _enrolled(record):
    for name, module in record.modules.items():
        if sys.modules.get(name) is not module:
            raise ValueError("original_source_module_substituted")
        if "." in name:
            parent, _, short = name.rpartition(".")
            if getattr(record.modules[parent], short, None) is not module:
                raise ValueError("original_source_package_binding_substituted")
        package = name if name in record.packages else name.rpartition(".")[0]
        if module.__name__ != name or module.__package__ != package:
            raise ValueError("original_source_module_coordinates_changed")
        if name in record.packages and (
            type(module.__path__) is not list or module.__path__ != []
        ):
            raise ValueError("original_source_package_path_changed")


def _load(record, short):
    _current(record)
    if short not in record.pins:
        raise ImportError("source_not_in_original_closure")
    full = _module_name(record, short)
    if full in record.modules:
        _enrolled(record)
        return record.modules[full]
    if full in sys.modules:
        raise ValueError("foreign_source_module_present")
    module = types.ModuleType(full)
    module.__file__ = str(_source_path(record, short))
    parent, _, leaf = full.rpartition(".")
    module.__package__ = parent
    module.__dict__["__builtins__"] = dict(
        vars(builtins),
        __import__=lambda name, globals=None, locals=None, fromlist=(), level=0: (
            _import(record, name, globals, locals, fromlist, level)
        ),
    )
    # Custody is retained before executing any original definition.
    record.modules[full] = module
    sys.modules[full] = module
    setattr(record.modules[parent], leaf, module)
    record.executing.add(short)
    exec(compile(record.bodies[short], module.__file__, "exec"), module.__dict__)  # noqa: S102 -- exact original captured source only
    record.executing.remove(short)
    record.executed.add(short)
    _enrolled(record)
    return module


def _import(record, name, globals, locals, fromlist, level):
    _current(record)
    _enrolled(record)
    if level:
        if (
            level != 1
            or globals is None
            or globals.get("__package__") not in record.packages
        ):
            raise ImportError("original_relative_source_import_required")
        package = globals["__package__"]
        prefix = (
            "filesystem"
            if package == "aware_file_system"
            else package[len(record.namespace) + 1 :]
        )
        prefix = prefix + "." if prefix else ""
        if name:
            return _load(record, prefix + name)
        for short in fromlist:
            _load(record, prefix + short)
        return record.modules[package]
    if (
        record.namespace
        in (
            STAGING_NAMESPACE,
            STAGING_BOUND_NAMESPACE,
            COMPACT_STAGING_NAMESPACE,
            RECORDED_STAGING_NAMESPACE,
            SEALED_STAGING_NAMESPACE,
            PACKED_STAGING_NAMESPACE,
            COMPRESSED_STAGING_NAMESPACE,
            BORROWED_STAGING_NAMESPACE,
            RETIRED_STAGING_NAMESPACE,
            RECEIPT_STAGING_NAMESPACE,
        )
        and name == "aware_file_system"
    ):
        for short in fromlist:
            _load(record, "filesystem." + short)
        return record.modules["aware_file_system"]
    if name.split(".")[0] not in record.stdlib:
        raise ImportError("original_source_external_import_refused")
    return _IMPORT(name, globals, locals, fromlist, level)


def bind_original_sources(
    selection: SourceSelection, *, original_owner: types.ModuleType
):
    """Read via the original bounded observer; execute only captured pinned bytes.

    Errors retain partial enrollment for explicit retirement. No automatic
    removal, source reread retry, owner dispatch or filesystem mutation.
    """
    record = handle = None
    try:
        if type(selection) is not SourceSelection:
            raise ValueError("explicit_original_source_selection_required")
        pins, namespace, stdlib, packages = _configuration(selection.profile)
        root = selection.root
        if (
            type(root) is not type(Path())
            or not root.is_absolute()
            or ".." in root.parts
        ):
            raise ValueError("explicit_original_source_root_required")
        if selection.initial_modules is not None and (
            selection.profile != RECEIPT_STAGING_PROFILE
            or type(selection.initial_modules) is not tuple
            or any(type(name) is not str for name in selection.initial_modules)
            or selection.initial_modules != RECEIPT_INITIAL_MODULES
        ):
            raise ValueError("explicit_original_staging_entrypoints_required")
        if type(original_owner) is not types.ModuleType:
            raise TypeError("qualified_original_source_observer_required")
        if _RECORDS:
            raise ValueError("original_source_binding_attempt_spent")
        _available(packages)
        handle = object.__new__(SourceHandle)
        record = _Binding(
            selection,
            root,
            original_owner,
            (os.getpid(), threading.get_ident()),
            tuple(
                (name, getattr(original_owner, name))
                for name in (
                    "ArchiveBodyRequest",
                    "ArchiveBodyObservation",
                    "observe_archive_body",
                    "_file",
                )
            ),
            pins,
            namespace,
            stdlib,
            packages,
            initial_modules=selection.initial_modules,
        )
        _RECORDS[handle] = record
        for short, (digest, size) in record.pins.items():
            _current(record)
            request = original_owner.ArchiveBodyRequest(
                _source_path(record, short), digest, size
            )
            returned = original_owner.observe_archive_body(request)
            record.reads.append(returned)
            _current(record)
            if (
                type(returned) is not original_owner.ArchiveBodyObservation
                or returned.request is not request
                or returned.request_snapshot != (request.path, digest, size)
                or type(returned.body) is not bytes
                or len(returned.body) != size
                or hashlib.sha256(returned.body).hexdigest() != digest
            ):
                raise ValueError("original_source_read_correlation_required")
            record.bodies[short] = returned.body
        record.state = "captured"
        # Original observer callbacks may have introduced foreign modules.
        # Refuse before enrollment;never overwrite them as captured custody.
        _available(record.packages)
        for name in record.packages:
            package = types.ModuleType(name)
            package.__package__ = name
            package.__path__ = []  # No PathFinder, source/pyc read or broad initializer.
            record.modules[name] = package
            sys.modules[name] = package
            if "." in name:
                parent, _, leaf = name.rpartition(".")
                setattr(record.modules[parent], leaf, package)
        record.state = "executing"
        # Capture and final guards still cover every carried source. Explicit
        # entrypoints avoid executing unused optional branches at startup; the
        # same original import hook loads authenticated dependencies as needed.
        for short in (
            record.pins if record.initial_modules is None else record.initial_modules
        ):
            _load(record, short)
        owner_short = (
            "whole_envelope" if namespace == NAMESPACE else "release.whole_envelope"
        )
        guarded_owner = record.modules[namespace + "." + owner_short]
        for index, (short, (digest, size)) in enumerate(record.pins.items()):
            _current(record)
            returned = guarded_owner._file(_source_path(record, short), digest, size)
            record.guards.append(returned)
            _current(record)
            original = record.reads[index]
            if returned != original.original_file:
                raise ValueError("original_source_identity_changed")
        _enrolled(record)
        _current(record)
        record.state = "bound"
        return handle
    except (
        BaseException
    ) as cause:  # Retain interruptions/partial enrollment without retry.
        if record is not None:
            record.state = "failed"
        raise SourceBindingError(selection, handle, record, cause) from cause


def bound_module(handle, short):
    """Return the same original module, without fresh IO or new authority."""
    try:
        record = _record(handle)
        _enrolled(record)
        if record.state != "bound" or short not in record.executed:
            raise ValueError("completed_original_source_binding_required")
        return record.modules[_module_name(record, short)]
    except (
        BaseException
    ) as cause:  # Typed original failure, including malformed handles.
        record = _RECORDS.get(handle) if type(handle) is SourceHandle else None
        raise SourceBindingError(None, handle, record, cause) from cause


def _remove_module(name, module):
    if sys.modules.get(name) is not module:
        raise ValueError("original_source_cleanup_binding_changed")
    del sys.modules[name]


def retire_source_binding(handle):
    """Explicit once-only Python module unenrollment; not source IO disposal.

    Refuse foreign replacements without removing them. Interrupted removal is
    spent/unknown and cannot be retried. Existing original IO returns survive.
    """
    record = None
    try:
        record = _record(handle)
        _enrolled(record)
        record.cleanup_attempted = True
        record.state = "retiring"
        for name, module in reversed(tuple(record.modules.items())):
            returned = _remove_module(name, module)
            record.cleanup.append((name, returned))
        record.state = "retired"
    except BaseException as cause:  # Never repeat removal after uncertainty.
        if record is not None and record.cleanup_attempted:
            record.state = "retirement_unknown"
        raise SourceBindingError(None, handle, record, cause) from cause
