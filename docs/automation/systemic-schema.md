<!-- markdownlint-disable MD013 -->
# Systemic Schema Reference

**Status:** Living  
**Purpose:** Define neutral JSON Schemas and validation guidance for systemic metadata and receipt envelopes.

Use this reference when integrating TEOF’s S/L lattice into external tooling, pipelines, or mixed-language stacks.

---

## 1. Schemas

| Artifact | Path | Description |
| --- | --- | --- |
| Systemic metadata | `schemas/systemic/metadata.schema.json` | Minimal fields describing systemic_targets, layer_targets, systemic_scale, and primary layer. |
| Receipt envelope | `schemas/systemic/receipt.schema.json` | Signature-friendly wrapper that embeds systemic metadata alongside artifact hashes. |
| Sample payload | `docs/examples/systemic/receipt.sample.json` | End-to-end example with optional signature fields. |

Schemas follow JSON Schema draft 2020-12. They intentionally allow additional properties so organizations can extend the envelope without breaking validation.

---

## 2. Required fields

### systemic metadata

| Field | Type | Description |
| --- | --- | --- |
| `systemic_targets` | array of `S#` tokens | Sorted list of systemic axes advanced by the work. |
| `layer_targets` | array of `L#` tokens | Ordered list of layers touched (primary first). |
| `systemic_scale` | integer (1–10) | Highest axis that must be satisfied before deployment. |
| `layer` | `L#` token | Primary operating layer. |

Optional but recommended: `schema_version`, `summary`, `receipts`, `references`, `created_at`, `updated_at`.

### receipt envelope

| Field | Type | Description |
| --- | --- | --- |
| `artifact` | string (URI) | Pointer to the artifact (file, object storage, etc.). |
| `hash_sha256` | hex string | SHA-256 hash of the artifact to ensure integrity. |
| `issued_at` | ISO-8601 | UTC timestamp when the receipt was generated. |
| `systemic` | object | Embedded systemic metadata (must conform to the metadata schema). |

Optional fields include `schema_version`, `expires_at`, `meta`, and signature fields (`signature`, `public_key_id`, `signature_algorithm`).

---

## 3. Validation workflow

1. **Load schema**  
   ```python
   import json
   from pathlib import Path

   schema = json.loads(Path("schemas/systemic/receipt.schema.json").read_text())
   metadata_schema = json.loads(Path("schemas/systemic/metadata.schema.json").read_text())
   ```

2. **Register `$id` references**  
   Many JSON Schema validators (e.g., `jsonschema`, `ajv`) let you preload both schemas so the receipt schema can resolve the metadata schema by `$id`.

3. **Validate payload**  
   ```python
   from jsonschema import Draft202012Validator

   resolver = Draft202012Validator(schema, types={"object": dict})
   resolver.validate(payload)
   ```

   Replace `jsonschema` with your validator of choice. The schema only relies on base draft-2020-12 features (types, patterns, required fields).

4. **Verify signature (optional)**  
   Receipts may include an Ed25519 signature covering the JSON with the `signature` field omitted during signing. Use a compatible library (PyNaCl, libsodium bindings, WebCrypto) and supply the registered public key.

---

## 4. Signature convention

1. Serialize the receipt as UTF-8 with stable key ordering (e.g., `json.dumps(payload, separators=(",", ":"), sort_keys=True)`).
2. Exclude the `signature` field from the serialization before signing.
3. Produce a base64url-encoded Ed25519 signature.  
4. Store the public key identifier under `public_key_id`; register the actual key in your governance anchors or equivalent append-only log.

Organizations may adopt alternative algorithms by setting `signature_algorithm` accordingly, but Ed25519 is the TEOF default.

---

## 5. Integration tips

- **Language support:** Most languages have mature JSON Schema validators. Preload both schemas so clients can validate nested systemic metadata.
- **Backward compatibility:** Include `schema_version` to manage field changes. When bumping versions, update the `$id` to keep old payloads valid.
- **Streaming receipts:** When generating receipts from CI pipelines, write the envelope to your preferred storage and capture the hash of the envelope itself for audit trails.
- **S/L discipline:** Validation only ensures structural correctness. Uphold the constitutional ordering separately (e.g., checking that `systemic_scale` exists in `systemic_targets`, that higher axes are satisfied before lower ones escalate).

---

## 6. Roadmap

The interoperability plan (`2025-10-17-systemic-interoperability`) tracks future enhancements:

- Language-specific adapter snippets (TypeScript, Go).
- JSON Schema test suite covering edge cases (empty arrays, invalid tokens).
- Optional REST/gRPC contract for serving systemic receipts.

Contributions should include receipts demonstrating validation in the target language/environment.
