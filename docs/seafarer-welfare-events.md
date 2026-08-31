# Seafarer Welfare / MLC 2006 Events

**Status:** normative companion to
`proto/blueeconomy/contracts/v1/welfare.proto` for the
`seafarers.welfare.v1` topic. Envelope transport, validation order and signing
are unchanged: every event is the primary resource of an `EventEnvelope` FHIR
message Bundle (`envelope.proto`) and is signed per
[`docs/envelope-signature.md`](envelope-signature.md). This document adds no
new envelope behaviour.

The welfare module implements the MLC 2006 complaint channels (Regulation
5.1.5 on-board; Regulation 5.2.2 flag-state/onshore), a welfare-provider
referral channel, and a rest-hour record surface with derived MLC Regulation
2.3 compliance flags. **All envelopes carrying these resources are classified
`CONFIDENTIAL`.**

## Event types

| Event type | Primary resource | Purpose |
| --- | --- | --- |
| `seafarer.welfare.complaint.v1` | `WelfareComplaintSubmitted` | Complaint intake, bound to a verified seafarer identity, with right-to-external-redress notice acknowledgement (Reg 5.1.5(3)). |
| `seafarer.welfare.complaint_status.v1` | `WelfareComplaintStatusTransitioned` | Governed maker-checker status transition; identity disclosures are emitted here with `disclosure_event=true`. |
| `seafarer.welfare.referral.v1` | `WelfareReferralRecorded` | Welfare-provider referral with mandatory recorded consent. |
| `seafarer.rest_hours.flagged.v1` | `RestHoursBreachFlagged` | Derived Reg 2.3 compliance flag against an operator-submitted record, versioned by policy. |

Synthetic, schema-valid example envelopes for all four types live under
[`fixtures/welfare/`](../fixtures/welfare/).

## Anti-victimization and confidentiality

Complainant identity is withheld from respondents until disclosure is legally
required (Reg 5.1.5(2)); events carry tokenized references and narrative
digests only, never identity or narrative content. Every disclosure is a
logged, maker-checker-approved transition event carrying
`disclosure_event=true` and a reason code; disclosure events are expected to
be rare and are alerted on. The right-to-redress notice is displayed and
acknowledged at intake; producers fail closed when
`right_to_redress_acknowledged` is false.

## Rest-hour records and flags

Rest-hour records are originated by operators/masters digest-bound and
immutable; the module never originates or alters records. Flags are derived,
recomputable computations: the same `(record, policy_version)` always yields
the same flags. The compliance regime (`MIN_REST` 10 h/24 h + 77 h/7 d, or
`MAX_WORK` 14 h/24 h + 72 h/7 d, with the ≤2-periods, ≥6 h single period and
≤14 h gap rules) is selected by a signed welfare-policy document — never
hard-coded — and mutation endpoints fail closed until it is configured.
Absent records are reported as NOT_SUBMITTED, never as compliant.
