# Confidential data handling

Confidential by default:
- position size
- entry price
- leverage
- collateral
- liquidation threshold
- order parameters
- trading history

Handling model:
- Ciphertext storage for sensitive payloads
- Commitment hashes for tamper detection and deterministic referencing
- Authorization-gated decryption
- No plaintext-sensitive persistence by default
- Provenance fields preserved for intent/mandate/policy/risk/auth and proof linkage
