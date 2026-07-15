# Aware Content Service

Canonical Content service package over the generated `content-service-api`
protocol.

Content owns read/render of `aware_content.Content` into text parts and a
flattened text payload. Social, connector providers, and workspace consumers
should consume this service/API/SDK rail instead of reading Content ontology
internals directly.
