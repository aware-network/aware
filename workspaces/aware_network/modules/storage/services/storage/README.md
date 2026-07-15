# Aware Storage Service

Canonical Storage service package over the generated `storage-service-api`
protocol.

Storage owns media resolution. Renderers and Interface SDKs should ask Storage
for `StorageMediaResolution` descriptors, then fetch bytes through a
Storage-owned data-plane transport. Node HTTP file operations remain a
compatibility mount point, but the implementation lives in this service package.
