"""
Automated Liquidity Sweep Controller.
Evaluates velocity vectors, triggers ISO 20022 camt.050 sweeps, and replenishes pre-funded settlement accounts.
"""

from typing import List, Optional
import uuid
import time
from .models import (
    SettlementAccount,
    VelocityVector,
    LiquiditySweepInstruction,
    TreasuryParityAttestation,
)
from .camt050_liquidity_engine import Camt050LiquidityEngine

class AutomatedSweepController:
    def __init__(self, master_reserve_account: str = "master_treasury_vault"):
        self.master_reserve = master_reserve_account
        self.camt_engine = Camt050LiquidityEngine()
        self.sweep_history: List[LiquiditySweepInstruction] = []

    def evaluate_and_sweep(
        self,
        account: SettlementAccount,
        velocity: VelocityVector
    ) -> Optional[LiquiditySweepInstruction]:
        """
        Determines whether a liquidity sweep is required.
        Triggers sweep if balance < safety floor OR projected depletion < 15 minutes.
        """
        requires_sweep = account.is_below_floor or velocity.projected_depletion_minutes <= 15.0

        if not requires_sweep:
            return None

        sweep_amount = account.required_topup
        sweep_id = f"swp_{uuid.uuid4().hex[:12]}"

        # Synthesize camt.050 XML instruction
        camt_xml = self.camt_engine.synthesize_camt050_message(
            instruction_id=sweep_id,
            debtor_account=self.master_reserve,
            creditor_account=account.account_id,
            amount=sweep_amount,
            currency=account.currency
        )

        instruction = LiquiditySweepInstruction(
            sweep_id=sweep_id,
            source_account=self.master_reserve,
            target_account=account.account_id,
            amount=sweep_amount,
            rail=account.rail,
            trigger_reason=f"Velocity depletion in {velocity.projected_depletion_minutes}m (Floor: ${account.safety_floor:,.2f})",
            camt050_message_ref=sweep_id,
            executed=True,
            executed_at=time.time()
        )

        # Replenish balance atomically
        account.current_balance += sweep_amount
        self.sweep_history.append(instruction)
        return instruction

    def get_treasury_attestation(self, accounts: List[SettlementAccount]) -> TreasuryParityAttestation:
        total_balance = sum(a.current_balance for a in accounts)
        total_floors = sum(a.safety_floor for a in accounts)
        surplus = total_balance - total_floors

        return TreasuryParityAttestation(
            attestation_id=f"treasury_att_{uuid.uuid4().hex[:10]}",
            total_liquidity_reserve=total_balance,
            mandatory_reserve_floor=total_floors,
            surplus_liquidity=surplus,
            active_sweep_count=len(self.sweep_history),
            timestamp=time.time()
        )
