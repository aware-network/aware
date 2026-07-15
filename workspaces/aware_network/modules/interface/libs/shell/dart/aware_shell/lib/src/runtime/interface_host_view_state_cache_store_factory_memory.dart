import 'interface_host_view_state_cache.dart';

InterfaceHostViewStateCacheStore buildPlatformInterfaceHostViewStateCacheStore(
  InterfaceHostViewStateCacheStoreConfig config,
) {
  return MemoryInterfaceHostViewStateCacheStore();
}
