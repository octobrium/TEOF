# TEOF v1.5 — Provenance (Immutable Capsule Freeze)

**Date (UTC):** YYYY-MM-DD  
**Branch:** main

## Canonical Artifacts (SHA-256)
- `capsule/v1.5/capsule-mini.txt`  
  `14832af97ac719244a36d2191dde79116bbced775ec0d091bf446650a5a81e94`
- `capsule/v1.5/capsule-handshake.txt`  
  `5c5e5a2cd8cdfe49a472c35a77bd5ebfa293275f5a808f8e19e3f24932a81bb1`
- `capsule/v1.5/capsule-selfreconstructing.txt`  
  `cbe147a6104fb4daea18087bdcbf1788cfa62c15eb5ea64384b9c5fc1f3a8ad9`

## Verify locally
**macOS/Linux**
```bash
shasum -a 256 capsule/v1.5/capsule-*.txt
```

**Windows PowerShell**
```powershell
Get-FileHash capsule/v1.5/capsule-*.txt -Algorithm SHA256
```

Hashes must match the values above.

## Scope & Policy
- This freeze covers doctrinal immutables (Primacy, Axioms 1–5+X, Ethic, Precedence) and the operational guardrails embedded in the capsule.
- Any content change beyond formatting requires a version bump (e.g., v1.6).
- **Order of trust:** Content tests > Provenance > Commentary.
