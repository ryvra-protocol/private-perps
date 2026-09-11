# Private order flow

1. `INTENT_RECEIVED`
2. `AUTHORITY_VALIDATED`
3. `MARGIN_VALIDATED`
4. `PROOF_GENERATED`
5. `PROOF_VERIFIED`
6. `POSITION_RESERVED`
7. `ORDER_ACCEPTED`
8. `ORDER_MATCHED` / `EXECUTED`
9. `SETTLEMENT_PREPARED`
10. `SETTLED`
11. `RECONCILED`

Failure states: `REJECTED`, `EXPIRED`, `PROOF_FAILED`, `ORACLE_INVALID`, `MARGIN_INSUFFICIENT`, `PARTIAL`, `DISPUTED`, `MANUAL_REVIEW`.

The gateway enforces fail-closed authority linkage (intent/mandate/policy/risk/authorization), confidential-mode checks, policy hash matching, and deterministic oracle/margin/proof gates before settlement preparation.
