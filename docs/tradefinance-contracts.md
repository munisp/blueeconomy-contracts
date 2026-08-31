# Trade-Finance Contracts (WP-6)

`blueeconomy.tradefinance.v1` covers the CamelONE-style multi-bank trade
finance rail (Singapore NTP TFC pattern):

- Consent lifecycle: `ConsentGranted`, `ConsentRevoked` on
  `tradefinance.consent.v1`.
- Product workflow: `ApplicationSubmitted`, `ApplicationDecisionRecorded`,
  `DisbursementRecorded`, `SettlementRecorded` on
  `tradefinance.application.v1`.

All payloads carry tokenized references, digests and integer money only.
Producer: `blueeconomy-financial-controls` (`internal/tradefinance`).
Signed fixtures live in `fixtures/tradefinance/`.
