# Solvency and liquidation proofs

- Margin sufficiency is computed from asset-registry initial/maintenance margin ratios.
- Under-margined intents are deterministically rejected at `MARGIN_INSUFFICIENT` before execution/state persistence.
- Proof verification returns standardized status and reason codes.
- If proof is absent or invalid for proof-required transitions, the workflow halts with `PROOF_FAILED`.
- Verified proofs are required before confidential transition persistence and settlement preparation.
- In the current scaffold, liquidation evaluation is reached only after margin-valid paths, and under-margined paths are fail-closed earlier.
