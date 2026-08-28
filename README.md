# Blue Economy Platform Contracts

This repository is the authoritative source for versioned API, event, identity-claim and data-product contracts used by Blue Economy Platform deployables. It contains contracts only; it does not contain endpoint configuration, credentials, production data or partner secrets.

## Contract status

The contracts define the platform event envelope, the FHIR-aligned domain contracts for the six integration workstreams, and the maritime evidence and waterway-safety event boundaries. They are syntactically validated as Protocol Buffers descriptors and linted with Buf `STANDARD` rules. They do **not** claim conformance with an external Ministry or partner API until its authoritative interface and a successful non-production test are recorded under the integration-gate policy.

## Layout

All contracts live under `proto/blueeconomy/contracts/v1/` in the `blueeconomy.contracts.v1` package.

| File | Purpose |
| --- | --- |
| `envelope.proto` | `EventEnvelope`: the integration backbone carried on every Kafka topic (`ports.*`, `ferries.*`, `cvff.*`, `seafarer.*`, `fisheries.*`, `coldchain.*`, `export.*`, `maritime.*`). |
| `ecallup.proto` | Workstream A: e-Call-Up truck booking, slot, payment and gate events. |
| `manifest.proto` | Workstream B: ferry passenger manifest, ticketing, telemetry-reference and weather-alert events. |
| `cvff.proto` | Workstream C: CVFF loan, underwriting, four-party approval, disbursement and ledger-commit events. |
| `seafarer.proto` | Workstream D: seafarer credential issue/verification/revocation (W3C VC 2.0 digest + status-list references) and training progression events. |
| `fisheries.proto` | Workstream E: catch records, cold-chain breach alerts, custody handoffs, export consignment bundling and fraud flags. |
| `isr.proto` | Workstream F: ISR event admission, track anomaly detection, response transitions and outcome-ledger anchoring. |
| `common.proto` | Shared metadata, classification, severity/validation enums and integer `Money`. |
| `audit.proto` | Immutable security/audit event boundary. |
| `evidence.proto`, `safety.proto`, `mobile_observation.proto` | Evidence, waterway-safety and field-observation event boundaries. |

## The event envelope

Every message published to a platform topic is an `EventEnvelope`:

- `envelope_version` (the only supported value is `"1.0"`), `event_id`, `event_type` (dotted, e.g. `ports.ecallup.truck_booking.created.v1`), `occurred_at`, `producer`, `correlation_id`.
- `fhir`: a pragmatic FHIR R4-aligned **message Bundle** (`resource_type` fixed to `"Bundle"`, `type` fixed to `BUNDLE_TYPE_MESSAGE`, `entry[]` of resources) carried under the canonical `fhir` wire key (the legacy `bundle` key is retired). The first entry is the primary event resource named by `event_type`; later entries are supporting resources cross-referenced by `full_url`.
- `entry.resource` is modelled as `google.protobuf.Any`. This keeps the resource type explicit in the `type_url` (e.g. `type.googleapis.com/blueeconomy.contracts.v1.TruckBookingCreated`), preserves schema governance and typed code generation, and lets consumers fail closed on unrecognised types. `google.protobuf.Struct` was deliberately rejected because it would bypass schema governance.
- `provenance`: `principal_id` (Keycloak `sub`, never a username or token), `principal_role`, the fleet `signature`, and the `ledger_commit_hash` anchoring the event.
- `classification`: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED` or `FIDUCIARY_SEGREGATED` (CVFF flows are always `FIDUCIARY_SEGREGATED`).
- `record_classification`: optional per-record clearance label (`UNCLASSIFIED`, `RESTRICTED`, `CONFIDENTIAL`, `SECRET`) persisted by classified-scope consumers for row-level filtering; mandatory for classified scopes.

### Provenance signature (fleet scheme)

`provenance.signature` is a **JWS compact serialization (EdDSA/Ed25519)** over the **JCS-canonicalized (RFC 8785) JSON of the full envelope excluding the signature field**, with protected header `{"alg":"EdDSA","kid":"<producer>-<epoch>"}`. Consumers resolve keys from a mounted public-key directory (`{kid: base64url-ed25519-pubkey}`, path from `KEY_DIRECTORY_PATH`), load it fail-closed at startup, and reject envelopes with an unknown `kid`, malformed compact serialization, payload mismatch, or invalid signature — rejected envelopes are never persisted. The normative specification is [`docs/envelope-signature.md`](docs/envelope-signature.md).

Consumers must validate `envelope_version`, bundle type, classification and signature **before** unpacking entry resources, and must fail closed on any violation.

## Domain contracts

Domain messages are *resources*, not standalone envelopes: they are transported as the primary resource of an envelope bundle and therefore do not duplicate envelope metadata.

- **Workstream A (`ecallup.proto`, `ports.*`)** — per-truck flow: `TruckBookingCreated` → `PaymentIntentUpdated` → `SlotReservationUpdated` → `GateScanRecorded` (gate approval), with audit anchoring via envelope provenance. Trucks, operators and payers are tokenized references; plates, documents and instruments stay inside the producing boundary.
- **Workstream B (`manifest.proto`, `ferries.*`)** — `PassengerManifestSubmitted` models the manifest as a FHIR-aligned Composition/List: `manifest_bundle` entries are `AnonymizedPassengerEntry` resources carrying only salted digests; `passenger_count` must equal the entry count. Plus `TicketIssued`, `VesselTelemetryRef` and `AdverseWeatherAlert`. No passenger PII ever appears on the bus.
- **Workstream C (`cvff.proto`, `cvff.*`)** — fiduciary flow: `LoanApplicationSubmitted` → `UnderwritingDecisionRecorded` (PLI tier `PRIMARY_50`/`SECONDARY_35`/`TERTIARY_15`) → `FourPartyApprovalRecorded` (NIMASA approver → PLI tiers → receiving bank → beneficiary; disbursement is prohibited until `COMPLETED`) → `DisbursementRecorded` (NGN integer amount paired with the CBN fx-adjusted USD cost entry) → `AuditCommitRecorded` (hash-chained ledger anchor matching `provenance.ledger_commit_hash`).
- **Workstream D (`seafarer.proto`, `seafarer.credential.v1`, `seafarer.revocation.v1`)** — `CredentialIssued` references W3C VC 2.0 credentials by digest plus status-list reference only (the VC payload never crosses the bus); `CredentialVerificationRequested`/`CredentialVerificationCompleted` carry an enum verifier role (`EMPLOYER`/`PORT_STATE_CONTROL`) and a fail-closed `VerificationResult`; `CredentialRevoked` carries an enum reason; `TrainingProgression` carries the enum stage (`EXAM_REGISTRATION`/`EXAM_RESULT`/`TRAINING_COMPLETION`/`CREDENTIAL_ELIGIBILITY`). Envelopes are classified `CONFIDENTIAL`.
- **Workstream E (`fisheries.proto`, `fisheries.catch.v1`, `coldchain.telemetry.v1`, `export.consignment.v1`)** — `CatchRecorded` (enum `SpeciesCode` with `OTHER` escape, integer weight kg, fixed-point micro-degree coordinates, tokenized vessel/operator references) → `ColdChainBreachAlerted` (integer milli-degree threshold/observed, duration) → `CustodyHandoffCompleted` (enum stage `CATCH`/`LANDING`/`COLDCHAIN_TRANSIT`/`PROCESSOR`/`EXPORTER`/`IMPORT_RECEIPT`) → `ExportConsignmentBundled` (Merkle bundle root + custody hash-chain tip) → `FraudFlagRaised` (enum rule `CAPACITY_EXCEEDED`/`SPECIES_MIX_ANOMALY`/`IMPOSSIBLE_SPEED`).
- **Workstream F (`isr.proto`, `maritime.isr.v1`, `maritime.behaviour.v1`, `maritime.outcome.v1`)** — `IsrEventAdmitted` (enum modality `AIS`/`SAR`/`RF`/`ACOUSTIC`/`OPTICAL`, payload digest only) → `TrackAnomalyDetected` (enum rule `DARK_VESSEL`/`SPEED_OUTLIER`/`RENDEZVOUS`/`LOITERING_RESTRICTED_ZONE`, track + correlation references) → `IsrResponseTransitioned` (enum stage `ALERT`/`CLASSIFICATION`/`DISPATCH`/`INTERDICTION`/`OUTCOME_CAPTURE`) → `OutcomeLedgerPosted` (incident reference + premium-delta evidence digest, hash-chained). ISR content carries its own fail-closed `SecurityClassification`, distinct from envelope classification.

## Data minimization and fail-closed rules

- Events carry immutable identifiers, correlation identifiers, tokenized references, digests, classification and timestamps. Raw documents, credentials, personal records, bank account details, payment instruments and sensitive precise locations are prohibited in events.
- Status, severity, classification, decision and currency fields are enums, never free strings; the `*_UNSPECIFIED` zero value is invalid on the wire and consumers must fail closed on it. Legacy free-text `severity`/`validation_status` fields in `evidence.proto`, `safety.proto` and `mobile_observation.proto` are deprecated in favour of the shared `Severity`/`ValidationStatus` enums.
- Money is integer minor units (`Money.amount_minor`) with an enum currency; floating-point money and floating-point fx rates are prohibited.

## Versioning policy

- All v1 contracts are additive-only within the package: new messages, new fields and new enum values may be added; existing field numbers, names and types must not change. `buf breaking` (FILE ruleset) against `main` must pass on every pull request.
- Breaking changes require a new package version (`v2`), a documented migration decision, a consumer inventory and a compatibility window before merge, per `docs/contract-lifecycle.md` and the strict review policy.
- `envelope_version` on the wire tracks the envelope contract version; consumers must reject unsupported major versions.

### Tagging and release policy

- Contract releases are tagged `v<MAJOR>.<MINOR>.<PATCH>` (for example `v1.2.3`) from `main`. Within v1 only additive changes may ship: bump PATCH for clarifications and comment changes, MINOR for new messages, fields or enum values. MAJOR is never bumped inside the v1 package; breaking changes require a new `v2` package per the policy above.
- Each `v*` tag triggers the Contract Release workflow, which verifies `buf breaking` (FILE ruleset) against the previous `v*` tag (fail-closed), verifies the committed generated code is reproducible, builds the generated Go module, and publishes a GitHub release with the descriptor set attached. Releases are immutable: the workflow refuses to recreate an existing release.
- Go module tags `gen/go/v<same-version>` are created at the same commit so consumers can `go get` the generated module by version. These aliases carry no independent contract meaning; compatibility is governed by the `v*` contract tags only.

## Consuming the contracts

### Go (generated module, committed)

Generated Go code (protobuf-go messages, grpc-go ready) is committed under `gen/go/` as the module `github.com/munisp/blueeconomy-contracts/gen/go`. Pin an immutable release tag; do not track a moving branch:

```bash
go get github.com/munisp/blueeconomy-contracts/gen/go@gen/go/v1.2.3
```

`gen/go/v1.2.3` module tags point at the same commit as contract release tag `v1.2.3` (Go requires the directory prefix for subdirectory modules). CI enforces that the committed code is reproducible: `buf generate` followed by `git diff --exit-code -- gen/go` must be clean, and `go build ./...` + `go vet ./...` must pass in `gen/go`.

### Other languages

Generate from source pinned to a git tag or commit:

```bash
buf generate --template '{"version":"v2","plugins":[{"local":"protoc-gen-go","out":"gen/go"}]}' \
  git+https://github.com/munisp/blueeconomy-contracts.git#tag=<release-tag>
```

or clone and run `protoc`/your language plugin against `proto/` with the protobuf well-known types on the include path. Release tags also carry a descriptor-set artifact (`blueeconomy-contracts-<tag>.descriptor.binpb`, imports included) on the GitHub release.

## Validation

```bash
./scripts/validate-contracts.sh   # protoc descriptor build
buf lint                          # STANDARD ruleset
buf format --diff --exit-code     # canonical formatting
buf breaking --against ".git#branch=main"   # FILE compatibility ruleset
```

Breaking changes require a documented migration decision, consumer inventory and compatibility window before merge.
