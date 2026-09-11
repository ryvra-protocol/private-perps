from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from private_perps.adapters.confidential_compute import ConfidentialComputeAdapter


@dataclass(frozen=True)
class EncryptedPositionVersion:
    position_id: str
    version_ref: str
    ciphertext: str
    commitment_hash: str
    authorization_id: str
    created_at: datetime


class EncryptedPositionStore:
    def __init__(self, compute_adapter: ConfidentialComputeAdapter):
        self._compute_adapter = compute_adapter
        self._versions: dict[str, list[EncryptedPositionVersion]] = {}

    @staticmethod
    def _canonical_payload(payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _commitment(payload_text: str) -> str:
        return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()

    def append_encrypted_version(
        self,
        *,
        position_id: str,
        payload: dict[str, Any],
        authorization_id: str,
    ) -> EncryptedPositionVersion:
        payload_text = self._canonical_payload(payload)
        commitment_hash = self._commitment(payload_text)
        ciphertext = self._compute_adapter.encrypt(payload_text)
        version_no = len(self._versions.get(position_id, [])) + 1
        version = EncryptedPositionVersion(
            position_id=position_id,
            version_ref=f"{position_id}:v{version_no}",
            ciphertext=ciphertext,
            commitment_hash=commitment_hash,
            authorization_id=authorization_id,
            created_at=datetime.now(timezone.utc),
        )
        self._versions.setdefault(position_id, []).append(version)
        return version

    def get_latest(self, position_id: str) -> EncryptedPositionVersion | None:
        versions = self._versions.get(position_id, [])
        return versions[-1] if versions else None

    def get_history(self, position_id: str) -> list[EncryptedPositionVersion]:
        return list(self._versions.get(position_id, []))

    def decrypt_version(self, version: EncryptedPositionVersion, authorization_id: str) -> dict[str, Any]:
        if not self._compute_adapter.is_authorized_to_decrypt(authorization_id, version.authorization_id):
            raise PermissionError("DECRYPTION_UNAUTHORIZED")
        payload_text = self._compute_adapter.decrypt(version.ciphertext)
        if self._commitment(payload_text) != version.commitment_hash:
            raise ValueError("COMMITMENT_MISMATCH")
        return json.loads(payload_text)
