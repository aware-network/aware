# File System API Migration

Migration tracker for removing the file system API from the Interface API package.

**Canonical Target**
- The API package does not own local file system indexing/watching.
- File-system tooling lives in `libs/file_system/dart` as a standalone package.
- DTO-only client remains free of local storage concerns.

**Source Inventory (Legacy)**
- `libs/file_system/dart/lib/file_system/**` (moved)
- `OLD/aware_interface_api_dart/database_helper.dart` (moved to OLD)
- Providers/usage tied to repository/domain services.

**Canonical Gaps (Must Remove/Replace)**
- File system watchers and index caches are non-canonical (local SSOT).
- Local SQLite helpers duplicate app responsibilities.

**Phase Plan**
- [x] Move file system APIs to `libs/file_system/dart`.
- [x] Move database helper to `OLD/aware_interface_api_dart/`.
- [ ] Drop interface_api dependencies (`sqflite`, `path_provider`, etc.) once no longer used.

**Dependencies / Open Questions**
- Confirm whether app-specific providers should be lifted into a separate app package.
