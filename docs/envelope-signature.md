# Envelope Provenance Signature — Fleet Scheme

**Status:** normative for all platform producers and consumers of the canonical
event envelope (`blueeconomy.contracts.v1.EventEnvelope`, envelopeVersion `1.0`).
Every implementation (Go, TypeScript, Python) must agree on this document
byte-for-byte; divergence is a security defect.

## 1. Signature value

`provenance.signature` is a **JWS compact serialization** (RFC 7515) using
**EdDSA over Ed25519** (RFC 8037), with exactly three non-empty
base64url-encoded segments:

```
base64url(protected-header) "." base64url(payload) "." base64url(signature)
```

Base64url is the RFC 4648 §5 alphabet **without padding** (`=` is prohibited).

### 1.1 Protected header

The protected header is exactly this JSON object (key order irrelevant before
encoding; no other members are permitted):

```json
{"alg":"EdDSA","kid":"<producer>-<epoch>"}
```

- `alg` must be the string `EdDSA`. Consumers must reject any other algorithm
  (fail closed — no algorithm negotiation).
- `kid` names the producer signing key (see §2).

### 1.2 Payload

The payload is the **JCS-canonicalized (RFC 8785) JSON of the full envelope
excluding the `provenance.signature` field**, encoded as UTF-8. All other
fields — including the other `provenance` members (`principalId`,
`principalRole`, `ledgerCommitHash`) — are inside the signed payload.

Canonicalization rules (RFC 8785):

- Object members sorted by key using UTF-16 code-unit order; no whitespace.
- Strings use minimal JSON escaping; non-ASCII characters are emitted raw
  (UTF-8), never `\u`-escaped except the mandatory control-character escapes.
- Numbers follow ECMAScript `Number::toString` semantics (shortest
  round-trip; exponential form only below 1e-6 or at/above 1e21). Producers
  must not emit numbers outside the IEEE-754 double-precision safe range.
- No duplicate object keys; the payload must be valid JSON.

Consumers must re-canonicalize the received envelope (minus the signature
field) and require a **byte-exact match** with the decoded payload segment
before verifying the signature. This makes the compact serialization
self-verifying and prevents payload/canonicalization substitution.

### 1.3 Signature input

The Ed25519 signature is computed over the ASCII bytes:

```
base64url(protected-header) "." base64url(payload)
```

exactly as RFC 7515 §5.1 specifies (the signature is over the encoded
segments, not over a digest of them, and not over the raw JSON).

## 2. Key identifier (`kid`) convention

```
kid = "<producer>-<epoch>"
```

- `<producer>` is the stable deployable name carried in the envelope's
  `producer` field (for example `blueeconomy-credential-verification`).
  Consumers should treat a mismatch between the `kid` producer prefix and the
  envelope `producer` field as suspicious, but the key directory (§3) is the
  sole source of truth for key resolution.
- `<epoch>` is the producer's key-rotation epoch: a non-negative integer
  (decimal, no leading zeros) incremented on every key rotation. Old epochs
  are removed from the directory only after all events signed with them have
  aged out of every consumer's replay window.
- Allowed `kid` characters: `[A-Za-z0-9._-]`, length 1–256.

## 3. Public-key directory

The platform distributes producer public keys as a **mounted JSON file**;
the filesystem path is supplied through the `KEY_DIRECTORY_PATH` environment
variable. Shape:

```json
{
  "blueeconomy-credential-verification-0": "n4bQgYhMfWWaL-qgxVrQFaO_TxsrC4Is0V1sFbDwCgg",
  "blueeconomy-financial-controls-3": "Gb9ECWmEzf6FQbrBZ9w7lshQhqowtrbLDFw4rXAxZuE"
}
```

- Keys: `kid` strings per §2. Values: base64url (no padding) encodings of the
  raw 32-byte Ed25519 public key.
- Consumers load the directory **once at startup** and must **fail closed**
  (refuse to start) when the file is absent, unreadable, not a regular
  non-symlink file, not valid JSON, or contains a malformed key.
- Private keys never leave the producer boundary and are never carried in
  events or in the directory.

## 4. Consumer verification algorithm (fail closed)

1. Parse the envelope JSON. Require `provenance.signature` to be a string of
   three non-empty base64url segments; reject otherwise.
2. Decode the protected header; require `alg == "EdDSA"` and a well-formed
   `kid`; reject otherwise.
3. Resolve `kid` in the key directory; **unknown kid → reject**.
4. Decode the payload segment; require it to byte-equal the RFC 8785
   canonicalization of the envelope minus `provenance.signature`; reject
   otherwise.
5. Verify the Ed25519 signature over `segment1 + "." + segment2` with the
   resolved public key; **invalid signature → reject**.
6. Any rejection must be logged with a reason code
   (`malformed-jws`, `unsupported-alg`, `unknown-kid`, `payload-mismatch`,
   `invalid-signature`) and counted; rejected envelopes must never be
   persisted or forwarded.

Rejection is terminal: there is no retry, fallback, or "unsigned but
well-formed" admission path.

## 5. Worked invariant

For an envelope `E` with signature field `s`:

```
payload(E) == JCS-UTF8(E minus provenance.signature)
signature(E) == Ed25519.Sign(key(kid), b64u(header) + "." + b64u(payload(E)))
```

A verifier accepts `E` iff both hold and `kid` is present in the directory.
