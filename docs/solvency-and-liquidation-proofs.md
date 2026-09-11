# Solvency and liquidation proofs

- Margin sufficiency is computed from asset-registry initial/maintenance margin ratios.
- Under-margined intents are deterministically rejected at `MARGIN_INSUFFICIENT` before execution/state persistence; if a proof is provided, proof verification is still evaluated for liquidation-decision context.
- Proof verification returns standardized status and reason codes.
- If proof is absent or invalid for proof-required transitions, the workflow halts with `PROOF_FAILED`.
- Verified proofs are required before confidential transition persistence and settlement preparation.
- Under-margined paths evaluate liquidation with proof requirements (`PROOF_REQUIRED`, `PROOF_INVALID`, or `LIQUIDATION_TRIGGERED`) while still failing closed from execution/settlement.
