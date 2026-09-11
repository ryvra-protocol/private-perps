from __future__ import annotations

from private_perps.models import ProofVerificationResult, VerificationStatus


class ZKProofAdapter:
    """Adapter boundary for ZK/attestation proof verification."""

    def __init__(self, verifier_name: str = "zk-proof-adapter", accepted_proofs: set[str] | None = None):
        self.verifier_name = verifier_name
        self.accepted_proofs = accepted_proofs or set()

    def verify(self, *, proof_id: str, proof_type: str, commitment_hash: str) -> ProofVerificationResult:
        if proof_id in self.accepted_proofs:
            return ProofVerificationResult(
                proof_id=proof_id,
                verifier=self.verifier_name,
                status=VerificationStatus.VERIFIED,
                reason_code="PROOF_VERIFIED",
                metadata={"proof_type": proof_type, "commitment_hash": commitment_hash},
            )
        return ProofVerificationResult(
            proof_id=proof_id,
            verifier=self.verifier_name,
            status=VerificationStatus.REJECTED,
            reason_code="PROOF_INVALID",
            metadata={"proof_type": proof_type, "commitment_hash": commitment_hash},
        )
