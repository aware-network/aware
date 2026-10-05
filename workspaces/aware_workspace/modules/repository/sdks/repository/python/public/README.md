# Neutral repository preparation SDK

Operation: `repository_sdk.prepare_repository`, version `0.1.0a1`.
Request/result and provider contract are authored public neutral code, not
generated API/ontology objects. The SDK delegates; the selected filesystem
provider owns preparation. It does not own Issue transitions or Git publication.

The preparation request selects an absolute exact root and explicit creation
intent. `head = null` means an unborn branch, not a fake baseline. The CLI
composes preparation and versioned Protocol setup; retained partial state is not
claimed atomic. A service binding is unavailable, not an implicit fallback.
