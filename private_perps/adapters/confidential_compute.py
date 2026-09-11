from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import secrets


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
    secret_key: str = "phase9-local-confidential-key"

    def _keystream(self, nonce: bytes, length: int) -> bytes:
        key = self.secret_key.encode("utf-8")
        out = bytearray()
        counter = 0
        while len(out) < length:
            block = hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest()
            out.extend(block)
            counter += 1
        return bytes(out[:length])

    def encrypt(self, plaintext: str) -> str:
        data = plaintext.encode("utf-8")
        nonce = secrets.token_bytes(16)
        keystream = self._keystream(nonce, len(data))
        encrypted = bytes(a ^ b for a, b in zip(data, keystream))
        payload = base64.b64encode(nonce + encrypted).decode("ascii")
        return f"{self.provider}:{payload}"

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext.startswith(f"{self.provider}:"):
            raise ValueError("CIPHERTEXT_PROVIDER_MISMATCH")
        encoded = ciphertext.split(":", 1)[1]
        payload = base64.b64decode(encoded.encode("ascii"))
        if len(payload) < 16:
            raise ValueError("CIPHERTEXT_INVALID")
        nonce, encrypted = payload[:16], payload[16:]
        keystream = self._keystream(nonce, len(encrypted))
        data = bytes(a ^ b for a, b in zip(encrypted, keystream))
        return data.decode("utf-8")

    def is_authorized_to_decrypt(self, authorization_id: str, expected_authorization_id: str) -> bool:
        return authorization_id == expected_authorization_id
