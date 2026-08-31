# Trade-Finance Fixtures (WP-6)

Signed envelope fixtures for `tradefinance.consent.v1` and
`tradefinance.application.v1` (proto: `proto/blueeconomy/tradefinance/v1/tradefinance.proto`).

- `tradefinance.consent-granted.v1.json` — ConsentGranted
- `tradefinance.application-submitted.v1.json` — ApplicationSubmitted
- `tradefinance.application-decision.v1.json` — ApplicationDecisionRecorded
- `tradefinance.disbursement-recorded.v1.json` — DisbursementRecorded

Every fixture carries an Ed25519 JWS provenance signature (kid
`financial-controls-wp6-fixture`) over the RFC 8785 canonical envelope, as
produced by the financial-controls outbox signer. Fixture keys are test-only
and are never trusted by any production verifier.
