"""
Data models for intraday-liquidity-orchestrator.
Represents real-time settlement balances, velocity depletion curves, and ISO 20022 camt.050 sweeps.
Uses pure standard library dataclasses for zero-dependency portability.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import time
import hashlib

class SettlementRail(str, Enum):
    FEDNOW = "FEDNOW"
    SEPA_INSTANT = "SEPA_INSTANT"
    FAWRY_RETAIL_MENA = "FAWRY_RETAIL_MENA"
    PAYMOB_OMNICHANNEL = "PAYMOB_OMNICHANNEL"
    SWIFT_GPI_INSTANT = "SWIFT_GPI_INSTANT"

@dataclass
class SettlementAccount:
    account_id: str
    rail: SettlementRail
    currency: str = "USD"
    current_balance: float = 0.0
    safety_floor: float = 100000.0  # Dynamic minimum balance
    target_balance: float = 500000.0
    last_updated: float = field(default_factory=time.time)

    @property
    def is_below_floor(self) -> bool:
        return self.current_balance < self.safety_floor

    @property
    def required_topup(self) -> float:
        return max(0.0, self.target_balance - self.current_balance)

@dataclass
class VelocityVector:
    account_id: str
    outflow_rate_per_sec: float  # $ / second
    inflow_rate_per_sec: float
    net_burn_rate_per_sec: float
    projected_depletion_minutes: float  # Minutes until safety floor breach
    calculated_at: float = field(default_factory=time.time)

@dataclass
class LiquiditySweepInstruction:
    sweep_id: str
    source_account: str
    target_account: str
    amount: float
    rail: SettlementRail
    trigger_reason: str
    camt050_message_ref: str
    executed: bool = True
    executed_at: float = field(default_factory=time.time)

    def compute_sha256_hash(self) -> str:
        payload = f"{self.sweep_id}:{self.source_account}:{self.target_account}:{self.amount}:{self.executed_at}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

@dataclass
class TreasuryParityAttestation:
    attestation_id: str
    total_liquidity_reserve: float
    mandatory_reserve_floor: float
    surplus_liquidity: float
    active_sweep_count: int
    a2zsoc_seal: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
