# Geospatial and Vessel-Tracking Events

**Status:** normative companion to `proto/blueeconomy/contracts/v1/geo.proto`
for the `geo.*.v1` topics. Envelope transport, validation order and signing
are unchanged: every event is the primary resource of an
`EventEnvelope` FHIR message Bundle (`envelope.proto`) and is signed per
[`docs/envelope-signature.md`](envelope-signature.md). This document adds no
new envelope behaviour.

## Event types

| Event type | Primary resource | Purpose |
| --- | --- | --- |
| `geo.vessel-position.v1` | `VesselPositionReported` | Single validated position report from an AIS receiver, GSM/satellite tracker, or the mobile application. |
| `geo.vessel-static.v1` | `VesselStaticReported` | Static and voyage-related vessel data decoded from AIS message types 5, 19 and 24 (or an equivalent registry update). |
| `geo.geofence-event.v1` | `GeofenceEventRecorded` | Vessel crossing into (`ENTER`) or out of (`EXIT`) a governed geofence zone. |
| `geo.app-position-report.v1` | `AppPositionReported` | Manual Tier-0 mobile position report with device-outbox idempotency. |
| `geo.sos.v1` | `SosAlertRaised` | Distress alert raised from the Tier-0 mobile application. |

Synthetic, schema-valid example envelopes for all five types live under
[`fixtures/geo/`](../fixtures/geo/).

## FHIR Bundle mapping

Each event is carried exactly like every other platform event: the envelope's
`fhir` bundle has `resourceType` `"Bundle"` and `type` `"message"`, and
`entry[0]` is the primary event resource as a `google.protobuf.Any` whose
`type_url` names the proto message
(`type.googleapis.com/blueeconomy.contracts.v1.<Message>`). Consumers map
`eventType` to that resource type and must fail closed on any mismatch, on an
unrecognised `type_url`, or on the legacy `bundle` wire key.

When an envelope is projected to FHIR R4 JSON for FHIR-native consumers, the
primary resource renders as a FHIR `Basic` resource whose `code` identifies
the event type and whose event-specific fields are carried as extensions
under the platform StructureDefinition namespace
`https://blueeconomy.gov.ng/fhir/StructureDefinition/`. The extension URLs
for the geo event family are:

| Event type | Extension URL |
| --- | --- |
| `geo.vessel-position.v1` | `https://blueeconomy.gov.ng/fhir/StructureDefinition/geo-vessel-position` |
| `geo.vessel-static.v1` | `https://blueeconomy.gov.ng/fhir/StructureDefinition/geo-vessel-static` |
| `geo.geofence-event.v1` | `https://blueeconomy.gov.ng/fhir/StructureDefinition/geo-geofence-event` |
| `geo.app-position-report.v1` | `https://blueeconomy.gov.ng/fhir/StructureDefinition/geo-app-position-report` |
| `geo.sos.v1` | `https://blueeconomy.gov.ng/fhir/StructureDefinition/geo-sos` |

The proto contract remains the governing schema; the FHIR projection is a
rendering of it and must not widen the field set.

## Source-class taxonomy

`PositionSourceClass` is the fail-closed set of position-report origins.
Free-text source values are prohibited; the canonical JSON wire form renders
the values without the `POSITION_SOURCE_CLASS_` prefix.

| Wire value | Meaning |
| --- | --- |
| `AIS` | Terrestrial or satellite AIS receiver network (message type carried in `ais_message_type`). |
| `GSM_TRACKER` | GSM/GPRS tracker hardware installed on the vessel. |
| `SAT_TRACKER` | Satellite tracker hardware installed on the vessel. |
| `APP_REPORT` | Human-reported position from the Tier-0 mobile application; `mmsi` may be empty. |

## Classification floors

`GeoClassification` classifies the geospatial content itself and is
deliberately distinct from the envelope-level `EnvelopeClassification` (which
governs the whole event's trust boundary) and from the optional per-record
`ClearanceLabel`. Producers must assert both coherently: the envelope
classification must be at least as restrictive as the event content.

- `geo.sos.v1`: **minimum `RESTRICTED`**. Producers must classify SOS alerts
  at `GEO_CLASSIFICATION_RESTRICTED` or higher; consumers must fail closed on
  a lower value.
- `geo.app-position-report.v1`: defaults to `PUBLIC` for Tier-0 community
  reports.
- `geo.vessel-position.v1` / `geo.vessel-static.v1`: typically `PUBLIC` or
  `INTERNAL` for commercial AIS traffic; ISR-adjacent positions (defence,
  law-enforcement or sanctioned-actor tracks) may carry up to `SECRET`. Events
  classified `RESTRICTED` or higher must also populate the envelope
  `record_classification` per `envelope.proto`.
- `geo.geofence-event.v1`: classification follows the sensitivity of the zone;
  enforcement-zone crossings are typically `INTERNAL` or higher.

## Field conventions

- Coordinates are fixed-point micro-degrees (`latitude_micros`,
  `longitude_micros`); speeds, courses, headings and draughts are likewise
  fixed-point integers (`*_milliknots`, `*_millidegrees`,
  `*_millimetres_per_second`, `draught_millimetres`). Floating-point
  coordinates, speeds and draughts are prohibited.
- `mmsi` is exactly 9 decimal digits. It is optional only on
  `VesselPositionReported` when `source_class` is `APP_REPORT`. On
  `GeofenceEventRecorded` exactly one of `mmsi` or `track_reference` must be
  populated; consumers must fail closed on violation.
- `nav_status`, `ais_message_type` and `ship_type_code` carry the raw AIS code
  table values as integers; `epfs_type` is the fail-closed `EpfsType` enum
  mirroring the AIS EPFS code table.
- `reporter_id` is pseudonymous (never a device identifier, phone number or
  personal name) and `vessel_reference` is a tokenized registry reference.
  Device clocks are untrusted: `recorded_at` on mobile-origin events is the
  device-clock reading and consumers reconcile it against the envelope
  `occurred_at`.
- `outbox_id` is the producer idempotency key from the device outbox;
  consumers must dedupe on `(reporter_id, outbox_id)` so offline replays of
  `geo.app-position-report.v1` and `geo.sos.v1` are applied exactly once.
- `free_text` on `SosAlertRaised` is capped by the producer at 280 characters
  and must not embed documents, credentials or contact details.

## Signing

No changes to the fleet signature scheme. Geo producers sign envelopes with
JWS-EdDSA over the RFC 8785 JCS-canonicalized envelope exactly as specified in
[`docs/envelope-signature.md`](envelope-signature.md); consumers apply its
fail-closed verification algorithm before unpacking any geo resource.
