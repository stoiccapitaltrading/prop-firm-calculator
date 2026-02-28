# -*- coding: utf-8 -*-
import random

import streamlit as st

st.set_page_config(page_title="Risk of Ruin Calculator", layout="centered")

st.title("Risk of Ruin Calculator")
st.caption("Estimate the chance of violating prop-firm drawdown rules.")

st.markdown(
    """
This simulator models many account paths using your trading profile.
A run is marked as **ruined** if it breaches either:
- **Daily drawdown limit** (relative to start-of-day balance), or
- **Overall drawdown limit** (relative to initial balance).
"""
)
st.set_page_config(page_title="Risk of Ruin Calculator", layout="wide")

st.title("Risk of Ruin Calculator")
st.caption("Estimate ruin risk, pass probability, and expected time-to-pass for prop-firm challenges.")

challenge_type = st.radio(
    "Challenge Type",
    options=["1-Phase Challenge", "2-Phase Challenge"],
    horizontal=True,
)

preset_targets = {
    "1-Phase Challenge": {"phase_1": 8.0, "phase_2": 0.0},
    "2-Phase Challenge": {"phase_1": 8.0, "phase_2": 5.0},
}

use_presets = st.checkbox("Use default target presets", value=True)
selected_preset = preset_targets[challenge_type]

left_col, right_col = st.columns(2)
with left_col:
    starting_balance = st.number_input("Starting Balance ($)", min_value=1000, value=100000, step=1000)
    daily_drawdown_pct = st.number_input(
        "Daily Drawdown Limit (%)", min_value=0.1, max_value=20.0, value=5.0, step=0.1
    )
    overall_drawdown_pct = st.number_input(
        "Overall Drawdown Limit (%)", min_value=0.1, max_value=30.0, value=10.0, step=0.1
    )

with right_col:
    win_rate_pct = st.number_input("Win Rate (%)", min_value=1.0, max_value=99.0, value=50.0, step=1.0)
    reward_risk = st.number_input("Average Reward/Risk (R)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
    risk_per_trade_pct = st.number_input(
        "Risk Per Trade (% of balance)", min_value=0.1, max_value=5.0, value=1.0, step=0.1
    )
    trades_per_day = st.number_input("Trades Per Day", min_value=1, max_value=20, value=3, step=1)

phase_col_1, phase_col_2 = st.columns(2)
with phase_col_1:
use_presets = st.toggle("Use default target presets", value=True)
selected_preset = preset_targets[challenge_type]

st.markdown("### Account & Risk Profile")
col1, col2, col3 = st.columns(3)
with col1:
    starting_balance = st.number_input("Starting Balance ($)", min_value=1000, value=100000, step=1000)
    daily_drawdown_pct = st.number_input("Daily Drawdown Limit (%)", min_value=0.1, max_value=20.0, value=5.0, step=0.1)
with col2:
    overall_drawdown_pct = st.number_input("Overall Drawdown Limit (%)", min_value=0.1, max_value=30.0, value=10.0, step=0.1)
    risk_per_trade_pct = st.number_input("Risk Per Trade (% of balance)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
with col3:
    win_rate_pct = st.number_input("Win Rate (%)", min_value=1.0, max_value=99.0, value=50.0, step=1.0)
    reward_risk = st.number_input("Average Reward/Risk (R)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)

st.markdown("### Challenge Targets & Simulation")
col4, col5, col6, col7 = st.columns(4)
with col4:
    target_phase_1_pct = st.number_input(
        "Phase 1 Target Profit (%)",
        min_value=0.1,
        max_value=100.0,
        value=float(selected_preset["phase_1"]) if use_presets else 8.0,
        step=0.1,
    )

with phase_col_2:
with col5:
    if challenge_type == "2-Phase Challenge":
        target_phase_2_pct = st.number_input(
            "Phase 2 Target Profit (%)",
            min_value=0.1,
            max_value=100.0,
            value=float(selected_preset["phase_2"]) if use_presets else 5.0,
            step=0.1,
        )
    else:
        target_phase_2_pct = 0.0
        st.caption("Phase 2 is not used in 1-Phase mode.")

sim_col_1, sim_col_2 = st.columns(2)
with sim_col_1:
    simulation_runs = st.slider("Simulation Runs", min_value=100, max_value=10000, value=2000, step=100)
with sim_col_2:
    max_days_per_phase = st.slider("Max Trading Days (per phase)", min_value=5, max_value=180, value=30)


def simulate_phase(target_profit_pct):
        st.caption("Phase 2 disabled in 1-Phase mode")
with col6:
    trades_per_day = st.number_input("Trades Per Day", min_value=1, max_value=20, value=3, step=1)
    max_days_per_phase = st.slider("Max Trading Days (per phase)", min_value=5, max_value=180, value=30)
with col7:
    simulation_runs = st.slider("Simulation Runs", min_value=100, max_value=10000, value=2000, step=100)


def simulate_phase(target_profit_pct: float):
    balance = float(starting_balance)
    initial_balance = float(starting_balance)
    target_balance = initial_balance * (1.0 + target_profit_pct / 100.0)
    overall_floor = initial_balance * (1.0 - overall_drawdown_pct / 100.0)

    win_prob = win_rate_pct / 100.0
    risk_fraction = risk_per_trade_pct / 100.0

    for _ in range(int(max_days_per_phase)):
    for day in range(1, int(max_days_per_phase) + 1):
        day_start_balance = balance
        daily_floor = day_start_balance * (1.0 - daily_drawdown_pct / 100.0)

        for _ in range(int(trades_per_day)):
            risk_amount = balance * risk_fraction
            if random.random() <= win_prob:
                pnl = risk_amount * reward_risk
            else:
                pnl = -risk_amount

            balance += pnl

            if balance <= overall_floor or balance <= daily_floor:
                return True, False, balance

            if balance >= target_balance:
                return False, True, balance

    return False, False, balance


def simulate_challenge():
    ruined, phase_1_passed, balance_after_phase_1 = simulate_phase(target_phase_1_pct)

    if ruined:
        return True, False, False, balance_after_phase_1

    if not phase_1_passed:
        return False, False, False, balance_after_phase_1

    if challenge_type == "1-Phase Challenge":
        return False, True, False, balance_after_phase_1

    ruined, phase_2_passed, balance_after_phase_2 = simulate_phase(target_phase_2_pct)

    if ruined:
        return True, False, True, balance_after_phase_2

    if phase_2_passed:
        return False, True, True, balance_after_phase_2

    return False, False, True, balance_after_phase_2
            pnl = risk_amount * reward_risk if random.random() <= win_prob else -risk_amount
            balance += pnl

            if balance <= overall_floor or balance <= daily_floor:
                return True, False, balance, day

            if balance >= target_balance:
                return False, True, balance, day

    return False, False, balance, int(max_days_per_phase)


def simulate_challenge():
    ruined, phase_1_passed, balance_after_phase_1, phase_1_days = simulate_phase(target_phase_1_pct)

    if ruined:
        return True, False, False, balance_after_phase_1, None, phase_1_days
    if not phase_1_passed:
        return False, False, False, balance_after_phase_1, None, phase_1_days
    if challenge_type == "1-Phase Challenge":
        return False, True, False, balance_after_phase_1, phase_1_days, phase_1_days

    ruined, phase_2_passed, balance_after_phase_2, phase_2_days = simulate_phase(target_phase_2_pct)
    total_days = phase_1_days + phase_2_days

    if ruined:
        return True, False, True, balance_after_phase_2, None, total_days
    if phase_2_passed:
        return False, True, True, balance_after_phase_2, total_days, total_days
    return False, False, True, balance_after_phase_2, None, total_days


if st.button("Run Simulation", type="primary"):
    ruined_count = 0
    passed_count = 0
    reached_phase_2_count = 0
    ending_balances = []

    for _ in range(int(simulation_runs)):
        ruined, passed, reached_phase_2, final_balance = simulate_challenge()
    pass_days = []

    for _ in range(int(simulation_runs)):
        ruined, passed, reached_phase_2, final_balance, days_to_pass, _ = simulate_challenge()
        ruined_count += int(ruined)
        passed_count += int(passed)
        reached_phase_2_count += int(reached_phase_2)
        ending_balances.append(final_balance)
        if days_to_pass is not None:
            pass_days.append(days_to_pass)

    risk_of_ruin = ruined_count / float(simulation_runs)
    chance_to_pass = passed_count / float(simulation_runs)
    survival_rate = 1.0 - risk_of_ruin
    avg_ending_balance = sum(ending_balances) / len(ending_balances)

    st.subheader("Results")
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
    metric_2.metric("Chance to Pass Challenge", f"{chance_to_pass:.2%}")
    metric_3.metric("Survival Rate", f"{survival_rate:.2%}")
    avg_days_to_pass = (sum(pass_days) / len(pass_days)) if pass_days else None

    st.markdown("### Results")
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
    metric_2.metric("Chance to Pass", f"{chance_to_pass:.2%}")
    metric_3.metric("Survival Rate", f"{survival_rate:.2%}")
    metric_4.metric("Avg Ending Balance", f"${avg_ending_balance:,.2f}")

    if challenge_type == "2-Phase Challenge":
        reached_phase_2_probability = reached_phase_2_count / float(simulation_runs)
        st.metric("Reached Phase 2", f"{reached_phase_2_probability:.2%}")

    st.metric("Average Ending Balance", f"${avg_ending_balance:,.2f}")
    if avg_days_to_pass is not None:
        st.success(f"Average time to pass an account: **{avg_days_to_pass:.1f} trading days**")
    else:
        st.warning("No passing paths in this run, so average time-to-pass is unavailable.")

    st.info("Tip: Lower risk per trade and/or fewer trades per day usually lowers ruin risk.")

