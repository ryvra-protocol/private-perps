# Solvency and liquidation proofs

- Margin sufficiency is computed from asset-registry initial/maintenance margin ratios.
- Private liquidation requires proof context for insolvent accounts.
- Proof verification returns standardized status and reason codes.
- If proof is absent or invalid for proof-required transitions, the workflow halts with `PROOF_FAILED`.
- Verified proof enables deterministic `LIQUIDATION_TRIGGERED` decisions when margin is insufficient.
