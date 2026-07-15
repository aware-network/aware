import 'interface_host_view_state_cache.dart';
import 'interface_host_view_state_cache_store_factory_memory.dart'
    if (dart.library.io) 'interface_host_view_state_cache_store_factory_io.dart'
    as platform;

InterfaceHostViewStateCacheStore buildInterfaceHostViewStateCacheStore(
  InterfaceHostViewStateCacheStoreConfig config,
) {
  return platform.buildPlatformInterfaceHostViewStateCacheStore(config);
}
