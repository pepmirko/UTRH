# Payload integrity note — v1.2.3

The canonical scientific object is the decoded analysis plan, not the textual wrapping of individual base64 chunks.

Required reconstruction identity:

- canonical filename: `UTRH_Analysis_Plan_v1.2.3_PRE_FREEZE.md`
- SHA-256: `3b16f919ed3792d70266585d1b627793a074edb39fb8a187576d32fb04e80ffd`
- byte count: `86403`

Chunk whitespace (including trailing newlines) is not scientifically meaningful because it is ignored by base64 decoding. Before the freeze marker commit, the decoded bytes are verified against the canonical SHA-256 and byte count above. Any chunk-content discrepancy that changes decoded bytes must be corrected before freeze.
