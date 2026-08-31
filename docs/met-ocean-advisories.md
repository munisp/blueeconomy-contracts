# Met-Ocean Advisory Events

**Status:** normative companion to
`proto/blueeconomy/contracts/v1/metocean.proto` for the
`waterways.met_ocean.advisories.v1` topic. Envelope transport, validation
order and signing are unchanged: every event is the primary resource of an
`EventEnvelope` FHIR message Bundle (`envelope.proto`) and is signed per
[`docs/envelope-signature.md`](envelope-signature.md). This document adds no
new envelope behaviour.

Advisories are produced by the waterway-safety service from configured
met-ocean feeds (or the audited operator-override channel) and follow a WMO
Common Alerting Protocol (CAP) 1.2 profile. **Advisories are operational
decision-support issued by the platform sender; they are never presented as
official national met-authority (NiMet) warnings.** With no feed configured,
the producing service issues nothing; there is no synthetic feed.

## Event types

| Event type | Primary resource | Purpose |
| --- | --- | --- |
| `waterways.met_ocean.advisory.v1` | `MetoceanAdvisoryIssued` | Issue, update or explicit cancellation of a CAP-profile met-ocean advisory. |

A synthetic, schema-valid example envelope lives under
[`fixtures/metocean/`](../fixtures/metocean/).

## CAP 1.2 profile

`MetoceanAdvisoryIssued` carries the CAP elements as governed fields:

- `advisory_id` is the CAP `identifier`; `sender` is the stable platform
  producer name; `category` is fixed to `"Met"` (fail closed otherwise).
- `msg_type` (`ALERT`, `UPDATE`, `CANCEL`) governs the lifecycle. **Cancel is
  explicit**: an active advisory whose feed goes dark or whose conditions
  subside is terminated by a `CANCEL` advisory carrying
  `references_advisory_id` — never by silent absence — so downstream consumers
  (for example the ferry boarding-pause bridge) resume deterministically.
- `severity`/`urgency`/`certainty` are the CAP 1.2 code tables rendered
  without their enum prefixes (`Minor`, `Moderate`, `Severe`, `Extreme`,
  `Unknown`; `Immediate`, `Expected`, `Future`, `Past`, `Unknown`;
  `Observed`, `Likely`, `Possible`, `Unlikely`, `Unknown`).
- `effective_from`/`onset`/`effective_until` map to CAP
  `effective`/`onset`/`expires`.
- `zone_id` references the signed, versioned hazard-zone registry; zone
  geometry is not carried in the event.

## Digest binding and attribution

Every advisory is bound by `bulletin_reference` to the SHA-256 digest of the
raw source artifacts it was derived from; advisories are never issued without
a digest-bound source. `attribution_text` (licence attribution, for example
"Weather data by Open-Meteo.com") is mandatory and non-empty for feed-derived
advisories. `policy_digest_sha256` binds the signed advisory-policy and
hazard-zone-registry versions applied.

`source` is `FEED` or `OPERATOR_OVERRIDE`; operator overrides are a retained,
audited manual channel and are always classified distinctly.

## Classification

Advisories are typically `INTERNAL`. An advisory is never promoted to a lower
classification to reach a wider audience; distribution beyond the platform
uses the governed read API.
