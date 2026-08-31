# ML model registry contract (blueeconomy.ml.v1)

`proto/blueeconomy/ml/v1/registry.proto` defines the shared registry and
event contract unifying the platform's AI estates.

- **ModelRef** — registry identity (name, semver, optional artifact digest).
- **InferenceEvent** — emitted by blueeconomy-ml-stack to Kafka topic
  `ml.inference.v1` for every scoring decision (including
  `SCORING_UNAVAILABLE`). Carries score/model/latency plus SHA-256 digests
  of entity ID and feature vector — never raw PII. Transport is the
  platform envelope v1.0 (FHIR R4 message Bundle, JWS-EdDSA over RFC 8785
  JCS, kid `<producer>-<epoch>`).
- **HealthEvent** — model availability heartbeat (fail-closed states only).

Implementations:
- blueeconomy-ml-stack `inference/events.py` (producer, InferenceEvent).
- singlewindow `server/_core/cvEnvelope.ts` + `cvContainerConsumer.ts`
  (envelope verification; same contract family as cv.*.v1 consumers) and
  `server/_core/polyglotClients.ts` (declaration-fraud scorer client).
- blueeconomy-maritime-intelligence `internal/cvconsumer` (consumer-side
  verification reference for cv topics, same envelope contract).
