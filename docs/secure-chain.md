# Secure Chain (WP-7) — Verified-Chain Digital Container Release

**Status:** normative for producers and consumers of the `ports.securechain.v1`
topic. Modelled on the Portbase Secure Chain (mandatory for import containers
in the Netherlands since Feb 2025): a shipping line issues a digital release
authorization that passes down a verified chain (line → forwarder →
transporter); each link explicitly nominates the next; the terminal releases
the container only to the last verified chain holder.

## 1. No PINs, no shared secrets

PIN-code releases are phishable and are prohibited. Actor identity is always
the **verified OIDC/Keycloak gateway subject** of the request; organisation
identifiers in the contract are those verified subjects. Nothing in this
contract carries a password, PIN or bearer secret.

## 2. Data model

- **ReleaseChain** — `chain_id`, ISO 6346 `container_id`, `bl_digest_sha256`
  (SHA-256 of the carrier B/L manifest record; the plaintext B/L never leaves
  the shipping line), `issuer_org`, status `ACTIVE | COMPLETED | REVOKED |
  EXPIRED`. One ACTIVE chain per container (DB-enforced partial unique
  index). Chain creation requires B/L release authority registered by the
  same verified shipping-line organisation.
- **ChainLink** — append-only, hash-chained:
  `link_hash = sha256(prev_link_hash || "|" || JCS(link identity fields))`.
  `seq` and `prev_hash` are trigger-pinned to the previous link; identity
  fields are immutable; a link resolves exactly once (`ACCEPTED | DECLINED |
  REVOKED`). The **single-active-tail invariant** is DB-enforced: at most one
  PENDING link per chain, and only the current tail holder (accepted nominee,
  or the nominator after a decline) may append the next link.
- **Release token** — short-TTL, single-use, envelope-signed JWS carrying a
  random 256-bit nonce. Consumption is an atomic
  `UPDATE ... WHERE consumed_at IS NULL`; replay is DB-rejected.
- **Audit ledger** — hash-chained append-only
  (`entry_hash = sha256(prev || "|" || JCS(payload))`); recomputation detects
  any out-of-band tampering.

## 3. Lifecycle

1. `chain_created` — shipping line (shipping-line role, B/L release
   authority) opens the chain.
2. `link_nominated` — current tail nominates the next organisation.
3. `link_accepted` / `link_declined` — the nominee resolves the pending
   link; a decline returns the tail to the nominator.
4. `chain_revoked` — issuer kills the chain; revocation cascades to
   unresolved links and outstanding tokens.
5. `release_authorized` — issued ONLY to the verified tail holder via
   `GET /v1/secure-chain/{container}/release-authorization`.
6. `release_consumed` — the gate/eCallUp check-in redeems the nonce
   (`POST /v1/secure-chain/consume`, terminal-operator or gate-officer
   role); the chain becomes COMPLETED.
7. `chain_expired` — the Temporal expiry sweep retires stale ACTIVE chains.
8. `velocity_flagged` — anti-fraud anomaly hook: more than the configured
   number of nominations within 24h flags the chain and, with fail-closed
   hold configured, blocks all further nominations and releases.

## 4. eCallUp integration

A truck booking bound to an import container (`container_id` on the booking)
is gated on the verified chain tail **inside the booking transaction** — the
booking is refused fail-closed when the caller is not the tail holder, when a
nomination is pending, or when no release verifier is wired. The gate
consumes the single-use token at check-in.

## 5. Envelope and signature

All events use envelope v1.0 (FHIR R4 message Bundle + JWS EdDSA/JCS
provenance signature) exactly as specified in
[envelope-signature.md](envelope-signature.md). Producer:
`s1-port-interoperability`; topic: `ports.securechain.v1`. Signed fixtures
for every lifecycle event live in
[fixtures/securechain/](fixtures/securechain/). Message schemas:
`proto/blueeconomy/securechain/v1/securechain.proto`.
