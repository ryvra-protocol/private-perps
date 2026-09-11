# private-perps

Phase 9 implements confidential perpetual market scaffolding aligned to RFC-0012 and RFC-0013.

## Architecture and boundaries

Core module components:
- Private Order Gateway: validates authority linkage and fail-closed policy checks, then routes through margin, position, funding, proof, and settlement steps.
- Encrypted Position Store: ciphertext-only position versions with deterministic commitment hashes.
- Position Engine: confidential open/adjust processing and committed transition output.
- Margin Engine: collateral checks using asset-registry metadata and deterministic risk flags.
- Funding Engine: funding delta computation boundary.
- Liquidation Engine (private): proof-gated liquidation trigger decision.
- Oracle Adapter: deterministic confidence/staleness/fallback gates.
- ZK Proof Adapter: standardized proof verification result/reason model.
- Confidential Compute Adapter: provider-agnostic private-execution interface.
- Settlement Adapter: settlement-ready records with provenance refs for ledger-settlement handoff.

## Confidential state model

Sensitive fields are confidential by default (size, entry price, leverage, collateral, liquidation threshold, order parameters, history).
At rest, position/order payloads are stored as ciphertext plus commitments. Plaintext-sensitive storage is not the default model.

## Proof verification and liquidation flow

1. Intent received and authority refs validated.
2. Oracle observation validated.
3. Margin validated.
4. Proof required transitions block until proof is provided and verified.
5. Position transition persisted as encrypted version with commitment.
6. Liquidation decision uses margin status and proof verification status.
7. Settlement-prepared record emitted with intent/proof/commitment provenance and funding-adjusted delta.

## Integration points

- `private-execution`: confidential compute adapter interface in `private_perps/adapters/confidential_compute.py`
- `asset-registry`: collateral metadata adapter in `private_perps/adapters/asset_registry.py`
- `ledger-settlement`: settlement handoff adapter in `private_perps/adapters/settlement.py`
- Authority decisions are fail-closed and do not bypass gateway policy/risk/authorization linkage.

## RFC mapping

- RFC-0012: confidential perps lifecycle and authority/intent linkage
- RFC-0013: confidential storage, proof verification, and deterministic boundary enforcement
- Dependencies: private execution abstraction, oracle policy metadata, settlement provenance compatibility

## Docs

- `docs/private-order-flow.md`
- `docs/solvency-and-liquidation-proofs.md`
- `docs/confidential-data-handling.md`
