# Met-ocean advisory event fixtures (SYNTHETIC)

One canonical-wire envelope JSON per event type defined in
`proto/blueeconomy/contracts/v1/metocean.proto` and described in
`docs/met-ocean-advisories.md`.

All contents are synthetic: identifiers, references, positions, quantities,
timestamps and keys are invented for schema illustration only and must never
be treated as real operational data. The fixtures are, however, schema-valid
against the compiled descriptor set and carry genuinely verifiable
JWS-EdDSA signatures (RFC 7515 compact serialization over the RFC 8785
JCS-canonicalized envelope, per `docs/envelope-signature.md`), signed with a
throwaway synthetic key so consumers can exercise their full verification
path:

```
kid:        blueeconomy-waterway-safety-0
public key: uLft_MTFfuFxhL4Esnc5-kgJvfzoU3uGvK87QGDtf8I
```

This key is for fixture verification only and is not a production producer
key; production key directories are distributed per
`docs/envelope-signature.md` §3.
