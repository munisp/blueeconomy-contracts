# SAR C2 Events

**Status:** normative companion to `proto/blueeconomy/contracts/v1/sar.proto`
for the `maritime.sar.v1` topic. Envelope transport, validation order and
signing are unchanged: every event is the primary resource of an
`EventEnvelope` FHIR message Bundle (`envelope.proto`) and is signed per
[`docs/envelope-signature.md`](envelope-signature.md). This document adds no
new envelope behaviour.

The SAR case lifecycle is IAMSAR-informed (IAMSAR Manual, Vol. II): emergency
phases INCERFA/ALERFA/DETRESFA and case stages AWARENESS → INITIAL_ACTION →
COORDINATION → STAND_DOWN. SAR cases are anchored to maritime incident records
(category `SAR`) inside the producing boundary.

## Event types

| Event type | Primary resource | Purpose |
| --- | --- | --- |
| `maritime.sar.case_opened.v1` | `SarCaseOpened` | Case opened via one of three fail-closed intake paths (`WATERWAY_EVENT`, `GEO_SOS`, `MANUAL`). |
| `maritime.sar.phase_changed.v1` | `SarPhaseChanged` | IAMSAR emergency phase declared/escalated/de-escalated with recorded rationale (digest). |
| `maritime.sar.stage_changed.v1` | `SarStageChanged` | Lifecycle stage transition; version-checked at the boundary. |
| `maritime.sar.tasking_changed.v1` | `SarTaskingChanged` | Tasking-order state change (`PROPOSED` → `TASKED` → `ACKED` → `ON_SCENE` → `RELEASED`; `ABORTED` terminal branch). |
| `maritime.sar.sitrep_issued.v1` | `SarSitrepIssued` | Numbered, immutable, envelope-v1.0-signed SITREP issued from retained case state. |
| `maritime.sar.case_closed.v1` | `SarCaseClosed` | Stand-down closure with recorded reason (`RESOLVED`, `SUSPENDED`, `FALSE_ALERT`, `HANDED_OVER`). |

Synthetic, schema-valid example envelopes for all six types live under
[`fixtures/sar/`](../fixtures/sar/).

## SITREP discipline

SITREPs are generated from retained case state — never free-typed untracked
text as the system of record. `sequence` is monotonic per case starting at 1;
an issued SITREP is never edited (corrections are a new SITREP number). The
issued body is an envelope-v1.0-signed artifact retained inside the producing
boundary; the event carries `body_digest_sha256` and `envelope_digest_sha256`.

## Intake provenance and idempotency

Exactly one `SarIntakeKind` is recorded per case. `WATERWAY_EVENT` intake rides
the signed feed-admission uniqueness on `(source, source_event)`; `GEO_SOS`
intake carries the geo `sos_alert_id` (geo-service remains the SOS system of
record); `MANUAL` intake is attributed to a watchkeeper principal. Replay
returns the retained case; conflicting reuse fails closed.

## Classification floors

Envelope classification equals the case classification and is never widened
(mapping per the ISR envelope-classification rule). SOS-sourced cases floor at
`RESTRICTED`, mirroring the `geo.sos.v1` floor in `docs/geo-events.md`; such
events populate the envelope `record_classification`. No SAR outcome is
asserted without record: stand-down reason, persons-recovered counts and
handover target are operator-recorded, attributed facts.
