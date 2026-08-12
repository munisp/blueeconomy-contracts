# Contract Lifecycle

A contract is proposed with a clear producer, consumer, retention/classification decision and compatibility impact. It is validated by the repository’s descriptor build and by compatibility checks against the last approved release once a release baseline exists. Contract acceptance is distinct from external integration acceptance: a syntactically valid contract does not prove a partner endpoint is reachable or conformant.

Events carry immutable identifiers, correlation identifiers, classification and timestamps. Raw document payloads, source credentials, personal records, financial details and sensitive location information are not copied into event metadata merely for convenience. Consumers must be idempotent and preserve source-event provenance.
