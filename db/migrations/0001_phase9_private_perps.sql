-- Phase 9 confidential perps schema (additive)

CREATE TABLE IF NOT EXISTS trading_accounts (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL UNIQUE,
  owner_actor_id TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS private_positions (
  id TEXT PRIMARY KEY,
  position_id TEXT NOT NULL UNIQUE,
  account_id TEXT NOT NULL,
  encrypted_payload_ref TEXT,
  encrypted_payload_ciphertext TEXT NOT NULL,
  commitment_hash TEXT NOT NULL,
  authority_intent_id TEXT NOT NULL,
  authority_mandate_id TEXT NOT NULL,
  authority_risk_assessment_id TEXT NOT NULL,
  authority_authorization_id TEXT NOT NULL,
  authority_policy_version TEXT NOT NULL,
  authority_policy_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  settlement_ref TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS private_orders (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL UNIQUE,
  account_id TEXT NOT NULL,
  intent_id TEXT NOT NULL,
  mandate_id TEXT NOT NULL,
  risk_assessment_id TEXT NOT NULL,
  authorization_id TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  policy_hash TEXT NOT NULL,
  privacy_mode TEXT NOT NULL,
  execution_mode TEXT NOT NULL,
  encrypted_order_payload_ref TEXT,
  encrypted_order_payload_ciphertext TEXT NOT NULL,
  commitment_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  settlement_ref TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS position_state_versions (
  id TEXT PRIMARY KEY,
  position_id TEXT NOT NULL,
  version_ref TEXT NOT NULL UNIQUE,
  encrypted_payload_ref TEXT,
  encrypted_payload_ciphertext TEXT NOT NULL,
  commitment_hash TEXT NOT NULL,
  proof_ref TEXT,
  verifier_status TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS position_proofs (
  id TEXT PRIMARY KEY,
  proof_id TEXT NOT NULL UNIQUE,
  position_id TEXT,
  order_id TEXT,
  proof_ref TEXT,
  verifier_name TEXT,
  verifier_status TEXT NOT NULL,
  reason_code TEXT,
  commitment_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS liquidation_proofs (
  id TEXT PRIMARY KEY,
  proof_id TEXT NOT NULL UNIQUE,
  position_id TEXT,
  order_id TEXT,
  proof_ref TEXT,
  verifier_name TEXT,
  verifier_status TEXT NOT NULL,
  reason_code TEXT,
  commitment_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oracle_observations (
  id TEXT PRIMARY KEY,
  oracle_id TEXT NOT NULL,
  market TEXT NOT NULL,
  source TEXT NOT NULL,
  fallback_used INTEGER NOT NULL DEFAULT 0,
  confidence REAL NOT NULL,
  min_confidence REAL NOT NULL,
  staleness_ms INTEGER NOT NULL,
  max_staleness_ms INTEGER NOT NULL,
  commitment_hash TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trading_accounts_account_id ON trading_accounts(account_id);
CREATE INDEX IF NOT EXISTS idx_private_orders_account_id ON private_orders(account_id);
CREATE INDEX IF NOT EXISTS idx_private_orders_intent_id ON private_orders(intent_id);
CREATE INDEX IF NOT EXISTS idx_private_orders_mandate_id ON private_orders(mandate_id);
CREATE INDEX IF NOT EXISTS idx_private_positions_account_id ON private_positions(account_id);
CREATE INDEX IF NOT EXISTS idx_private_positions_position_id ON private_positions(position_id);
CREATE INDEX IF NOT EXISTS idx_position_state_versions_position_id ON position_state_versions(position_id);
CREATE INDEX IF NOT EXISTS idx_private_orders_order_id ON private_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_position_proofs_proof_id ON position_proofs(proof_id);
CREATE INDEX IF NOT EXISTS idx_liquidation_proofs_proof_id ON liquidation_proofs(proof_id);
CREATE INDEX IF NOT EXISTS idx_private_orders_created_at ON private_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_private_positions_created_at ON private_positions(created_at);
CREATE INDEX IF NOT EXISTS idx_oracle_observations_created_at ON oracle_observations(created_at);
