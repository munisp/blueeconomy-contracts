# Yaounde Gateway Regional Exchange Events

**Status:** normative companion to `proto/blueeconomy/contracts/v1/yaounde.proto`
for the `maritime.yaounde.v1` topic. Envelope transport, validation order and
signing are unchanged: every event is the primary resource of an
`EventEnvelope` FHIR message Bundle (`envelope.proto`) and is signed per
[`docs/envelope-signature.md`](envelope-signature.md). This document adds no
new envelope behaviour.

The gateway exchanges incident reports, inbound regional advisories and shared
maritime picture contributions with Yaounde Architecture peers. **No YARIS or
peer wire-protocol compatibility is claimed or implied**: YARIS protocols are
not public, and interoperability with a real ICC/MMCC/MDAT-GoG endpoint is an
external integration action recorded in the gateway's peer registry before any
dispatch succeeds. With no peer endpoint configured, every exchange surface
reports UNCONFIGURED; these contracts do not create a simulated peer.

## Event types

| Event type | Primary resource | Purpose |
| --- | --- | --- |
| `maritime.yaounde.incident_report.v1` | `RegionalIncidentReport` | The sealed outbound incident-report artifact delivered to a peer; assembled strictly from adjudicated platform records, capped by the release marking and classification ceiling. |
| `maritime.yaounde.release_transitioned.v1` | `YaoundeReleaseTransitioned` | State transition of an outbound release (`DRAFT` → `APPROVED` → `DISPATCHED` → `ACKNOWLEDGED`; `FAILED` retryable-explicit; `WITHDRAWN` terminal). |
| `maritime.yaounde.inbound_report_admitted.v1` | `YaoundeInboundReportAdmitted` | Admission of an inbound peer report through the signed feed-admission path; lands pending analyst adjudication, never overwrites national records. |
| `maritime.yaounde.picture_contribution_transitioned.v1` | `YaoundePictureContributionTransitioned` | State transition of a shared-picture contribution; the classification ceiling is re-applied at dispatch time. |

Synthetic, schema-valid example envelopes for all four types live under
[`fixtures/yaounde/`](../fixtures/yaounde/).

## Release markings

`ReleaseMarking` is the closed distribution-caveat enum carried by every
exchanged message alongside the national clearance label
(`SecurityClassification` from `isr.proto`). Release rules never widen
visibility.

| Wire value | Rule |
| --- | --- |
| `NATIONAL_ONLY` | Never releasable. Asserting it on an outbound release is a fail-closed policy refusal (audited), not a dispatch. |
| `YAOUNDE_ZONE_E` | Releasable to the MMCC Zone E community. |
| `YAOUNDE_REGIONAL` | Releasable regionally across the Yaounde Architecture (ICC, CRESMAC, CRESMAO, all MMCC zones). |
| `MDAT_GOG_SHAREABLE` | Releasable to MDAT-GoG-style reporting contacts. |

## Signed inbound admission

Inbound peer reports are admitted only through the signed feed-admission path:
the peer payload is Ed25519-verified against the registered peer public key and
retained verbatim inside the gateway boundary. The event carries digests only
(`payload_digest_sha256`, `signature_digest_sha256`). Admission is replay-safe
on `(peer_reference, peer_report_reference)`: identical replay returns the
retained evidence; conflicting reuse fails closed with a refusal. Unknown
markings or peer kinds fail closed.

## Acknowledgement honesty

`YaoundeReleaseTransitioned` with state `ACKNOWLEDGED` must carry
`ack_receipt_digest_sha256`, the digest of a verifiable peer-signed receipt.
Consumers must fail closed on an `ACKNOWLEDGED` transition without it; an
acknowledgement is never fabricated or asserted ahead of the receipt.

## Classification floors

Envelope classification follows `isr.EnvelopeClassificationOf`-style mapping of
the content clearance label and never widens: `UNCLASSIFIED` → `INTERNAL`,
`RESTRICTED` → `RESTRICTED`, `CONFIDENTIAL`/`SECRET` → `CONFIDENTIAL`. Events
carrying content at `RESTRICTED` or higher also populate the envelope
`record_classification` per `envelope.proto`.
