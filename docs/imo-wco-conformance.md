# IMO / WCO / UN-CEFACT Wire Conformance — Maritime Single Window

Status: NORMATIVE for the `phase10/wp3-conformance` wire layer.
Scope: blueeconomy-singlewindow MSW (FAL forms 1–7 + MDOH) cross-border
export/import. Companion machine-readable artefacts:

- `mappings/msw/v1/*.yaml` — field-level mapping tables (authoritative).
- `mappings/msw/v1/extension-registry.yaml` — honest registry of platform-only fields.
- `schema/msw/v1/imo/imomsw-message.schema.json` — wire export/import message shape.

## 1. Why this layer exists

The platform models FAL 1–7 + MDOH internally (singlewindow
`server/mswService.ts`, `proto/blueeconomy/msw/v1/msw.proto`). Those payloads
are platform-internal on the wire. IMO MSW recognition and MSW-to-MSW
exchange (the model proven by Singapore digitalPORT@SG and the WCO Data
Model–native ASYCUDA Regional Single Window) require the window to speak the
**IMO Compendium on Facilitation and Electronic Business** data model
(Reference Model per FAL.5/Circ.45, authentication/integrity per
FAL.5/Circ.46), with WCO Data Model cross-references where a WCO element
exists. This document and its mapping tables are that layer.

## 2. Normative rules

1. **Fail closed.** Any mandatory IMO element that cannot be populated from a
   validated platform field rejects the export with a reason code
   (`IMO_EXPORT_UNMAPPED_ELEMENT`, `IMO_EXPORT_MISSING_MANDATORY`,
   `IMO_EXPORT_TYPE_VIOLATION`). Nothing is ever silently dropped; inbound
   messages with unmapped mandatory IMO elements are rejected
   (`IMO_IMPORT_UNMAPPED_ELEMENT`).
2. **Digest-bound.** Every export carries `source.formPayloadDigestSha256`,
   the sha256 (JCS-canonical) digest of the accepted declaration version it
   was transformed from, plus `source.declarationId`/`visitId`/`version`.
3. **Envelope v1.0.** Cross-border exchange wraps the IMO message in the
   platform EventEnvelope (`envelopeVersion: "1.0"`, JCS + JWS provenance
   signature, per `docs/envelope-signature.md`).
4. **Classification floors preserved.** FAL4, FAL5, FAL6 and MDOH carry
   personal data (NDPA PERSONAL) and floor the envelope at RESTRICTED with
   `recordClassification` set; floors are never widened by this layer.
5. **Honest extensions.** Platform fields with no IMO Compendium element are
   exported under `extensions.blueeconomy.<form>.<field>` and registered in
   `extension-registry.yaml`. Unregistered extensions reject the export.
6. **No fabrication.** Absent optional values are omitted, never synthesized.
   Unknown IMO/WCO cross-references are recorded as `wcoPath: null`, not
   guessed.

## 3. Mapping-table semantics (mappings/msw/v1)

Each form file:

```yaml
mappingVersion: "1.0"
form: FAL1                      # platform MswFormType wire value
imoMessage: IMOCompendium/GeneralDeclaration
reference: "IMO Compendium Reference Model, FAL.5/Circ.45 Annex"
fields:
  - platform: vesselImoNumber   # canonical platform payload field (camelCase)
    type: string                # string | integer | number | boolean | datetime | array<object>
    pattern: '^[0-9]{7}$'       # optional validation, enforced both directions
    mandatory: true             # mandatory in BOTH directions
    imoPath: IMOCompendium/GeneralDeclaration/Ship/IMONumber
    wcoPath: null               # WCO Data Model path where one exists, else null
    repeating: false            # true for list-valued fields
    itemFields: [...]           # nested mapping for repeating items
```

- `imoPath` uses the Compendium Reference Model structure
  (`IMOCompendium/<Message>/<aggregate>/<element>`). Element names follow the
  Compendium data set names; where the Compendium groups the same concept per
  form, the per-form message path is used.
- `wcoPath` is populated only where a WCO Data Model element is established
  for the concept (e.g. transport-means identification, UN/LOCODE locations);
  otherwise `null` — the honest "no established cross-reference" state.
- Round-trip requirement: for every mapped field, `import(export(x)) == x`
  (lossless). The conformance harness
  (singlewindow `scripts/msw-conformance/`) proves this per form.

## 4. Wire message shape

See `schema/msw/v1/imo/imomsw-message.schema.json`. Top level:

- `messageType`: `"IMO-MSW-FAL-EXPORT"` | `"IMO-MSW-FAL-IMPORT"`.
- `specVersion`: `"1.0"`.
- `messageId`, `issuedAt` (RFC 3339), `sender` (MSW operator identifier).
- `formType`: FAL1..FAL7 | MDOH.
- `source`: `{ declarationId, visitId, version, formPayloadDigestSha256 }` —
  export provenance; on import this block is absent and the platform stamps
  its own provenance (`provenance.foreignSender`, `provenance.importedAt`,
  `provenance.sourceMessageId`) on the created declaration DRAFT.
- `imoMessage`: object keyed by the mapped `imoPath` aggregates.
- `extensions`: `{ "blueeconomy": { "<FORM>": { ... } } }` — registered
  platform-only fields only.

## 5. Import direction (foreign MSW → platform)

A validated inbound IMO message produces a **platform declaration draft**
(status DRAFT-equivalent, i.e. it must still traverse the platform's own
submission/maker-checker lifecycle; import never auto-accepts). The draft
payload contains only mapped fields plus registered extensions, and carries:

```json
"provenance": {
  "foreignSender": "<sender from message>",
  "sourceMessageId": "<messageId>",
  "importedAt": "<RFC3339>",
  "direction": "IMPORT"
}
```

## 6. Cross-border exchange security

MSW-to-MSW transport mirrors the port-interoperability NSW JWS ingress
pattern (`blueeconomy-port-interoperability/internal/nswsecurity`):

- Inbound: `POST /api/v1/msw/exchange/ingest` requires an authority JWS
  (RS256, compact serialization) verified against a **pinned peer JWKS**
  (HTTPS URL + `sha256:` digest pin + allow-listed KIDs, env-only). The JWS
  protected-header `jti` is reserved in a replay store before processing;
  replays are rejected.
- Outbound: `POST /api/v1/msw/exchange/egress` transforms + signs
  (envelope v1.0, EdDSA provenance signature, env-only key). Delivery to a
  peer endpoint occurs only when a peer URL is explicitly configured;
  otherwise the signed payload is returned with an honest
  `delivery: "NOT_DELIVERED_NO_PEER_CONFIGURED"` marker — no fake
  connectivity.

## 7. Coverage statistics

Coverage (mapped platform fields / total platform fields per form) is
computed by the conformance harness and reported in its signed report. At
spec freeze, per-form totals are:

| Form | Mapped | Extension (platform-only) | Total |
|------|--------|---------------------------|-------|
| FAL1 | 19 | 1 | 20 |
| FAL2 | 14 | 1 | 15 |
| FAL3 | 14 | 1 | 15 |
| FAL4 | 14 | 1 | 15 |
| FAL5 | 19 | 1 | 20 |
| FAL6 | 18 | 1 | 19 |
| FAL7 | 19 | 1 | 20 |
| MDOH | 18 | 2 | 20 |
| **ALL** | **135** | **9** | **144** |

## 8. WCO CEN / ASEAN Single Window alignment

The export layer is the single source of IMO-shaped content for downstream
G2G channels. Alignment with singlewindow's existing `cen` (WCO Customs
Enforcement Network) and `aseanSw` (ASEAN Single Window G2G dispatch, WCO
XML formatting) routers is documented in singlewindow
`docs/imo-wco-cen-asean-alignment.md`, including extension points. No live
CEN/ASEAN connectivity is claimed by this layer.
