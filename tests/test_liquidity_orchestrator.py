"""
Unit tests for intraday-liquidity-orchestrator.
Verifies velocity forecasting, time-to-depletion math, camt.050 message synthesis, and automated sweeping.
"""

import unittest
from intraday_liquidity_orchestrator.models import (
    SettlementRail,
    SettlementAccount,
)
from intraday_liquidity_orchestrator.velocity_forecaster import VelocityForecaster
from intraday_liquidity_orchestrator.camt050_liquidity_engine import Camt050LiquidityEngine
from intraday_liquidity_orchestrator.automated_sweep_controller import AutomatedSweepController
from intraday_liquidity_orchestrator.a2zsoc_liquidity_bridge import A2ZSOCLiquidityBridge

class TestIntradayLiquidityOrchestrator(unittest.TestCase):
    def setUp(self):
        self.forecaster = VelocityForecaster(critical_minutes_threshold=15.0)
        self.camt_engine = Camt050LiquidityEngine()
        self.controller = AutomatedSweepController(master_reserve_account="vault_res_01")
        self.bridge = A2ZSOCLiquidityBridge()

    def test_velocity_forecasting_depletion(self):
        account = SettlementAccount(
            account_id="acc_fednow",
            rail=SettlementRail.FEDNOW,
            current_balance=150000.0,
            safety_floor=100000.0,
            target_balance=500000.0
        )
        # Outflow = $60k/min = $1k/sec. Buffer = $50k. Seconds = 50s = 0.83 min
        outflows = [60000.0]
        inflows = [0.0]

        velocity = self.forecaster.calculate_velocity(account, outflows, inflows, window_seconds=60.0)
        self.assertEqual(velocity.outflow_rate_per_sec, 1000.0)
        self.assertLess(velocity.projected_depletion_minutes, 2.0)

    def test_camt050_xml_synthesis(self):
        xml = self.camt_engine.synthesize_camt050_message(
            instruction_id="instr_123",
            debtor_account="vault_source",
            creditor_account="fednow_target",
            amount=250000.0,
            currency="USD"
        )
        self.assertIn("<Document xmlns=\"urn:iso:std:iso:20022:tech:xsd:camt.050.001.05\">", xml)
        self.assertIn("<Amt Ccy=\"USD\">250000.00</Amt>", xml)
        self.assertIn("<InstrId>instr_123</InstrId>", xml)

    def test_automated_sweep_execution(self):
        account = SettlementAccount(
            account_id="acc_target",
            rail=SettlementRail.FEDNOW,
            current_balance=80000.0,  # Below safety floor ($100k)
            safety_floor=100000.0,
            target_balance=500000.0
        )
        velocity = self.forecaster.calculate_velocity(account, [1000.0], [0.0], window_seconds=60.0)

        sweep = self.controller.evaluate_and_sweep(account, velocity)
        self.assertIsNotNone(sweep)
        self.assertEqual(sweep.amount, 420000.0)
        self.assertEqual(account.current_balance, 500000.0)  # Restored to target

        # Attestation
        attestation = self.controller.get_treasury_attestation([account])
        self.assertGreater(attestation.surplus_liquidity, 0.0)

        seal = self.bridge.anchor_liquidity_attestation(sweep, attestation)
        self.assertTrue(seal.startswith("a2z_lqdty_seal_"))

if __name__ == "__main__":
    unittest.main()
