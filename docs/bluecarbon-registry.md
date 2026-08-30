# Blue-Carbon Registry Events and Credit Serial Grammar

**Status:** normative companion to
`proto/blueeconomy/contracts/v1/bluecarbon.proto` for the `bluecarbon.*`
topics. Envelope transport, validation order and signing are unchanged: every
event is the primary resource of an `EventEnvelope` FHIR message Bundle
(`envelope.proto`) and is signed per
[`docs/envelope-signature.md`](envelope-signature.md). This document adds no
new envelope behaviour. It additionally defines, normatively, the credit
serial-number grammar.

## Event types

| Topic | Event type | Primary resource | Classification |
| --- | --- | --- | --- |
| `bluecarbon.projects` | `bluecarbon.project.v1` | `BlueCarbonProjectStateChanged` | `INTERNAL` |
| `bluecarbon.evidence` | `bluecarbon.evidence.v1` | `BlueCarbonEvidenceSubmitted` | `CONFIDENTIAL` |
| `bluecarbon.verifications` | `bluecarbon.verification.v1` | `BlueCarbonVerificationRecorded` | `CONFIDENTIAL` |
| `bluecarbon.credit-blocks` | `bluecarbon.credit-block.v1` | `BlueCarbonCreditBlockIssued` | `INTERNAL` |
| `bluecarbon.ledger` | `bluecarbon.ledger-movement.v1` | `BlueCarbonLedgerMovementPosted` | `INTERNAL` |
| `bluecarbon.retirements` | `bluecarbon.retirement.v1` | `BlueCarbonRetirementRecorded` | `INTERNAL` (public projection downstream only) |

Synthetic, schema-valid example envelopes for all six types live under
[`fixtures/bluecarbon/`](../fixtures/bluecarbon/).

## FHIR R4 resource profiles

When an envelope is projected to FHIR R4 JSON for FHIR-native consumers, the
primary resource renders as follows (StructureDefinition namespace
`https://blueeconomy.gov.ng/fhir/StructureDefinition/`; the proto contract
remains the governing schema and the projection must not widen the field set):

| Event type | FHIR profile | Extension URL |
| --- | --- | --- |
| `bluecarbon.project.v1` | `Location` (project boundary reference) plus `Provenance` (registration act) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/bluecarbon-project` |
| `bluecarbon.evidence.v1` | `DocumentReference` with one sha256 hash per evidence artifact | `https://blueeconomy.gov.ng/fhir/StructureDefinition/bluecarbon-evidence` |
| `bluecarbon.verification.v1` | `Provenance` (decision as activity code, verifier as agent) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/bluecarbon-verification` |
| `bluecarbon.credit-block.v1` | `Contract` (the credit block) plus `Provenance` (issuance) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/bluecarbon-credit-block` |
| `bluecarbon.ledger-movement.v1` | `Provenance` (ledger movement) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/bluecarbon-ledger-movement` |
| `bluecarbon.retirement.v1` | `Contract` (the retired block) plus `Provenance` (retirement) | `https://blueeconomy.gov.ng/fhir/StructureDefinition/bluecarbon-retirement` |

## Credit serial-number grammar (Article 6.4-aligned)

The serial number of a credit block is a contracts artifact. It is aligned
with the UNFCCC Article 6 guidance that the UNDP National Carbon Registry
(Digital Public Good) implements — ITMO/unit unique-identifier elements per
Decision 5/CMA.4 (guidance on cooperative approaches) and Decision 6/CMA.4
annex I paragraph 5, and the Article 6.4 mechanism registry procedure
(A6.4-SBM015-A12, paragraphs 13–17): host Party, activity identifier, vintage
year, and a serial number unique within each (vintage, activity) combination —
and carries the fields CAD Trust mapping requires.

### Grammar

```
serial = hostParty "-" registryId "-" projectSerial "-" methodologyCode
         "-" vintage "-" blockStart "-" blockEnd
```

ABNF-style definition (the wire value must match this regular expression):

```
^[A-Z]{2}-BCR-[0-9]{4,8}-[A-Z0-9][A-Z0-9_]{0,31}-(19|20)[0-9]{2}-[1-9][0-9]{0,11}-[1-9][0-9]{0,11}$
```

| Element | Definition |
| --- | --- |
| `hostParty` | ISO 3166-1 alpha-2 code of the host Party (for example `NG`). |
| `registryId` | `BCR` — the national blue-carbon registry. Distinct from `UN01`, which designates the UNFCCC Article 6.4 mechanism registry under the common nomenclatures. |
| `projectSerial` | National project sequence number, 4–8 digits, assigned at registration; with `hostParty` and `registryId` it forms the project identifier (the national analogue of the Article 6.4 activity identifier). |
| `methodologyCode` | Approved methodology token from the operator-approved registry policy, uppercased with dots as underscores (for example `VERRA_VM0033_V2_1`). |
| `vintage` | Four-digit year in which the emission reductions or removals occurred. |
| `blockStart` | First unit serial number of the block, 1-based, unique within the (project, vintage) namespace. |
| `blockEnd` | Last unit serial number of the block; `blockEnd >= blockStart`. |

Example: `NG-BCR-0007-VERRA_VM0033_V2_1-2025-1-3000` — Nigerian national
registry, project 0007, Verra VM0033 v2.1, vintage 2025, units 1–3000.

Each unit represents exactly 1 tCO2e and is indivisible, consistent with the
Article 6.4 registry rule that tracked units are indivisible. Blocks are
managed as consecutive serial ranges, and serial numbers remain unchanged
throughout the credit life cycle, including across transfers between accounts.

### Elements carried as structured fields, not embedded in the serial

The cooperative-approach identifier (`CA[NNNN]`, with `CA0001` designating the
Article 6.4 mechanism itself), the authorization designation (`N`/`I`/`O` for
authorized AERs; MCU designation for mitigation-contribution units), the
conditionality of authorization (`C`/`NC`) and the first-transfer flag (`FT`)
are **not** embedded in the national serial. They are carried as structured
fields on `BlueCarbonCreditBlockIssued` (`authorization`,
`corresponding_adjustment`, `first_transferred`) so CAD Trust and AEF
(Article 6.2 Agreed Electronic Format) mappings can be derived without
parsing.

### Partial-block split rule

When a block is partially transferred or retired, the current owner always
retains the **first** sub-block and the transferee/retirement receives the
**last** sub-block (the UNDP registry / Article 6 serial-block rule). For
example, transferring 1,000 of the 3,000 credits of
`NG-BCR-0007-VERRA_VM0033_V2_1-2025-1-3000` yields
`NG-BCR-0007-VERRA_VM0033_V2_1-2025-1-2000` (retained by the owner) and
`NG-BCR-0007-VERRA_VM0033_V2_1-2025-2001-3000` (transferred).

### Fail-closed validation

Producers and consumers must reject a serial that does not match the grammar,
whose `blockEnd < blockStart`, or whose quantity does not equal
`blockEnd - blockStart + 1` whole credits. The final methodology list, buffer
rules and crediting-period bounds ship as an operator-approved registry policy
document citing the underlying methodologies (Verra VM0033 v2.1, Gold Standard
SMM 2024, Plan Vivo); the registry fails closed without it.

## Non-fabrication rules carried by the contract

- **No invented sequestration rates or default factors.** Events carry claimed
  and verifier-adjusted quantities attributable to a cited methodology; the
  registry records and checks arithmetic but never computes carbon from
  built-in defaults.
- **No issuance without VERIFIED status** and a recorded buffer percentage
  from the methodology risk-tool output (dual-control entry; bounds checked,
  risk never computed by the system).
- **External-registry linkage is recorded, never asserted as verified**;
  reconciliation discrepancies fail closed and block further issuance for the
  project.
- **Retirement is terminal** — no un-retire; retirement movements are posted,
  never voided.
- **The credit ledger is a dedicated namespace**; no code path moves credits
  and currency in one movement.
- **Public transparency is projection-by-construction**: the public API reads
  only governed gold projections; evidence internals and confidential fields
  never leave their classification boundary.
