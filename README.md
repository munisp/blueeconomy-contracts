# Blue Economy Platform Contracts

This repository is the authoritative source for versioned API, event, identity-claim and data-product contracts used by Blue Economy Platform deployables. It contains contracts only; it does not contain endpoint configuration, credentials, production data or partner secrets.

## Contract status

The initial contracts define internal event envelopes and the first-release maritime evidence and waterway-safety event boundaries. They are syntactically validated as Protocol Buffers descriptors. They do **not** claim conformance with an external Ministry or partner API until its authoritative interface and a successful non-production test are recorded under the integration-gate policy.

## Validation

```bash
./scripts/validate-contracts.sh
```

Breaking changes require a documented migration decision, consumer inventory and compatibility window before merge.
