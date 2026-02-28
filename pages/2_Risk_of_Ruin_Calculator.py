# -*- coding: utf-8 -*-
import random
from typing import Optional, Tuple

import streamlit as st


st.set_page_config(page_title="Risk of Ruin Calculator", layout="centered")

st.title("Risk of Ruin Calculator")
st.caption("Estimate the chance of violating prop-firm drawdown rules via Monte Carlo simulation.")

st.markdown(
    """
This simulator models many possible equity paths using your trading profile.

A run is marked as **ruined** if it breaches either:
- **Daily drawdown limit** (relative to the day's starting balance), or
- **Overall drawdown limit** (relative to the account's starting balance).
"""
)

# -----------------------------
# Challenge type + presets
# -----------------------------
challenge_type = st.radio(
    "Challenge Type",
    options=["1-Phase Challenge", "2-Phase Challenge"],
    horizontal=True,
    key="challenge_type",
)

preset_targets = {
    "1-Phase Challenge": {"phase_1": 8.0, "phase_2": 0.0},
    "2-Phase Challenge": {"phase_1": 8.0, "phase_2": 5.0},
}

use_presets = st.toggle("Use default target presets", value=True, key="use_presets_toggle")
selected_preset = preset_targets[challenge_type]

st.markdown("### Account & Risk Profile")
col1, col2, col3 = st.columns(3)

with col1:
    starting_balance = st.number_input(
        "Starting Balance ($)",
        min_value=1000,
        value=100000,
        step=1000,
        key="starting_balance",
    )
    daily_drawdown_pct = st.number_input(
        "Daily Drawdown Limit (%)",
        min_value=0.1,
        max_value=20.0,
        value=5.0,
        step=0.1,
        key="daily_drawdown_pct",
    )

with col2:
    overall_drawdown_pct = st.number_input(
        "Overall Drawdown Limit (%)",
        min_value=0.1,
        max_value=30.0,
        value=10.0,
        step=0.1,
        key="overall_drawdown_pct",
    )
    risk_per_trade_pct = st.number_input(
        "Risk Per Trade (% of balance)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
        key="risk_per_trade_pct",
    )

with col3:
    win_rate_pct = st.number_input(
        "Win Rate (%)",
        min_value=1.0,
        max_value=99.0,
        value=50.0,
        step=1.0,
        key="win_rate_pct",
    )
    reward_risk = st.number_input(
        "Average Reward/Risk (R)",
        min_value=0.1,
        max_value=10.0,
        value=1.5,
        step=0.1,
        key="reward_risk",
    )

st.markdown("### Challenge Targets & Simulation")
tcol1, tcol2 = st.columns(2)

with tcol1:
    target_phase_1_pct = st.number_input(
        "Phase 1 Target Profit (%)",
        min_value=0.1,
        max_value=100.0,
        value=float(selected_preset["phase_1"]) if use_presets else 8.0,
        step=0.1,
        key="target_phase_1_pct",
    )

with tcol2:
    if challenge_type == "2-Phase Challenge":
        target_phase_2_pct = st.number_input(
            "Phase 2 Target Profit (%)",
            min_value=0.1,
            max_value=100.0,
            value=float(selected_preset["phase_2"]) if use_presets else 5.0,
            step=0.1,
            key="target_phase_2_pct",
        )
    else:
        target_phase_2_pct = 0.0
        st.caption("Phase 2 is not used in 1-Phase mode.")

scol1, scol2, scol3 = st.columns(3)
with scol1:
    trades_per_day = st.number_input(
        "Trades Per Day",
        min_value=1,
        max_value=20,
        value=3,
        step=1,
        key="trades_per_day",
    )
with scol2:
    max_days_per_phase = st.slider(
        "Max Trading Days (per phase)",
        min_value=5,
        max_value=180,
        value=30,
        key="max_days_per_phase",
    )
with scol3:
    simulation_runs = st.slider(
        "Simulation Runs",
        min_value=100,
        max_value=10000,
        value=2000,
        step=100,
        key="simulation_runs",
    )


def simulate_phase(
    target_profit_pct: float,
    initial_balance: float,
    *,
    daily_dd_pct: float,
    overall_dd_pct: float,
    win_rate: float,
    rr: float,
    risk_pct: float,
    trades_day: int,
    max_days: int,
) -> Tuple[bool, bool, float, int, Optional[int]]:
    """Return: (ruined, passed, final_balance, days_used, days_to_pass_if_passed)."""
    balance = float(initial_balance)
    target_balance = initial_balance * (1.0 + target_profit_pct / 100.0)
    overall_floor = initial_balance * (1.0 - overall_dd_pct / 100.0)

    win_prob = win_rate / 100.0
    risk_fraction = risk_pct / 100.0

    for day in range(1, int(max_days) + 1):
        day_start_balance = balance
        daily_floor = day_start_balance * (1.0 - daily_dd_pct / 100.0)

        for _ in range(int(trades_day)):
            risk_amount = balance * risk_fraction
            pnl = (risk_amount * rr) if (random.random() <= win_prob) else (-risk_amount)
            balance += pnl

            if balance <= overall_floor or balance <= daily_floor:
                return True, False, balance, day, None

            if balance >= target_balance:
                return False, True, balance, day, day

    return False, False, balance, int(max_days), None


def simulate_challenge() -> Tuple[bool, bool, bool, float, Optional[int]]:
    """Return: (ruined, passed, reached_phase_2, final_balance, days_to_pass)."""
    initial = float(starting_balance)

    ruined, passed_p1, bal_after_p1, days_used_p1, days_to_pass_p1 = simulate_phase(
        target_phase_1_pct,
        initial,
        daily_dd_pct=float(daily_drawdown_pct),
        overall_dd_pct=float(overall_drawdown_pct),
        win_rate=float(win_rate_pct),
        rr=float(reward_risk),
        risk_pct=float(risk_per_trade_pct),
        trades_day=int(trades_per_day),
        max_days=int(max_days_per_phase),
    )

    if ruined:
        return True, False, False, bal_after_p1, None
    if not passed_p1:
        return False, False, False, bal_after_p1, None

    if challenge_type == "1-Phase Challenge":
        return False, True, False, bal_after_p1, days_to_pass_p1

    # Phase 2
    ruined, passed_p2, bal_after_p2, days_used_p2, days_to_pass_p2 = simulate_phase(
        target_phase_2_pct,
        float(bal_after_p1),
        daily_dd_pct=float(daily_drawdown_pct),
        overall_dd_pct=float(overall_drawdown_pct),
        win_rate=float(win_rate_pct),
        rr=float(reward_risk),
        risk_pct=float(risk_per_trade_pct),
        trades_day=int(trades_per_day),
        max_days=int(max_days_per_phase),
    )

    if ruined:
        return True, False, True, bal_after_p2, None
    if passed_p2:
        total_days = int(days_used_p1) + int(days_used_p2)
        return False, True, True, bal_after_p2, total_days

    return False, False, True, bal_after_p2, None


if st.button("Run Simulation", type="primary", key="run_sim_btn"):
    ruined_count = 0
    passed_count = 0
    reached_phase_2_count = 0
    ending_balances = []
    pass_days = []

    for _ in range(int(simulation_runs)):
        ruined, passed, reached_phase_2, final_balance, days_to_pass = simulate_challenge()
        ruined_count += int(ruined)
        passed_count += int(passed)
        reached_phase_2_count += int(reached_phase_2)
        ending_balances.append(float(final_balance))
        if days_to_pass is not None:
            pass_days.append(int(days_to_pass))

    risk_of_ruin = ruined_count / float(simulation_runs)
    chance_to_pass = passed_count / float(simulation_runs)
    survival_rate = 1.0 - risk_of_ruin
    avg_ending_balance = sum(ending_balances) / max(1, len(ending_balances))

    st.markdown("### Results")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
    m2.metric("Chance to Pass", f"{chance_to_pass:.2%}")
    m3.metric("Survival Rate", f"{survival_rate:.2%}")
    m4.metric("Avg Ending Balance", f"${avg_ending_balance:,.2f}")

    if challenge_type == "2-Phase Challenge":
        reached_phase_2_probability = reached_phase_2_count / float(simulation_runs)
        st.metric("Reached Phase 2", f"{reached_phase_2_probability:.2%}")

    if pass_days:
        st.success(f"Average time to pass: **{(sum(pass_days) / len(pass_days)):.1f} trading days**")
    else:
        st.warning("No passing paths in this run, so average time-to-pass is unavailable.")

    st.info("Tip: Lower risk per trade and/or fewer trades per day usually lowers ruin risk.")
