"""Dependency-free full Code module manifest meaning and retained-bytes parser."""

from .codec import (
    CONTRACT,
    ModuleManifestMeaningError,
    decode_module_manifest_meaning,
    encode_module_manifest_meaning,
)
from .models import (
    AwareModulePackageSemanticContractBindingSpec,
    AwareModulePackageSemanticContractSpec,
    AwareModulePackageSpec,
    AwareModulePluginCapabilityPolicySpec,
    AwareModulePluginSpec,
    AwareModuleRuntimeSpec,
    AwareModuleServiceSpec,
    AwareModuleSpec,
)
from .parser import AwareModuleTomlError, parse_module_manifest

__all__ = ['CONTRACT', 'AwareModulePackageSemanticContractBindingSpec', 'AwareModulePackageSemanticContractSpec', 'AwareModulePackageSpec', 'AwareModulePluginCapabilityPolicySpec', 'AwareModulePluginSpec', 'AwareModuleRuntimeSpec', 'AwareModuleServiceSpec', 'AwareModuleSpec', 'AwareModuleTomlError', 'ModuleManifestMeaningError', 'decode_module_manifest_meaning', 'encode_module_manifest_meaning', 'parse_module_manifest']

from .v2_codec import (
    CONTRACT_V2,
    decode_module_manifest_meaning_v2,
    encode_module_manifest_meaning_v2,
)
from .v2_models import (
    AwareModuleSpecV2,
    DeclarationTable,
    DeclarationTag,
    PackageDeclarationV2,
    PackageOccurrenceDeclaration,
)

__all__ += ["CONTRACT_V2", "AwareModuleSpecV2", "DeclarationTable", "DeclarationTag", "PackageDeclarationV2", "PackageOccurrenceDeclaration", "decode_module_manifest_meaning_v2", "encode_module_manifest_meaning_v2"]

from .v3_codec import (
    CONTRACT_V3,
    decode_module_manifest_meaning_v3,
    encode_module_manifest_meaning_v3,
)
from .v3_models import AwareModuleSpecV3

__all__ += ["CONTRACT_V3", "AwareModuleSpecV3", "decode_module_manifest_meaning_v3", "encode_module_manifest_meaning_v3"]
