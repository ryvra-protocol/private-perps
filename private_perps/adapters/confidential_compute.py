from __future__ import annotations

import base64
from dataclasses import dataclass


class ConfidentialComputeAdapter:
    """Provider-agnostic interface backed by private-execution providers."""

    def encrypt(self, plaintext: str) -> str:
        raise NotImplementedError

    def decrypt(self, ciphertext: str) -> str:
        raise NotImplementedError

    def is_authorized_to_decrypt(self, authorization_id: str, expected_authorization_id: str) -> bool:
        raise NotImplementedError


@dataclass
class InMemoryPrivateExecutionAdapter(ConfidentialComputeAdapter):
    provider: str = "private-execution:in-memory"

    def encrypt(self, plaintext: str) -> str:
        encoded = base64.b64encode(plaintext.encode("utf-8")).decode("ascii")
        return f"{self.provider}:{encoded}"

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext.startswith(f"{self.provider}:"):
            raise ValueError("CIPHERTEXT_PROVIDER_MISMATCH")
        encoded = ciphertext.split(":", 1)[1]
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")

    def is_authorized_to_decrypt(self, authorization_id: str, expected_authorization_id: str) -> bool:
        return authorization_id == expected_authorization_id
