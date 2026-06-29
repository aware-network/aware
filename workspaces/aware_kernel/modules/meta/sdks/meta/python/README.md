# Meta SDK

Consumer facade over the generated Meta service API.

`aware_meta_sdk` is the canonical boundary for module proofs, kernel tests, and
other consumers that need Meta graph authority without importing Meta runtime
implementation packages directly.

The service authority split is:

```text
consumer -> aware_meta_sdk -> aware_meta_service_api -> services/meta -> aware_meta.runtime
```

The SDK must not import `aware_meta.runtime`, generated Meta handler modules,
`aware_runtime`, or `services.meta`.
