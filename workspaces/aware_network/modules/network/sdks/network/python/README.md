# Aware Network SDK

Handwritten Network SDK facade over the generated Network Service API client.

The SDK is the caller boundary for topology, peer, hosted-service, and route
resolution consumers. It may keep process-local cache for ergonomics, but
Network Service remains the authority for remote truth.

