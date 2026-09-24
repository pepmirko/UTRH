# Reconstruct canonical UTRH Analysis Plan v1.2.3

The canonical preregistration bytes are archived under `freeze/payload/` as base64 parts.

```bash
cat freeze/payload/UTRH_Analysis_Plan_v1.2.3_PRE_FREEZE.md.b64.part* \
  | base64 -d \
  > UTRH_Analysis_Plan_v1.2.3_PRE_FREEZE.md

sha256sum UTRH_Analysis_Plan_v1.2.3_PRE_FREEZE.md
wc -c UTRH_Analysis_Plan_v1.2.3_PRE_FREEZE.md
```

Expected canonical output:

- SHA-256: `3b16f919ed3792d70266585d1b627793a074edb39fb8a187576d32fb04e80ffd`
- bytes: `86403`

The freeze is valid only if reconstruction matches both values. The source-basis and theoretical-baseline artifacts marked `HASH_ONLY` in the manifest are identified by exact SHA-256 and byte count rather than duplicated into this repository.
