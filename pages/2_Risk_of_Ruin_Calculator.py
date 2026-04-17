# -*- coding: utf-8 -*-
import random
from typing import Optional, Tuple, List

import streamlit as st

st.set_page_config(page_title="Risk of Ruin Calculator", layout="wide")

TRADING_DAYS_PER_WEEK = 5
TRADING_DAYS_PER_MONTH = 21
BIWEEKLY_TRADING_DAYS = 10


def days_to_weeks_months(trading_days: float) -> Tuple[float, float]:
    """Convert trading‑days to weeks and months (approx)."""
    return trading_days / TRADING_DAYS_PER_WEEK, trading_days / TRADING_DAYS_PER_MONTH


def estimate_setup_day_probability(
    avg_trades_per_month: float, win_rate_pct: float, partial_win_rate_pct: float
) -> Tuple[float, float]:
    """Return (setup_day_probability, expected_setup_days_per_month)."""
    expected_trades_per_setup_day = 2.0 - ((win_rate_pct + partial_win_rate_pct) / 100.0)
    if expected_trades_per_setup_day <= 0:
        return 0.0, 0.0
    setup_day_probability = min(
        avg_trades_per_month
        / (TRADING_DAYS_PER_MONTH * expected_trades_per_setup_day),
        1.0,
    )
    expected_setup_days = setup_day_probability * TRADING_DAYS_PER_MONTH
    return setup_day_probability, expected_setup_days


def payout_interval_days(frequency: str) -> int:
    """Map payout frequency string to number of trading days."""
    return {
        "Weekly": 5,
        "Biweekly": BIWEEKLY_TRADING_DAYS,
        "Monthly": TRADING_DAYS_PER_MONTH,
    }[frequency]


# ----------------------------------------------------------------------
#   CFD TAB
# ----------------------------------------------------------------------
def render_cfd_tab() -> None:
    st.caption(
        "Estimate ruin risk, pass probability, and expected time‑to‑pass for prop‑firm CFD challenges."
    )

    # ------------------------------------------------------------------
    #   Challenge type selector
    # ------------------------------------------------------------------
    challenge_type = st.radio(
        "Challenge Type",
        options=["1-Phase Challenge", "2-Phase Challenge", "3-Phase Challenge"],
        horizontal=True,
        key="cfd_challenge_type",
    )

    # ------------------------------------------------------------------
    #   Account & risk profile inputs
    # ------------------------------------------------------------------
    st.markdown("### Account & Risk Profile")
    left_col, right_col = st.columns(2)

    with left_col:
        starting_balance = st.number_input(
            "Starting Balance ($)",
            min_value=1000.0,
            value=100000.0,
            step=1000.0,
            key="cfd_starting_balance",
        )
        daily_drawdown_pct = st.number_input(
            "Daily Drawdown Limit (%)",
            min_value=0.1,
            max_value=20.0,
            value=5.0,
            step=0.1,
            key="cfd_daily_drawdown_pct",
        )
        overall_drawdown_pct = st.number_input(
            "Overall Drawdown Limit (%)",
            min_value=0.1,
            max_value=30.0,
            value=10.0,
            step=0.1,
            key="cfd_overall_drawdown_pct",
        )

    with right_col:
        win_rate_pct = st.number_input(
            "Full Win Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=0.01,
            format="%.2f",
            key="cfd_win_rate_pct",
        )
        partial_win_rate_pct = st.number_input(
            "Partial Win Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="cfd_partial_win_rate_pct",
            help="Trades that close in profit but below your full target R.",
        )
        partial_win_r = st.number_input(
            "Partial Win Avg R",
            min_value=0.01,
            max_value=10.0,
            value=0.5,
            step=0.01,
            format="%.2f",
            key="cfd_partial_win_r",
            help="Average R earned on partial win trades.",
        )
        breakeven_rate_pct = st.number_input(
            "Breakeven Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="cfd_breakeven_rate_pct",
        )
        reward_risk = st.number_input(
            "Full Win Avg R",
            min_value=0.1,
            max_value=10.0,
            value=1.5,
            step=0.01,
            format="%.2f",
            key="cfd_reward_risk",
            help="Average R earned on full win trades.",
        )
        risk_per_trade_pct = st.number_input(
            "Risk Per Trade (% of balance)",
            min_value=0.1,
            max_value=5.0,
            value=1.0,
            step=0.1,
            key="cfd_risk_per_trade_pct",
        )
        avg_trades_per_month = st.number_input(
            "Average Trades Per Month",
            min_value=1,
            max_value=200,
            value=22,
            step=1,
            key="cfd_avg_trades_per_month",
        )

    # ------------------------------------------------------------------
    #   Basic validation & EV calculation
    # ------------------------------------------------------------------
    total_non_loss_pct = win_rate_pct + partial_win_rate_pct + breakeven_rate_pct
    if total_non_loss_pct > 100:
        st.error("Full Win % + Partial Win % + Breakeven % cannot exceed 100%.")
        st.stop()

    loss_rate_pct = 100.0 - total_non_loss_pct
    ev = (
        (win_rate_pct / 100.0) * float(reward_risk)
        + (partial_win_rate_pct / 100.0) * float(partial_win_r)
        - (loss_rate_pct / 100.0) * 1.0
    )
    setup_day_probability, expected_setup_days = estimate_setup_day_probability(
        float(avg_trades_per_month), float(win_rate_pct), float(partial_win_rate_pct)
    )
    st.caption(
        f"Outcome split — Full Win: **{win_rate_pct:.2f}%** @ +{reward_risk:.2f}R | "
        f"Partial Win: **{partial_win_rate_pct:.2f}%** @ +{partial_win_r:.2f}R | "
        f"BE: **{breakeven_rate_pct:.2f}%** | "
        f"Loss: **{loss_rate_pct:.2f}%** @ -1R | "
        f"Expected Value per trade: **{ev:+.4f}R**"
    )
    st.caption(
        "Daily rule model: a full win or partial win ends the day. "
        "A first‑trade breakeven or loss allows one more trade only. "
        f"Average trades/month of **{avg_trades_per_month}** implies setups on about **{expected_setup_days:.1f}** trading days per month."
    )

    # ------------------------------------------------------------------
    #   Challenge targets & simulation parameters
    # ------------------------------------------------------------------
    st.markdown("### Challenge Targets & Simulation")
    if challenge_type == "3-Phase Challenge":
        c1, c2, c2b, c3, c4 = st.columns(5)
    elif challenge_type == "2-Phase Challenge":
        c1, c2, c3, c4 = st.columns(4)
    else:
        c1, c3, c4 = st.columns(3)

    with:
        target_phase_1_pct = st.number_input(
            "Phase 1 Target Profit (%)",
            min_value=0.1,
            max_value=100.0,
            value=8.0,
            step=0.1,
            key="cfd_target_phase_1_pct",
        )
        min_days_phase_1 = st.number_input(
            "Min Trading Days (Phase 1)",
            min_value=0,
            max_value=180,
            value=0,
            step=1,
            key="cfd_min_days_phase_1",
        )
        min_profit_day_pct_phase_1 = st.number_input(
            "Min Profitable‑Day % (Phase 1)",
            min_value=0.0,
            max_value=5.0,
            value=0.0,
            step=0.01,
            key="cfd_min_profit_day_pct_phase_1",
        )

    if challenge_type in ("2-Phase Challenge", "3-Phase Challenge"):
        with c2:
            target_phase_2_pct = st.number_input(
                "Phase 2 Target Profit (%)",
                min_value=0.1,
                max_value=100.0,
                value=5.0,
                step=0.1,
                key="cfd_target_phase_2_pct",
            )
            min_days_phase_2 = st.number_input(
                "Min Trading Days (Phase 2)",
                min_value=0,
                max_value=180,
                value=0,
                step=1,
                key="cfd_min_days_phase_2",
            )
            min_profit_day_pct_phase_2 = st.number_input(
                "Min Profitable‑Day % (Phase 2)",
                min_value=0.0,
                max_value=5.0,
                value=0.0,
                step=0.01,
                key="cfd_min_profit_day_pct_phase_2",
            )
    else:
        target_phase_2_pct = 0.0
        min_days_phase_2 = 0
        min_profit_day_pct_phase_2 = 0.0

    if challenge_type == "3-Phase Challenge":
        with c2b:
            target_phase_3_pct = st.number_input(
                "Phase 3 Target Profit (%)",
                min_value=0.1,
                max_value=100.0,
                value=5.0,
                step=0.1,
                key="cfd_target_phase_3_pct",
            )
            min_days_phase_3 = st.number_input(
                "Min Trading Days (Phase 3)",
                min_value=0,
                max_value=180,
                value=0,
                step=1,
                key="cfd_min_days_phase_3",
            )
            min_profit_day_pct_phase_3 = st.number_input(
                "Min Profitable‑Day % (Phase 3)",
                min_value=0.0,
                max_value=5.0,
                value=0.0,
                step=0.01,
                key="cfd_min_profit_day_pct_phase_3",
            )
    else:
        target_phase_3_pct = 0.0
        min_days_phase_3 = 0
        min_profit_day_pct_phase_3 = 0.0

    with c3:
        simulation_runs = st.slider(
            "Simulation Runs",
            min_value=100,
            max_value=10000,
            value=2000,
            step=100,
            key="cfd_simulation_runs",
        )

    with c4:
        max_days_per_phase = st.slider(
            "Max Trading Days (per phase)",
            min_value=5,
            max_value=180,
            value=30,
            key="cfd_max_days_per_phase",
        )

    # ------------------------------------------------------------------
    #   Advanced options
    # ------------------------------------------------------------------
    st.markdown("### Advanced Options")
    use_eod_trailing_stop = st.toggle(
        "Enable EOD Trailing Stop (Phase 1 only)",
        value=False,
        key="cfd_use_eod_trailing_stop",
        help="The overall drawdown floor trails up each EOD based on the highest closing balance reached so far in Phase 1.",
    )
    if use_eod_trailing_stop:
        st.caption(
            "EOD trailing stop is active for Phase 1. At the end of each trading day, "
            "if your closing balance is a new equity high, the overall floor moves up to "
            "`new_high x (1 - overall_drawdown_pct%)`. The floor never moves down."
        )

    # ------------------------------------------------------------------
    #   Funded‑account continuation toggle (no payout target any more)
    # ------------------------------------------------------------------
    st.markdown("### Funded Account Continuation")
    enable_funded_mode = st.toggle(
        "Continue Passed Runs Into Funded Account",
        value=False,
        key="cfd_enable_funded_mode",
        help="After a challenge pass, continue the same Monte Carlo run **but start from a fresh balance**. "
             "Withdraw whatever profit is available on each payout‑check day.",
    )
    if enable_funded_mode:
        funded_col1, funded_col2 = st.columns(2)
        with funded_col1:
            funded_payout_split_pct = st.number_input(
                "Payout Split (%)",
                min_value=1.0,
                max_value=100.0,
                value=80.0,
                step=1.0,
                key="cfd_funded_payout_split_pct",
            )
        with funded_col2:
            funded_max_days = st.slider(
                "Funded Trading Days",
                min_value=5,
                max_value=180,
                value=30,
                key="cfd_funded_max_days",
            )
            funded_payout_frequency = st.selectbox(
                "Payout Frequency",
                options=["Weekly", "Biweekly", "Monthly"],
                index=1,
                key="cfd_funded_payout_frequency",
            )
        st.caption(
            "Funded mode **resets the balance back to the original starting balance** "
            "but continues the same random‑draw sequence."
        )

    # ----------------------------------------------------------------------
    #   SINGLE‑PHASE simulator (used for every challenge phase)
    # ----------------------------------------------------------------------
    def simulate_phase(
        target_profit_pct: float,
        min_days: int,
        min_profit_day_pct: float,
        use_trailing: bool = False,
        prev_consec_losses: int = 0,
    ) -> Tuple[bool, bool, float, int, int, int, float]:
        """
        Simulate ONE challenge phase.

        Returns:
            ruined, passed,
            final_balance,
            days_used,
            max_consec_losses      – worst streak *inside* this phase,
            final_consec_losses    – streak length still open at the end of the phase,
            first_payout_size
        """
        # ----- 1️⃣  Fresh balance for the new phase -----
        balance = float(starting_balance)                 # reset to original balance
        initial_balance = float(starting_balance)

        target_balance = initial_balance * (1.0 + target_profit_pct / 100.0)
        overall_floor = initial_balance * (1.0 - float(overall_drawdown_pct) / 100.0)
        peak_balance = initial_balance

        # ----- 2️⃣  Outcome thresholds -----
        thresh_win = float(win_rate_pct) / 100.0
        thresh_partial_win = thresh_win + float(partial_win_rate_pct) / 100.0
        thresh_be = thresh_partial_win + float(breakeven_rate_pct) / 100.0

        risk_fraction = float(risk_per_trade_pct) / 100.0

        # ----- 3️⃣  Streak bookkeeping – carry over from previous phase -----
        max_consec_losses = prev_consec_losses
        current_consec_losses = prev_consec_losses
        first_payout_size = 0.0

        # ----- 4️⃣  Tracking for minimum‑profit‑day requirement -----
        profit_day_met = False
        profit_day_threshold = float(min_profit_day_pct) / 100.0 * starting_balance

        # ----- 5️⃣  Day‑by‑day loop -----
        for day in range(1, int(max_days_per_phase) + 1):
            day
