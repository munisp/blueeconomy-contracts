# Geo event fixtures (SYNTHETIC)

One canonical-wire envelope JSON per `geo.*.v1` event type defined in
`proto/blueeconomy/contracts/v1/geo.proto` and described in
`docs/geo-events.md`.

All contents are synthetic: identifiers, MMSIs, names, positions, timestamps
and keys are invented for schema illustration only and must never be treated
as real vessel or reporter data. The fixtures are, however, schema-valid
against the compiled descriptor set and carry genuinely verifiable
JWS-EdDSA signatures (RFC 7515 compact serialization over the RFC 8785
JCS-canonicalized envelope, per `docs/envelope-signature.md`), signed with a
throwaway synthetic key so consumers can exercise their full verification
path:

```
kid:        blueeconomy-geo-ingestion-0
public key: WArcCuaq-GkNackss01j6JIoHtheYKo6eqQ7VXSAFhI
```

This key is for fixture verification only and is not a production producer
key; production key directories are distributed per
`docs/envelope-signature.md` §3.
