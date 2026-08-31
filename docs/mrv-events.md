# MRV Emissions Events

**Status:** normative companion to `proto/blueeconomy/contracts/v1/mrv.proto`
for the `mrv.*` topics. Envelope transport, validation order and signing are
unchanged: every event is the primary resource of an `EventEnvelope` FHIR
message Bundle (`envelope.proto`) and is signed per
[`docs/envelope-signature.md`](envelope-signature.md). This document adds no
new envelope behaviour.

The module implements IMO DCS (MARPOL Annex VI reg. 27, Resolution
MEPC.278(70), enhanced granularity per MEPC.385(81)) as the compliance core,
with an EU-MRV-compatible voyage ledger (Regulation (EU) 2015/757 as amended)
and CII outcomes (MEPC.328(76)/MEPC.333(76)) only when operator-approved,
source-cited CII configuration exists.

## Event types

| Topic | Event type | Primary resource | Classification |
| --- | --- | --- | --- |
| `mrv.fuel-reports` | `mrv.fuel-report.v1` | `MrvFuelReportRecorded` | `CONFIDENTIAL` |
| `mrv.voyages` | `mrv.voyage.v1` | `MrvVoyageRecorded` | `CONFIDENTIAL` |
| `mrv.verifications` | `mrv.verification.v1` | `MrvVerificationRecorded` | `CONFIDENTIAL` |
| `mrv.annual-reports` | `mrv.emissions-annual.v1` | `MrvEmissionsAnnualReportSubmitted` | `CONFIDENTIAL` |
| `mrv.soc` | `mrv.soc.v1` | `MrvStatementOfComplianceIssued` | `INTERNAL` |
| `mrv.activity-estimates` | `mrv.activity-estimate.v1` | `MrvActivityEstimateComputed` | `INTERNAL` |

Synthetic, schema-valid example envelopes for all six types live under
[`fixtures/mrv/`](../fixtures/mrv/).

## FHIR R4 resource profiles

When an envelope is projected to FHIR R4 JSON for FHIR-native consumers, the
primary resource renders as follows (StructureDefinition namespace
`https://blueeconomy.gov.ng/fhir/StructureDefinition/`; the proto contract
remains the governing schema and the projection must not widen the field set):

| Event type | FHIR profile | Extension URL |
| --- | --- | --- |
| `mrv.fuel-report.v1` | `Observation` (code = fuel grade + consumer type; value = fuel quantity; period = reporting period) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/mrv-fuel-report` |
| `mrv.voyage.v1` | `Observation` (code = voyage ledger entry; BOSP/EOSP as effective period) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/mrv-voyage` |
| `mrv.verification.v1` | `Provenance` (decision as activity code, verifier as agent) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/mrv-verification` |
| `mrv.emissions-annual.v1` | `DocumentReference` (hash = report artifact sha256, period = calendar year) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/mrv-emissions-annual` |
| `mrv.soc.v1` | `DocumentReference` (hash = SoC artifact sha256) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/mrv-soc` |
| `mrv.activity-estimate.v1` | `Observation` (code = AIS-derived activity estimate) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/mrv-activity-estimate` |

## Non-fabrication rules carried by the contract

- **No invented emission factors.** Events carry `factor_set_digest_sha256`
  binding the exact source-cited factor-registry rows (MEPC.308(73)/
  MEPC.364(79); CH4/N2O/WtW from MEPC.391(81) and the IMO Fourth GHG Study).
  There is no default factor; a missing factor fails closed at the producer.
- **No invented CII parameters.** `attained_cii_nano`/`required_cii_nano` and
  `cii_rating` are carried only when computable from approved, source-cited
  configuration; otherwise they are absent (`NOT_COMPUTABLE`), never
  estimated.
- **No unverified report may produce an SoC.** `MrvStatementOfComplianceIssued`
  requires the referenced annual report to be `VERIFIED`; the artifact digest
  anchors the canonical signed artifact in the gold layer and equals the
  envelope `provenance.ledger_commit_hash`.
- **AIS activity is a cross-check.** `MrvActivityEstimateComputed` never
  overwrites reported values; `insufficient_coverage` is an honest outcome.
- **Fuel is classified by ISO 8217 viscosity grade** (`fuel_grade`), never by
  sulphur marketing label.
- Quantities are fixed-point integers (milli-tonnes, milli-nautical-miles,
  whole minutes, nano-CII); floating-point values are prohibited.
