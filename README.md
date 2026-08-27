# Blue Economy Platform Contracts

This repository is the authoritative source for versioned API, event, identity-claim and data-product contracts used by Blue Economy Platform deployables. It contains contracts only; it does not contain endpoint configuration, credentials, production data or partner secrets.

## Contract status

The contracts define the platform event envelope, the FHIR-aligned domain contracts for the three integration workstreams, and the maritime evidence and waterway-safety event boundaries. They are syntactically validated as Protocol Buffers descriptors and linted with Buf `STANDARD` rules. They do **not** claim conformance with an external Ministry or partner API until its authoritative interface and a successful non-production test are recorded under the integration-gate policy.

## Layout

All contracts live under `proto/blueeconomy/contracts/v1/` in the `blueeconomy.contracts.v1` package.

| File | Purpose |
| --- | --- |
| `envelope.proto` | `EventEnvelope`: the integration backbone carried on every Kafka topic (`ports.*`, `ferries.*`, `cvff.*`). |
| `ecallup.proto` | Workstream A: e-Call-Up truck booking, slot, payment and gate events. |
| `manifest.proto` | Workstream B: ferry passenger manifest, ticketing, telemetry-reference and weather-alert events. |
| `cvff.proto` | Workstream C: CVFF loan, underwriting, four-party approval, disbursement and ledger-commit events. |
| `common.proto` | Shared metadata, classification, severity/validation enums and integer `Money`. |
| `audit.proto` | Immutable security/audit event boundary. |
| `evidence.proto`, `safety.proto`, `mobile_observation.proto` | Evidence, waterway-safety and field-observation event boundaries. |

## The event envelope

Every message published to a platform topic is an `EventEnvelope`:

- `envelope_version` (semantic version of the envelope contract), `event_id`, `event_type` (dotted, e.g. `ports.ecallup.truck_booking.created.v1`), `occurred_at`, `producer`, `correlation_id`.
- `bundle`: a pragmatic FHIR R4-aligned **message Bundle** (`resource_type` fixed to `"Bundle"`, `type` fixed to `BUNDLE_TYPE_MESSAGE`, `entry[]` of resources). The first entry is the primary event resource named by `event_type`; later entries are supporting resources cross-referenced by `full_url`.
- `entry.resource` is modelled as `google.protobuf.Any`. This keeps the resource type explicit in the `type_url` (e.g. `type.googleapis.com/blueeconomy.contracts.v1.TruckBookingCreated`), preserves schema governance and typed code generation, and lets consumers fail closed on unrecognised types. `google.protobuf.Struct` was deliberately rejected because it would bypass schema governance.
- `provenance`: `principal_id` (Keycloak `sub`, never a username or token), `principal_role`, a detached `signature` over the canonical envelope, and the `ledger_commit_hash` anchoring the event.
- `classification`: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL` or `FIDUCIARY_SEGREGATED` (CVFF flows are always `FIDUCIARY_SEGREGATED`).

Consumers must validate `envelope_version`, bundle type, classification and signature **before** unpacking entry resources, and must fail closed on any violation.

## Domain contracts

Domain messages are *resources*, not standalone envelopes: they are transported as the primary resource of an envelope bundle and therefore do not duplicate envelope metadata.

- **Workstream A (`ecallup.proto`, `ports.*`)** — per-truck flow: `TruckBookingCreated` → `PaymentIntentUpdated` → `SlotReservationUpdated` → `GateScanRecorded` (gate approval), with audit anchoring via envelope provenance. Trucks, operators and payers are tokenized references; plates, documents and instruments stay inside the producing boundary.
- **Workstream B (`manifest.proto`, `ferries.*`)** — `PassengerManifestSubmitted` models the manifest as a FHIR-aligned Composition/List: `manifest_bundle` entries are `AnonymizedPassengerEntry` resources carrying only salted digests; `passenger_count` must equal the entry count. Plus `TicketIssued`, `VesselTelemetryRef` and `AdverseWeatherAlert`. No passenger PII ever appears on the bus.
- **Workstream C (`cvff.proto`, `cvff.*`)** — fiduciary flow: `LoanApplicationSubmitted` → `UnderwritingDecisionRecorded` (PLI tier `PRIMARY_50`/`SECONDARY_35`/`TERTIARY_15`) → `FourPartyApprovalRecorded` (NIMASA approver → PLI tiers → receiving bank → beneficiary; disbursement is prohibited until `COMPLETED`) → `DisbursementRecorded` (NGN integer amount paired with the CBN fx-adjusted USD cost entry) → `AuditCommitRecorded` (hash-chained ledger anchor matching `provenance.ledger_commit_hash`).

## Data minimization and fail-closed rules

- Events carry immutable identifiers, correlation identifiers, tokenized references, digests, classification and timestamps. Raw documents, credentials, personal records, bank account details, payment instruments and sensitive precise locations are prohibited in events.
- Status, severity, classification, decision and currency fields are enums, never free strings; the `*_UNSPECIFIED` zero value is invalid on the wire and consumers must fail closed on it. Legacy free-text `severity`/`validation_status` fields in `evidence.proto`, `safety.proto` and `mobile_observation.proto` are deprecated in favour of the shared `Severity`/`ValidationStatus` enums.
- Money is integer minor units (`Money.amount_minor`) with an enum currency; floating-point money and floating-point fx rates are prohibited.

## Versioning policy

- All v1 contracts are additive-only within the package: new messages, new fields and new enum values may be added; existing field numbers, names and types must not change. `buf breaking` (FILE ruleset) against `main` must pass on every pull request.
- Breaking changes require a new package version (`v2`), a documented migration decision, a consumer inventory and a compatibility window before merge, per `docs/contract-lifecycle.md` and the strict review policy.
- `envelope_version` on the wire tracks the envelope contract version; consumers must reject unsupported major versions.

## Consuming the contracts

There is no published generated-code module yet; generate from source pinned to a git tag or commit:

```bash
buf generate --template '{"version":"v2","plugins":[{"local":"protoc-gen-go","out":"gen/go"}]}' \
  git+https://github.com/munisp/blueeconomy-contracts.git#tag=<release-tag>
```

or clone and run `protoc`/your language plugin against `proto/` with the protobuf well-known types on the include path. Pin to an immutable ref; do not track a moving branch.

## Validation

```bash
./scripts/validate-contracts.sh   # protoc descriptor build
buf lint                          # STANDARD ruleset
buf format --diff --exit-code     # canonical formatting
buf breaking --against ".git#branch=main"   # FILE compatibility ruleset
```

Breaking changes require a documented migration decision, consumer inventory and compatibility window before merge.
