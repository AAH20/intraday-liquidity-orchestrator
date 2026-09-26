"""
Command Line Interface for intraday-liquidity-orchestrator.
Executes real-time liquidity velocity forecasting and ISO 20022 camt.050 sweep sprints.
"""

import argparse
import sys
import time
from .models import SettlementRail, SettlementAccount
from .velocity_forecaster import VelocityForecaster
from .automated_sweep_controller import AutomatedSweepController
from .a2zsoc_liquidity_bridge import A2ZSOCLiquidityBridge

def run_demo():
    print("=" * 80)
    print("🌊 INTRADAY-LIQUIDITY-ORCHESTRATOR v1.0.0 (Frontier September 2026)")
    print("    24/7/365 Real-Time Rail Treasury Balancing Engine & ISO 20022 camt.050 Sweeper")
    print("    Integrated with a2zsoc.com Evidence Vault & Basel BCBS 248 Attestation")
    print("=" * 80)

    forecaster = VelocityForecaster(critical_minutes_threshold=15.0)
    controller = AutomatedSweepController(master_reserve_account="apex_master_treasury_vault")
    bridge = A2ZSOCLiquidityBridge()

    print("\n[1/4] Monitoring Live Real-Time Pre-Funded Settlement Accounts...")
    fednow_account = SettlementAccount(
        account_id="fednow_clearing_enclave_01",
        rail=SettlementRail.FEDNOW,
        currency="USD",
        current_balance=120000.00,
        safety_floor=100000.00,
        target_balance=500000.00
    )
    print(f"   • Account ID:              {fednow_account.account_id}")
    print(f"   • Settlement Rail:         {fednow_account.rail.value} (Instant 24/7/365 Gross Settlement)")
    print(f"   • Current Live Balance:    ${fednow_account.current_balance:,.2f} USD")
    print(f"   • Safety Reserve Floor:    ${fednow_account.safety_floor:,.2f} USD")
    print(f"   • Target Buffer:           ${fednow_account.target_balance:,.2f} USD")

    print("\n[2/4] Simulating Autonomous Agent Purchasing Surge (Weekend 03:00 AM)...")
    # High outflow over 60 seconds
    outflows = [15000.0, 8500.0, 22000.0, 11000.0, 9500.0, 14000.0]  # $80,000 in 60s
    inflows = [5000.0, 3000.0]  # $8,000 inflow
    velocity = forecaster.calculate_velocity(fednow_account, outflows, inflows, window_seconds=60.0)

    print(f"   • Gross Outflow Velocity:  ${velocity.outflow_rate_per_sec:,.2f} USD / second")
    print(f"   • Net Burn Rate:           ${velocity.net_burn_rate_per_sec:,.2f} USD / second")
    print(f"   • Projected Depletion:     {velocity.projected_depletion_minutes} minutes remaining until floor breach!")

    print("\n[3/4] Triggering Automated ISO 20022 camt.050 Liquidity Sweep...")
    sweep = controller.evaluate_and_sweep(fednow_account, velocity)

    if sweep:
        print(f"   🚨 CRITICAL DEPLETION PREVENTED! Executing Automated Sweep...")
        print(f"   ✓ Sweep Instruction ID:    {sweep.sweep_id}")
        print(f"   ✓ Debtor (Source):         {sweep.source_account}")
        print(f"   ✓ Creditor (Target):       {sweep.target_account}")
        print(f"   ✓ Transferred Amount:      ${sweep.amount:,.2f} USD")
        print(f"   ✓ Message Format:          ISO 20022 camt.050.001.05 LiquidityCreditTransfer")
        print(f"   ✓ Restored Balance:        ${fednow_account.current_balance:,.2f} USD (Back at Target)")

    print("\n[4/4] Generating Basel BCBS 248 Attestation & Sealing to a2zsoc.com...")
    attestation = controller.get_treasury_attestation([fednow_account])
    seal = bridge.anchor_liquidity_attestation(sweep, attestation)
    print(f"   ✓ Total Liquidity Reserve: ${attestation.total_liquidity_reserve:,.2f} USD")
    print(f"   ✓ Mandatory Floor:         ${attestation.mandatory_reserve_floor:,.2f} USD")
    print(f"   ✓ Net Surplus:             ${attestation.surplus_liquidity:,.2f} USD")
    print(f"   ✓ a2zsoc.com Seal:         {seal}")
    print(f"   ✓ Mapped Frameworks:       Basel BCBS 248, Fed Reg D, ECB TARGET2")

    print("\n" + "=" * 80)
    print("✅ INTRADAY LIQUIDITY SPRINT COMPLETED: Zero Central Bank Overdraft Penalties.")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="24/7 Intraday Liquidity Orchestrator")
    parser.add_argument("--demo", action="store_true", help="Run end-to-end liquidity sweep simulation")
    args = parser.parse_args()

    if args.demo or len(sys.argv) == 1:
        run_demo()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
