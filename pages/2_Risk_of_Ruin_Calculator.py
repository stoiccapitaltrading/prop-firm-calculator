# -*- coding: utf-8 -*-
import random
import streamlit as st

# ---------------------------
# Page config (ONLY ONCE)
# ---------------------------
st.set_page_config(page_title="Risk of Ruin Calculator", layout="wide")

# ---------------------------
# Constants for time conversion
# ---------------------------
TRADING_DAYS_PER_WEEK = 5
TRADING_DAYS_PER_MONTH = 21  # approx trading days in a month


def days_to_weeks_months(trading_days: float) -> tuple[float, float]:
    weeks = trading_days / TRADING_DAYS_PER_WEEK
    months = trading_days / TRADING_DAYS_PER_MONTH
    return weeks, months


# ---------------------------
# UI Header
# ---------------------------
st.title("Risk of Ruin Calculator")
st.caption("Estimate ruin risk, pass probability, and expected time-to-pass for prop-firm challenges.")

st.markdown(
    """
This simulator models many account paths using your trading profile.
A run is marked as **ruined** if it breaches either:
- **Daily drawdown limit** (relative to start-of-day balance), or
- **Overall drawdown limit** (relative to initial balance).
"""
)

# ---------------------------
# Challenge selection
# ---------------------------
challenge_type = st.radio(
    "Challenge Type",
    options=["1-Phase Challenge", "2-Phase Challenge"],
    horizontal=True,
    key="challenge_type",
)

# ---------------------------
# Inputs
# ---------------------------
st.markdown("### Account & Risk Profile")
left_col, right_col = st.columns(2)

with left_col:
    starting_balance = st.number_input(
        "Starting Balance ($)",
        min_value=1000.0,
        value=100000.0,
        step=1000.0,
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
    overall_drawdown_pct = st.number_input(
        "Overall Drawdown Limit (%)",
        min_value=0.1,
        max_value=30.0,
        value=10.0,
        step=0.1,
        key="overall_drawdown_pct",
    )

with right_col:
    win_rate_pct = st.number_input(
        "Win Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=1.0,
        key="win_rate_pct",
    )
    breakeven_rate_pct = st.number_input(
        "Breakeven Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
        key="breakeven_rate_pct",
    )
    reward_risk = st.number_input(
        "Average Reward/Risk (R)",
        min_value=0.1,
        max_value=10.0,
        value=1.5,
        step=0.1,
        key="reward_risk",
    )
    risk_per_trade_pct = st.number_input(
        "Risk Per Trade (% of balance)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
        key="risk_per_trade_pct",
    )
    trades_per_day = st.number_input(
        "Trades Per Day",
        min_value=1,
        max_value=20,
        value=3,
        step=1,
        key="trades_per_day",
    )

# Validate rates
if win_rate_pct + breakeven_rate_pct > 100:
    st.error("Win Rate + Breakeven Rate cannot exceed 100%. Reduce one of them.")
    st.stop()

loss_rate_pct = 100.0 - win_rate_pct - breakeven_rate_pct

st.caption(
    f"Implied Loss Rate: **{loss_rate_pct:.1f}%** "
    f"(Win {win_rate_pct:.1f}% / BE {breakeven_rate_pct:.1f}% / Loss {loss_rate_pct:.1f}%)"
)

st.markdown("### Challenge Targets & Simulation")

# Phase 1 is always shown
if challenge_type == "2-Phase Challenge":
    c1, c2, c3, c4 = st.columns(4)
else:
    c1, c3, c4 = st.columns(3)

with c1:
    target_phase_1_pct = st.number_input(
        "Phase 1 Target Profit (%)",
        min_value=0.1,
        max_value=100.0,
        value=8.0,
        step=0.1,
        key="target_phase_1_pct",
    )

# Phase 2 is ONLY shown in 2-Phase mode (hidden otherwise)
if challenge_type == "2-Phase Challenge":
    with c2:
        target_phase_2_pct = st.number_input(
            "Phase 2 Target Profit (%)",
            min_value=0.1,
            max_value=100.0,
            value=5.0,
            step=0.1,
            key="target_phase_2_pct",
        )
else:
    target_phase_2_pct = 0.0  # not used

with c3:
    simulation_runs = st.slider(
        "Simulation Runs",
        min_value=100,
        max_value=10000,
        value=2000,
        step=100,
        key="simulation_runs",
    )

with c4:
    max_days_per_phase = st.slider(
        "Max Trading Days (per phase)",
        min_value=5,
        max_value=180,
        value=30,
        key="max_days_per_phase",
    )

# ---------------------------
# EOD Trailing Stop (Phase 1 only)
# ---------------------------
st.markdown("### Advanced Options")

use_eod_trailing_stop = st.toggle(
    "Enable EOD Trailing Stop (Phase 1 only)",
    value=False,
    key="use_eod_trailing_stop",
    help="The overall drawdown floor trails up each EOD based on the highest closing balance reached so far in Phase 1.",
)

if use_eod_trailing_stop:
    st.caption(
        "🔒 **EOD Trailing Stop active for Phase 1:** At the end of each trading day, "
        "if your closing balance is a new equity high, the overall floor moves up to "
        "`new_high × (1 - overall_drawdown_pct%)`. The floor never moves down."
    )


# ---------------------------
# Simulation logic
# ---------------------------
def simulate_phase(target_profit_pct: float, use_trailing: bool = False) -> tuple[bool, bool, float, int, int]:
    """
    Returns:
      ruined (bool),
      passed (bool),
      ending_balance (float),
      days_used (int),
      max_consecutive_losses (int)
    """
    balance = float(starting_balance)
    initial_balance = float(starting_balance)

    target_balance = initial_balance * (1.0 + target_profit_pct / 100.0)
    overall_floor = initial_balance * (1.0 - float(overall_drawdown_pct) / 100.0)

    # Trailing stop: track the highest EOD balance seen
    peak_balance = initial_balance

    win_prob = float(win_rate_pct) / 100.0
    be_prob = float(breakeven_rate_pct) / 100.0

    risk_fraction = float(risk_per_trade_pct) / 100.0

    max_consec_losses = 0
    current_consec_losses = 0

    for day in range(1, int(max_days_per_phase) + 1):
        day_start_balance = balance
        daily_floor = day_start_balance * (1.0 - float(daily_drawdown_pct) / 100.0)

        for _ in range(int(trades_per_day)):
            risk_amount = balance * risk_fraction
            r = random.random()

            if r <= win_prob:
                pnl = risk_amount * float(reward_risk)
                current_consec_losses = 0
            elif r <= win_prob + be_prob:
                pnl = 0.0
                # breakeven doesn't reset or increment loss streak
            else:
                pnl = -risk_amount
                current_consec_losses += 1
                if current_consec_losses > max_consec_losses:
                    max_consec_losses = current_consec_losses

            balance += pnl

            # Ruin check (either rule breached)
            if balance <= overall_floor or balance <= daily_floor:
                return True, False, balance, day, max_consec_losses

            # Pass check
            if balance >= target_balance:
                return False, True, balance, day, max_consec_losses

        # --- EOD: update trailing stop if enabled ---
        if use_trailing and balance > peak_balance:
            peak_balance = balance
            new_floor = peak_balance * (1.0 - float(overall_drawdown_pct) / 100.0)
            if new_floor > overall_floor:
                overall_floor = new_floor

    # Timed out
    return False, False, balance, int(max_days_per_phase), max_consec_losses


def simulate_challenge() -> tuple[bool, bool, bool, float, int | None, int, int]:
    """
    Returns:
      ruined,
      passed_final,
      reached_phase_2,
      final_balance,
      days_to_pass (None if not passed),
      total_days_used,
      max_consecutive_losses
    """
    ruined, phase_1_passed, bal_after_p1, p1_days, p1_consec = simulate_phase(
        target_phase_1_pct, use_trailing=use_eod_trailing_stop
    )

    if ruined:
        return True, False, False, bal_after_p1, None, p1_days, p1_consec

    if not phase_1_passed:
        return False, False, False, bal_after_p1, None, p1_days, p1_consec

    # If 1-phase, passing phase 1 is passing challenge
    if challenge_type == "1-Phase Challenge":
        return False, True, False, bal_after_p1, p1_days, p1_days, p1_consec

    # Phase 2 (no trailing stop)
    ruined, phase_2_passed, bal_after_p2, p2_days, p2_consec = simulate_phase(
        target_phase_2_pct, use_trailing=False
    )
    total_days = p1_days + p2_days
    max_consec = max(p1_consec, p2_consec)

    if ruined:
        return True, False, True, bal_after_p2, None, total_days, max_consec

    if phase_2_passed:
        return False, True, True, bal_after_p2, total_days, total_days, max_consec

    return False, False, True, bal_after_p2, None, total_days, max_consec


# ---------------------------
# Run
# ---------------------------
if st.button("Run Simulation", type="primary", key="run_sim_button"):
    ruined_count = 0
    passed_count = 0
    reached_phase_2_count = 0
    ending_balances: list[float] = []
    pass_days: list[int] = []
    all_consec_losses: list[int] = []

    for _ in range(int(simulation_runs)):
        ruined, passed, reached_phase_2, final_balance, days_to_pass, _total_days, max_consec = simulate_challenge()
        ruined_count += int(ruined)
        passed_count += int(passed)
        reached_phase_2_count += int(reached_phase_2)
        ending_balances.append(float(final_balance))
        all_consec_losses.append(max_consec)
        if days_to_pass is not None:
            pass_days.append(int(days_to_pass))

    risk_of_ruin = ruined_count / float(simulation_runs)
    chance_to_pass = passed_count / float(simulation_runs)
    survival_rate = 1.0 - risk_of_ruin
    avg_ending_balance = sum(ending_balances) / len(ending_balances) if ending_balances else 0.0

    st.markdown("### Results")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
    m2.metric("Chance to Pass", f"{chance_to_pass:.2%}")
    m3.metric("Survival Rate", f"{survival_rate:.2%}")
    m4.metric("Avg Ending Balance", f"${avg_ending_balance:,.2f}")

    if challenge_type == "2-Phase Challenge":
        reached_phase_2_probability = reached_phase_2_count / float(simulation_runs)
        st.metric("Reached Phase 2", f"{reached_phase_2_probability:.2%}")

    avg_days_to_pass = (sum(pass_days) / len(pass_days)) if pass_days else None
    if avg_days_to_pass is not None:
        weeks, months = days_to_weeks_months(avg_days_to_pass)
        st.success(
            f"Average time to pass: **{avg_days_to_pass:.1f} trading days** "
            f"(~**{weeks:.1f} weeks** / ~**{months:.1f} months**)"
        )
    else:
        st.warning("No passing paths in this run, so average time-to-pass is unavailable.")

    # ---------------------------
    # Consecutive Loss Streak Stats
    # ---------------------------
    st.markdown("### Consecutive Loss Streak Analysis")

    avg_consec = sum(all_consec_losses) / len(all_consec_losses) if all_consec_losses else 0
    max_consec_overall = max(all_consec_losses) if all_consec_losses else 0

    # Bucket distribution
    buckets = {"1–3": 0, "4–6": 0, "7–10": 0, "11+": 0}
    for v in all_consec_losses:
        if v <= 3:
            buckets["1–3"] += 1
        elif v <= 6:
            buckets["4–6"] += 1
        elif v <= 10:
            buckets["7–10"] += 1
        else:
            buckets["11+"] += 1

    cl1, cl2, cl3, cl4, cl5 = st.columns(5)
    cl1.metric("Avg Max Streak", f"{avg_consec:.1f} losses")
    cl2.metric("Worst Streak (all runs)", f"{max_consec_overall} losses")
    cl3.metric("Streak 1–3", f"{buckets['1–3'] / simulation_runs:.1%} of runs")
    cl4.metric("Streak 4–6", f"{buckets['4–6'] / simulation_runs:.1%} of runs")
    cl5.metric("Streak 7+", f"{(buckets['7–10'] + buckets['11+']) / simulation_runs:.1%} of runs")

    st.caption(
        f"The streak tracker counts the longest consecutive losing run encountered across the entire challenge path. "
        f"Breakeven trades do **not** reset or extend the streak."
    )

    st.info("Tip: Lower risk per trade and/or fewer trades per day usually lowers ruin risk.")
