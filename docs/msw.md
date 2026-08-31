# Maritime Single Window (FAL/MSW) Events

**Status:** normative companion to `proto/blueeconomy/msw/v1/msw.proto` for
the `maritime.msw.v1` topic. Envelope transport, validation order and
signing are unchanged: every event is the primary resource of an
`EventEnvelope` FHIR message Bundle (`envelope.proto`) and is signed per
[`docs/envelope-signature.md`](envelope-signature.md). This document adds no
new envelope behaviour.

The module implements the IMO FAL.14(46) single-window mandate (in force
2024-01-01): authorities must accept arrival/stay/departure information
electronically through a single window, submitted once and re-used maximally
(UNECE Rec-33). Declaration data sets follow the IMO Compendium
(FAL.5/Circ.45); authentication and integrity follow FAL.5/Circ.46. The
domestic joint-boarding order is NPPM 2021: **Port Health boards first and
grants free pratique; only then do NIS, NCS, NDLEA and NIMASA board
jointly.**

The producing boundary is the `singlewindow` deployable
(`blueeconomy-singlewindow-msw`). Port-call state is owned by the
port-interoperability boundary; MSW events reference it by `port_call_id`
only and never duplicate port-call fields.

## Topic registration

| Topic | Producer | Purpose |
| --- | --- | --- |
| `maritime.msw.v1` | `blueeconomy-singlewindow-msw` | FAL/MSW ship-clearance workflow: visit declaration, FAL 1–7 + MDOH declaration lifecycle, Port Health pratique, NPPM 2021 joint boarding, arrival/departure clearance, agent nomination. |

## Event types

All eleven event types are carried on `maritime.msw.v1`, discriminated by
`eventType`:

| Event type | Primary resource | Purpose |
| --- | --- | --- |
| `maritime.msw.visit_created.v1` | `MswVisitCreated` | Ship visit declared in the single window; anchored to a port-interop port call when linked, honestly flagged `portCallVerified=false` when unlinked or unverifiable. |
| `maritime.msw.agent_nominated.v1` | `MswAgentNominated` | Shipping agent nominated for a visit; nomination instrument retained in the producing boundary (digest only). |
| `maritime.msw.declaration_submitted.v1` | `MswDeclarationSubmitted` | One FAL form (FAL1–FAL7) or MDOH submitted; monotonic per-(visit, form) `version`, hash-chained to the prior submission (single-submission principle). Payload digest only. |
| `maritime.msw.declaration_accepted.v1` | `MswDeclarationAccepted` | Authority accepted a declaration version (maker-checker at the boundary). |
| `maritime.msw.declaration_returned.v1` | `MswDeclarationReturned` | Authority returned a declaration version for correction with a stable reason code; re-submission is a new version. |
| `maritime.msw.pratique_granted.v1` | `MswPratiqueGranted` | Port Health granted free pratique against an MDOH — the NPPM 2021 ordering pivot. |
| `maritime.msw.pratique_refused.v1` | `MswPratiqueRefused` | Port Health refused pratique with a stable reason code; blocks all downstream boarding/clearance until a grant. |
| `maritime.msw.boarding_scheduled.v1` | `MswBoardingScheduled` | Boarding party scheduled with a fail-closed agency set; non-Port-Health parties only after pratique. |
| `maritime.msw.boarding_completed.v1` | `MswBoardingCompleted` | Boarding party completed; `pratiqueGrantDigestSha256` mandatory for any party containing NIS/NCS/NDLEA/NIMASA. |
| `maritime.msw.clearance_granted.v1` | `MswClearanceGranted` | Arrival or departure clearance granted; DEPARTURE binds the evaluated precondition checklist digest. |
| `maritime.msw.clearance_refused.v1` | `MswClearanceRefused` | Arrival or departure clearance refused with a stable reason code. |

Synthetic, schema-valid example envelopes for all eleven types live under
[`fixtures/msw/`](../fixtures/msw/).

## Pratique-first invariant (NPPM 2021)

The ordering Port Health → pratique → joint boarding → clearance is enforced
at the producing boundary (service and database) and is visible on the wire:

- A `maritime.msw.boarding_scheduled.v1` or
  `maritime.msw.boarding_completed.v1` event whose agency set contains NIS,
  NCS, NDLEA or NIMASA is only valid for a visit with an antecedent
  `maritime.msw.pratique_granted.v1` event (and no later refusal).
  Completions carry `pratiqueGrantDigestSha256` binding the exact grant
  record; consumers must fail closed on a non-Port-Health completion
  without it (`PRATIQUE_REQUIRED` at the boundary).
- A `maritime.msw.clearance_granted.v1` event of kind DEPARTURE is emitted
  only after every submitted FAL form version is accepted, pratique is
  granted and the joint boarding is completed;
  `preconditionChecklistDigestSha256` binds the evaluated precondition set.
  Consumers must fail closed on a DEPARTURE grant without it.

## Single-submission and versioning

Declarations are submitted once and re-used across agencies (UNECE Rec-33);
nothing is duplicated to other agencies on the bus. A re-submitted form
creates a new `version` for the same `(visit_id, form_type)` pair and chains
to the prior submission via `priorSubmissionDigestSha256`; returned versions
are never edited. Agency visibility is a consumer-side PBAC concern
(`msw-port-health`, `msw-nis`, `msw-customs`, `msw-ndlea`, `msw-nimasa`,
`msw-npa`, `msw-agent` roles at the producing/consuming boundary), not a
wire concern.

## Data minimization

FAL form payloads, crew/passenger lists, health records, review notes,
boarding findings and nomination instruments stay inside the producing
boundary; events carry identifiers, tokenized references, enum-governed
state, stable reason codes and `sha256:` digests only. No ETA, vessel or
port-call data is fabricated: unlinked visits are emitted with
`portCallVerified=false` (the honest `PORT_CALL_UNVERIFIED` state), and
port-call fields are never copied from the port-interoperability boundary.

## Classification floors

The envelope enums carry no `PERSONAL` value; the NDPA personal-data
category is therefore floored fail-closed at `RESTRICTED`, and
security-adjacent events floor at `CONFIDENTIAL`. Floors are minima —
producers may raise, never widen:

| Event type | Envelope `classification` floor | `recordClassification` |
| --- | --- | --- |
| `maritime.msw.visit_created.v1` | `INTERNAL` | — |
| `maritime.msw.agent_nominated.v1` | `INTERNAL` | — |
| `maritime.msw.declaration_submitted.v1` | `INTERNAL`; `RESTRICTED` when `containsPersonalData=true` (FAL4/FAL5/FAL6/MDOH — NDPA PERSONAL) | `RESTRICTED` when floored |
| `maritime.msw.declaration_accepted.v1` / `…_returned.v1` | `INTERNAL`; `RESTRICTED` when the reviewed form is FAL4/FAL5/FAL6/MDOH | `RESTRICTED` when floored |
| `maritime.msw.pratique_granted.v1` / `…_refused.v1` | `RESTRICTED` (health-decision records anchored to the MDOH) | `RESTRICTED` |
| `maritime.msw.boarding_scheduled.v1` / `…_completed.v1` | `CONFIDENTIAL` (law-enforcement boarding operations, security-adjacent) | `CONFIDENTIAL` |
| `maritime.msw.clearance_granted.v1` / `…_refused.v1` | `CONFIDENTIAL` (border clearance decisions, security-adjacent) | `CONFIDENTIAL` |

## External dependencies (registered gaps)

The MSW contracts are adapter-ready only toward external authority systems;
no wire compatibility with them is claimed. The following external
dependencies are registered in the platform gap registry as
`GAP-MSW-{ESEN,NIS,PH,NCS}` (FG must-bring list): NPA e-SEN (electronic Ship
Entry Notice) integration agreement, NIS endpoint agreement, Port Health
endpoint agreement, NCS endpoint agreement. Producers must fail closed when
an adapter is unconfigured (for example `PORT_CALL_UNAVAILABLE` /
`GAP-MSW-ESEN` disabled states); no stub success paths exist.
