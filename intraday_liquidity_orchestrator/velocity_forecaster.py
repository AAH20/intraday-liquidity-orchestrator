"""
Velocity Forecaster & Liquidity Depletion Curve Calculator.
Calculates real-time burn rates across 24/7/365 instant gross settlement rails.
"""

from typing import Dict, List
import time
from .models import SettlementAccount, VelocityVector

class VelocityForecaster:
    def __init__(self, critical_minutes_threshold: float = 15.0):
        self.critical_threshold = critical_minutes_threshold

    def calculate_velocity(
        self,
        account: SettlementAccount,
        recent_outflows: List[float],
        recent_inflows: List[float],
        window_seconds: float = 60.0
    ) -> VelocityVector:
        """
        Calculates burn rates and estimates time-to-depletion.
        """
        total_out = sum(recent_outflows)
        total_in = sum(recent_inflows)

        out_rate = total_out / window_seconds
        in_rate = total_in / window_seconds
        net_burn = out_rate - in_rate

        if net_burn > 0:
            usable_buffer = max(0.0, account.current_balance - account.safety_floor)
            seconds_left = usable_buffer / net_burn
            minutes_left = seconds_left / 60.0
        else:
            minutes_left = 9999.0  # Safe / Inflow exceeds outflow

        return VelocityVector(
            account_id=account.account_id,
            outflow_rate_per_sec=round(out_rate, 2),
            inflow_rate_per_sec=round(in_rate, 2),
            net_burn_rate_per_sec=round(net_burn, 2),
            projected_depletion_minutes=round(minutes_left, 1),
            calculated_at=time.time()
        )
