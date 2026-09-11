from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
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
    secret_key: str | None = None

    def _keystream(self, nonce: bytes, length: int) -> bytes:
        if not self.secret_key:
            raise ValueError("MISSING_CONFIDENTIAL_COMPUTE_KEY")
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
        if not self.secret_key:
            raise ValueError("MISSING_CONFIDENTIAL_COMPUTE_KEY")
        key = self.secret_key.encode("utf-8")
        mac = hmac.new(key, nonce + encrypted, hashlib.sha256).digest()
        payload = base64.b64encode(nonce + encrypted + mac).decode("ascii")
        return f"{self.provider}:{payload}"

    def decrypt(self, ciphertext: str) -> str:
        prefix = f"{self.provider}:"
        if not ciphertext.startswith(prefix):
            raise ValueError("CIPHERTEXT_PROVIDER_MISMATCH")
        encoded = ciphertext[len(prefix):]
        payload = base64.b64decode(encoded.encode("ascii"))
        if len(payload) < 48:
            raise ValueError("CIPHERTEXT_INVALID")
        nonce = payload[:16]
        mac = payload[-32:]
        encrypted = payload[16:-32]
        if not self.secret_key:
            raise ValueError("MISSING_CONFIDENTIAL_COMPUTE_KEY")
        key = self.secret_key.encode("utf-8")
        expected_mac = hmac.new(key, nonce + encrypted, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("CIPHERTEXT_AUTH_FAILED")
        keystream = self._keystream(nonce, len(encrypted))
        data = bytes(a ^ b for a, b in zip(encrypted, keystream))
        return data.decode("utf-8")

    def is_authorized_to_decrypt(self, authorization_id: str, expected_authorization_id: str) -> bool:
        return hmac.compare_digest(authorization_id, expected_authorization_id)
