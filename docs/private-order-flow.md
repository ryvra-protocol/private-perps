# Private order flow

1. `INTENT_RECEIVED`
2. `AUTHORITY_VALIDATED`
3. `MARGIN_VALIDATED`
4. `POSITION_RESERVED`
5. `ORDER_ACCEPTED`
6. `ORDER_MATCHED` / `EXECUTED`
7. `PROOF_GENERATED`
8. `PROOF_VERIFIED`
9. `SETTLEMENT_PREPARED`
10. `SETTLED`
11. `RECONCILED`

Failure states: `REJECTED`, `EXPIRED`, `PROOF_FAILED`, `ORACLE_INVALID`, `MARGIN_INSUFFICIENT`, `PARTIAL`, `DISPUTED`, `MANUAL_REVIEW`.

The gateway enforces fail-closed authority linkage (intent/mandate/policy/risk/authorization), privacy mode checks, policy hash matching, and deterministic oracle/margin/proof gates before settlement preparation.
