import 'interface_host_view_state_cache.dart';
import 'interface_host_view_state_sqlite_cache.dart';

InterfaceHostViewStateCacheStore buildPlatformInterfaceHostViewStateCacheStore(
  InterfaceHostViewStateCacheStoreConfig config,
) {
  return switch (config.storeKind) {
    InterfaceHostViewStateCacheStoreKind.memory =>
      MemoryInterfaceHostViewStateCacheStore(),
    InterfaceHostViewStateCacheStoreKind.sqlite =>
      SqliteInterfaceHostViewStateCacheStore(
        databasePath: config.databasePath!,
      ),
  };
}
