# -*- coding: utf-8 -*-
import csv
import random
from collections import defaultdict
from datetime import datetime
from io import StringIO

import streamlit as st

from calculator_models import (
    estimate_setup_day_probability as calculate_setup_day_probability,
    expected_trades_per_active_day,
    percentile,
    sample_dirichlet_probabilities,
    settle_profit_payout,
    wilson_interval,
)

st.set_page_config(page_title="Risk of Ruin Calculator", layout="wide")

TRADING_DAYS_PER_WEEK = 5
TRADING_DAYS_PER_MONTH = 21
BIWEEKLY_TRADING_DAYS = 10
PHASE_SIMULATION_SAFETY_MARKET_DAYS = 10_000


def days_to_weeks_months(trading_days: float) -> tuple[float, float]:
    """Convert trading‑days to weeks and months (approx)."""
    return trading_days / TRADING_DAYS_PER_WEEK, trading_days / TRADING_DAYS_PER_MONTH


def estimate_setup_day_probability(
    avg_trades_per_month: float,
    win_rate_pct: float,
    partial_win_rate_pct: float,
    second_trade_after_non_profit_rate: float = 1.0,
    second_trade_after_profit_rate: float = 0.0,
) -> tuple[float, float]:
    """Return the active-day probability aligned to the selected trade frequency."""
    return calculate_setup_day_probability(
        avg_trades_per_month,
        win_rate_pct,
        partial_win_rate_pct,
        TRADING_DAYS_PER_MONTH,
        second_trade_after_non_profit_rate,
        second_trade_after_profit_rate,
    )


def payout_interval_days(frequency: str) -> int:
    """Map payout frequency string to number of trading days."""
    return {
        "Weekly": 5,
        "Biweekly": BIWEEKLY_TRADING_DAYS,
        "Monthly": TRADING_DAYS_PER_MONTH,
    }[frequency]


def parse_journal_day_blocks(
    uploaded_file: object,
    fallback_win_r: float,
    fallback_partial_r: float,
) -> tuple[list[tuple[float, ...]], int, int]:
    """Parse a Notion-style journal into chronologically ordered daily R blocks.

    The parser accepts the journal fields used by this app: Date, Entry, R and
    Outcome. Rows without a usable date are skipped because a day bootstrap
    needs the actual grouping of trades into days.
    """
    raw_text = uploaded_file.getvalue().decode("utf-8-sig")
    rows = csv.DictReader(StringIO(raw_text))
    grouped: dict[datetime, list[tuple[int, float]]] = defaultdict(list)
    accepted_rows = 0
    skipped_rows = 0

    for row in rows:
        date_value = (row.get("Date") or "").strip().split(" ")[0]
        parsed_date = None
        for date_format in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                parsed_date = datetime.strptime(date_value, date_format)
                break
            except ValueError:
                continue
        if parsed_date is None:
            skipped_rows += 1
            continue

        r_value = (row.get("R") or "").strip().replace(",", ".")
        outcome = (row.get("Outcome") or "").strip().casefold()
        try:
            r_multiple = float(r_value)
        except ValueError:
            if outcome == "win":
                r_multiple = fallback_win_r
            elif outcome in {"be+partial", "be + partial", "partial"}:
                r_multiple = fallback_partial_r
            elif outcome in {"breakeven", "break even", "be"}:
                r_multiple = 0.0
            elif outcome == "loss":
                r_multiple = -1.0
            else:
                skipped_rows += 1
                continue

        entry_minutes = 24 * 60
        entry_value = (row.get("Entry") or "").strip()
        try:
            entry_hour, entry_minute = entry_value.split(":", maxsplit=1)
            entry_minutes = (int(entry_hour) * 60) + int(entry_minute[:2])
        except (TypeError, ValueError):
            pass

        grouped[parsed_date].append((entry_minutes, r_multiple))
        accepted_rows += 1

    day_blocks = [
        tuple(r_multiple for _, r_multiple in sorted(trades))
        for _, trades in sorted(grouped.items())
        if trades
    ]
    return day_blocks, accepted_rows, skipped_rows


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
            value=35.1,
            step=0.01,
            format="%.2f",
            key="cfd_win_rate_pct",
        )
        partial_win_rate_pct = st.number_input(
            "Partial Win Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=15.9,
            step=0.01,
            format="%.2f",
            key="cfd_partial_win_rate_pct",
            help="Trades that close in profit but below your full target R.",
        )
        partial_win_r = st.number_input(
            "Partial Win Avg R",
            min_value=0.01,
            max_value=10.0,
            value=1.0,
            step=0.01,
            format="%.2f",
            key="cfd_partial_win_r",
            help="Average R earned on partial win trades.",
        )
        breakeven_rate_pct = st.number_input(
            "Breakeven Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=14.6,
            step=0.01,
            format="%.2f",
            key="cfd_breakeven_rate_pct",
        )
        reward_risk = st.number_input(
            "Full Win Avg R",
            min_value=0.1,
            max_value=10.0,
            value=2.5,
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
    total_non_loss_pct = (
        win_rate_pct
        + partial_win_rate_pct
        + breakeven_rate_pct
    )
    if total_non_loss_pct > 100:
        st.error(
            "Full Win % + Partial Win % + Breakeven % cannot exceed 100%."
        )
        st.stop()

    loss_rate_pct = 100.0 - total_non_loss_pct
    if win_rate_pct + partial_win_rate_pct == 0 and loss_rate_pct == 0:
        st.error("At least one profitable or losing outcome is required to simulate a phase without a deadline.")
        st.stop()
    ev = (
        (win_rate_pct / 100.0) * float(reward_risk)
        + (partial_win_rate_pct / 100.0) * float(partial_win_r)
        - (loss_rate_pct / 100.0) * 1.0
    )
    st.markdown("### Simulation Model")
    model_col, risk_col = st.columns(2)
    with model_col:
        day_model = st.selectbox(
            "Second-Trade Rule",
            options=["Historical Second-Trade Pattern", "Always Trade Again After Loss or BE"],
            key="cfd_day_model",
            help="Controls whether a second trade is taken after the first trade of an active day.",
        )
        if day_model == "Historical Second-Trade Pattern":
            second_trade_after_non_profit_pct = st.number_input(
                "Second Trade After First Loss or BE (%)",
                min_value=0.0,
                max_value=100.0,
                value=33.3,
                step=0.1,
                key="cfd_second_after_non_profit_pct",
            )
            second_trade_after_profit_pct = st.number_input(
                "Second Trade After First Win or Partial (%)",
                min_value=0.0,
                max_value=100.0,
                value=7.7,
                step=0.1,
                key="cfd_second_after_profit_pct",
            )
            st.caption(
                "Measured from the current journal: 20 of 60 first loss/BE days had a second trade; "
                "5 of 65 first win/partial days had a second trade."
            )
        else:
            second_trade_after_non_profit_pct = 100.0
            second_trade_after_profit_pct = 0.0
    with risk_col:
        risk_sizing = st.selectbox(
            "Risk Sizing",
            options=["Fixed from phase starting balance", "Percent of current balance"],
            key="cfd_risk_sizing",
            help="Fixed sizing mirrors a fixed-dollar prop-firm risk plan. Percentage sizing compounds risk after every trade.",
        )
        daily_drawdown_basis = st.selectbox(
            "Daily Drawdown Basis",
            options=["Start-of-day balance", "Phase starting balance"],
            key="cfd_daily_drawdown_basis",
            help="Match this to the firm's actual daily-loss calculation before relying on the result.",
        )

    journal_bootstrap_requested = st.toggle(
        "Bootstrap an Uploaded Trade Journal",
        value=False,
        key="cfd_journal_bootstrap_requested",
        help="Resample entire historical trading days so the simulation preserves your real one-trade and two-trade day patterns.",
    )
    journal_day_blocks: list[tuple[float, ...]] = []
    journal_rows = 0
    journal_skipped_rows = 0
    if journal_bootstrap_requested:
        uploaded_journal = st.file_uploader(
            "Trade Journal CSV",
            type=["csv"],
            key="cfd_journal_upload",
            help="Expected columns: Date, Entry, R, and optionally Outcome.",
        )
        if uploaded_journal is not None:
            journal_day_blocks, journal_rows, journal_skipped_rows = parse_journal_day_blocks(
                uploaded_journal,
                float(reward_risk),
                float(partial_win_r),
            )
            if journal_day_blocks:
                journal_average_trades_per_day = journal_rows / len(journal_day_blocks)
                st.caption(
                    f"Journal bootstrap loaded **{journal_rows}** trades across **{len(journal_day_blocks)}** days "
                    f"({journal_average_trades_per_day:.2f} trades per active day)."
                )
                if journal_skipped_rows:
                    st.caption(
                        f"Skipped **{journal_skipped_rows}** row(s) without a usable date or R-multiple."
                    )
            else:
                st.error("No usable dated R-multiple rows were found in that journal.")
        else:
            st.info("Upload a journal to enable the day-bootstrap model.")

    use_journal_bootstrap = journal_bootstrap_requested and bool(journal_day_blocks)
    second_trade_after_non_profit_rate = float(second_trade_after_non_profit_pct) / 100.0
    second_trade_after_profit_rate = float(second_trade_after_profit_pct) / 100.0
    if use_journal_bootstrap:
        expected_trades_active_day = journal_rows / len(journal_day_blocks)
        setup_day_probability = min(
            float(avg_trades_per_month) / (TRADING_DAYS_PER_MONTH * expected_trades_active_day),
            1.0,
        )
        expected_setup_days = setup_day_probability * TRADING_DAYS_PER_MONTH
    else:
        expected_trades_active_day = expected_trades_per_active_day(
            float(win_rate_pct),
            float(partial_win_rate_pct),
            second_trade_after_non_profit_rate,
            second_trade_after_profit_rate,
        )
        setup_day_probability, expected_setup_days = estimate_setup_day_probability(
            float(avg_trades_per_month),
            float(win_rate_pct),
            float(partial_win_rate_pct),
            second_trade_after_non_profit_rate,
            second_trade_after_profit_rate,
        )

    include_input_uncertainty = st.toggle(
        "Include Journal-Rate Uncertainty",
        value=True,
        disabled=use_journal_bootstrap,
        key="cfd_include_input_uncertainty",
        help="Samples plausible outcome probabilities from the journal sample size instead of assuming the entered rates are exact.",
    )
    journal_sample_size = st.number_input(
        "Journal Sample Size",
        min_value=20,
        max_value=100000,
        value=151,
        step=1,
        disabled=use_journal_bootstrap or not include_input_uncertainty,
        key="cfd_journal_sample_size",
        help="Use the number of trades used to estimate the entered outcome rates.",
    )

    st.caption(
        f"Outcome split — Full Win: **{win_rate_pct:.2f}%** @ +{reward_risk:.2f}R | "
        f"Partial Win: **{partial_win_rate_pct:.2f}%** @ +{partial_win_r:.2f}R | "
        f"BE: **{breakeven_rate_pct:.2f}%** | "
        f"Loss: **{loss_rate_pct:.2f}%** @ -1R | "
        f"Expected Value per trade: **{ev:+.4f}R**"
    )
    st.caption(
        f"Model: **{'journal-day bootstrap' if use_journal_bootstrap else day_model.lower()}** | "
        f"Expected trades per active day: **{expected_trades_active_day:.2f}** | "
        f"Average trades/month of **{avg_trades_per_month}** implies setups on about **{expected_setup_days:.1f}** trading days per month."
    )
    if setup_day_probability >= 1.0:
        st.warning("The selected trade frequency exceeds the model's available active days. The simulator is capped at one active setup day per trading day.")

    # ------------------------------------------------------------------
    #   Challenge targets & simulation parameters
    # ------------------------------------------------------------------
    st.markdown("### Challenge Targets & Simulation")
    if challenge_type == "3-Phase Challenge":
        c1, c2, c2b, c3 = st.columns(4)
    elif challenge_type == "2-Phase Challenge":
        c1, c2, c3 = st.columns(3)
    else:
        c1, c3 = st.columns(2)

    with c1:
        target_phase_1_pct = st.number_input(
            "Phase 1 Target Profit (%)",
            min_value=0.1,
            max_value=100.0,
            value=8.0,
            step=0.1,
            key="cfd_target_phase_1_pct",
        )
        min_days_phase_1 = st.number_input(
            "Min Trading Days (Phase 1)",
            min_value=0,
            max_value=180,
            value=0,
            step=1,
            key="cfd_min_days_phase_1",
        )
        min_profitable_days_phase_1 = st.number_input(
            "Min Profitable Days (Phase 1)",
            min_value=0,
            max_value=180,
            value=0,
            step=1,
            key="cfd_min_profitable_days_phase_1",
            help="Number of active days that must meet the qualifying profit threshold before the phase can pass.",
        )
        min_profit_day_pct_phase_1 = st.number_input(
            "Qualifying-Day Profit Threshold (Phase 1, %)",
            min_value=0.0,
            max_value=5.0,
            value=0.0,
            step=0.01,
            key="cfd_min_profit_day_pct_phase_1",
        )

    if challenge_type in ("2-Phase Challenge", "3-Phase Challenge"):
        with c2:
            target_phase_2_pct = st.number_input(
                "Phase 2 Target Profit (%)",
                min_value=0.1,
                max_value=100.0,
                value=5.0,
                step=0.1,
                key="cfd_target_phase_2_pct",
            )
            min_days_phase_2 = st.number_input(
                "Min Trading Days (Phase 2)",
                min_value=0,
                max_value=180,
                value=0,
                step=1,
                key="cfd_min_days_phase_2",
            )
            min_profitable_days_phase_2 = st.number_input(
                "Min Profitable Days (Phase 2)",
                min_value=0,
                max_value=180,
                value=0,
                step=1,
                key="cfd_min_profitable_days_phase_2",
                help="Number of active days that must meet the qualifying profit threshold before the phase can pass.",
            )
            min_profit_day_pct_phase_2 = st.number_input(
                "Qualifying-Day Profit Threshold (Phase 2, %)",
                min_value=0.0,
                max_value=5.0,
                value=0.0,
                step=0.01,
                key="cfd_min_profit_day_pct_phase_2",
            )
    else:
        target_phase_2_pct = 0.0
        min_days_phase_2 = 0
        min_profitable_days_phase_2 = 0
        min_profit_day_pct_phase_2 = 0.0

    if challenge_type == "3-Phase Challenge":
        with c2b:
            target_phase_3_pct = st.number_input(
                "Phase 3 Target Profit (%)",
                min_value=0.1,
                max_value=100.0,
                value=5.0,
                step=0.1,
                key="cfd_target_phase_3_pct",
            )
            min_days_phase_3 = st.number_input(
                "Min Trading Days (Phase 3)",
                min_value=0,
                max_value=180,
                value=0,
                step=1,
                key="cfd_min_days_phase_3",
            )
            min_profitable_days_phase_3 = st.number_input(
                "Min Profitable Days (Phase 3)",
                min_value=0,
                max_value=180,
                value=0,
                step=1,
                key="cfd_min_profitable_days_phase_3",
                help="Number of active days that must meet the qualifying profit threshold before the phase can pass.",
            )
            min_profit_day_pct_phase_3 = st.number_input(
                "Qualifying-Day Profit Threshold (Phase 3, %)",
                min_value=0.0,
                max_value=5.0,
                value=0.0,
                step=0.01,
                key="cfd_min_profit_day_pct_phase_3",
            )
    else:
        target_phase_3_pct = 0.0
        min_days_phase_3 = 0
        min_profitable_days_phase_3 = 0
        min_profit_day_pct_phase_3 = 0.0

    with c3:
        simulation_runs = st.slider(
            "Simulation Runs",
            min_value=1_000,
            max_value=100_000,
            value=20_000,
            step=1_000,
            key="cfd_simulation_runs",
            help="Use at least 20,000 runs for rare-event estimates. 100,000 is preferable when evaluating very low ruin probabilities.",
        )
    st.caption(
        "Evaluation phases have no modelled time deadline. The simulator continues until pass or drawdown breach."
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
            "EOD trailing stop is active for Phase 1. At the end of each trading day, "
            "if your closing balance is a new equity high, the overall floor moves up to "
            "`new_high x (1 - overall_drawdown_pct%)`. The floor never moves down."
        )
    stop_when_phase_rules_met = st.toggle(
        "Stop When Phase Pass Rules Are Met",
        value=True,
        key="cfd_stop_when_phase_rules_met",
        help="Stops immediately after the trade that reaches the target and all minimum-day rules. Turn this off to finish the simulated active day before checking for a pass.",
    )

    # ------------------------------------------------------------------
    random_seed = st.number_input(
        "Simulation Random Seed",
        min_value=0,
        value=42,
        step=1,
        key="cfd_random_seed",
        help="Use the same seed to reproduce a result; change it to sample a different path set.",
    )

    #   Funded-account projection
    # ------------------------------------------------------------------
    st.markdown("### Funded Account Continuation")
    enable_funded_mode = st.toggle(
        "Continue Passed Runs Into Funded Account",
        value=False,
        key="cfd_enable_funded_mode",
        help="After a challenge pass, continue the same Monte Carlo run and withdraw available profit on each payout-check day.",
    )
    if enable_funded_mode:
        funded_col1, funded_col2, funded_col3 = st.columns(3)
        with funded_col1:
            funded_payout_split_pct = st.number_input(
                "Payout Split (%)",
                min_value=1.0,
                max_value=100.0,
                value=80.0,
                step=1.0,
                key="cfd_funded_payout_split_pct",
            )
            funded_min_profit = st.number_input(
                "Minimum Profit Before Payout ($)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key="cfd_funded_min_profit",
            )
        with funded_col2:
            funded_payout_frequency = st.selectbox(
                "Payout Frequency",
                options=["Weekly", "Biweekly", "Monthly"],
                index=2,
                key="cfd_funded_payout_frequency",
            )
            funded_start_mode = st.selectbox(
                "Funded Starting Balance",
                options=["Fresh account balance", "Challenge pass balance"],
                key="cfd_funded_start_mode",
                help="Most firms issue a fresh funded account after passing. Choose the pass balance only when the firm actually carries evaluation equity forward.",
            )
        with funded_col3:
            funded_max_days = st.number_input(
                "Funded Projection Horizon (Market Days)",
                min_value=21,
                max_value=1260,
                value=252,
                step=21,
                key="cfd_funded_max_days",
                help="This is a reporting horizon, not an account expiry. Accounts still above their drawdown floor remain active at its end.",
            )

    def draw_configured_outcome(outcome_probabilities: tuple[float, ...]) -> tuple[float, str]:
        """Draw one R-multiple from the configured categorical distribution."""
        full_win_probability, partial_probability, breakeven_probability, _ = outcome_probabilities
        draw = rng.random()
        if draw < full_win_probability:
            return float(reward_risk), "profit"
        if draw < full_win_probability + partial_probability:
            return float(partial_win_r), "profit"
        if draw < full_win_probability + partial_probability + breakeven_probability:
            return 0.0, "breakeven"
        return -1.0, "loss"

    def draw_trade_day(outcome_probabilities: tuple[float, ...]) -> tuple[tuple[float, str], ...]:
        """Draw a complete active trading day from the chosen model."""
        if use_journal_bootstrap:
            return tuple(
                (r_multiple, "profit" if r_multiple > 0 else "loss" if r_multiple < 0 else "breakeven")
                for r_multiple in rng.choice(journal_day_blocks)
            )

        first_trade = draw_configured_outcome(outcome_probabilities)
        second_trade_probability = (
            second_trade_after_profit_rate
            if first_trade[1] == "profit"
            else second_trade_after_non_profit_rate
        )
        if rng.random() < second_trade_probability:
            return first_trade, draw_configured_outcome(outcome_probabilities)
        return (first_trade,)

    def risk_amount(balance: float, phase_start_balance: float) -> float:
        risk_fraction = float(risk_per_trade_pct) / 100.0
        if risk_sizing == "Fixed from phase starting balance":
            return phase_start_balance * risk_fraction
        return balance * risk_fraction

    def daily_floor(day_start_balance: float, phase_start_balance: float) -> float:
        reference_balance = (
            day_start_balance
            if daily_drawdown_basis == "Start-of-day balance"
            else phase_start_balance
        )
        return reference_balance * (1.0 - float(daily_drawdown_pct) / 100.0)

    def simulate_phase(
        target_profit_pct: float,
        min_days: int,
        min_profitable_days: int,
        min_profit_day_pct: float,
        use_trailing: bool,
        outcome_probabilities: tuple[float, ...],
    ) -> tuple[bool, bool, float, int]:
        """Simulate one evaluation phase from a fresh phase balance."""
        phase_start_balance = float(starting_balance)
        balance = phase_start_balance
        overall_floor = phase_start_balance * (1.0 - float(overall_drawdown_pct) / 100.0)
        peak_balance = phase_start_balance
        target_balance = phase_start_balance * (1.0 + float(target_profit_pct) / 100.0)
        profit_day_threshold = float(min_profit_day_pct) / 100.0 * phase_start_balance
        qualified_profitable_days = 0
        trading_days_used = 0
        required_profitable_days = max(
            int(min_profitable_days),
            1 if min_profit_day_pct > 0 else 0,
        )

        def phase_rules_met(current_balance: float, qualifying_days: int) -> bool:
            return (
                current_balance >= target_balance
                and trading_days_used >= min_days
                and qualifying_days >= required_profitable_days
            )

        day = 0
        while day < PHASE_SIMULATION_SAFETY_MARKET_DAYS:
            day += 1
            day_start_balance = balance
            if rng.random() > setup_day_probability:
                if use_trailing and balance > peak_balance:
                    peak_balance = balance
                    overall_floor = max(
                        overall_floor,
                        peak_balance * (1.0 - float(overall_drawdown_pct) / 100.0),
                    )
                continue

            trading_days_used += 1
            for r_multiple, _ in draw_trade_day(outcome_probabilities):
                balance += risk_amount(balance, phase_start_balance) * r_multiple
                if balance <= overall_floor or balance <= daily_floor(day_start_balance, phase_start_balance):
                    return True, False, balance, day
                current_day_profit = balance - day_start_balance
                prospective_qualified_days = qualified_profitable_days + int(
                    current_day_profit > 0 and current_day_profit >= profit_day_threshold
                )
                if stop_when_phase_rules_met and phase_rules_met(
                    balance,
                    prospective_qualified_days,
                ):
                    return False, True, balance, day

            day_profit = balance - day_start_balance
            if day_profit > 0 and day_profit >= profit_day_threshold:
                qualified_profitable_days += 1

            if use_trailing and balance > peak_balance:
                peak_balance = balance
                overall_floor = max(
                    overall_floor,
                    peak_balance * (1.0 - float(overall_drawdown_pct) / 100.0),
                )

            if phase_rules_met(balance, qualified_profitable_days):
                return False, True, balance, day

        return False, False, balance, day

    def simulate_challenge(outcome_probabilities: tuple[float, ...]) -> tuple[bool, bool, float, int | None]:
        """Run all configured phases and return the cumulative pass time."""
        ruined, passed, balance, total_days = simulate_phase(
            target_phase_1_pct,
            min_days_phase_1,
            min_profitable_days_phase_1,
            min_profit_day_pct_phase_1,
            use_eod_trailing_stop,
            outcome_probabilities,
        )
        if ruined or not passed:
            return ruined, False, balance, None
        if challenge_type == "1-Phase Challenge":
            return False, True, balance, total_days

        ruined, passed, balance, phase_days = simulate_phase(
            target_phase_2_pct,
            min_days_phase_2,
            min_profitable_days_phase_2,
            min_profit_day_pct_phase_2,
            False,
            outcome_probabilities,
        )
        total_days += phase_days
        if ruined or not passed:
            return ruined, False, balance, None
        if challenge_type == "2-Phase Challenge":
            return False, True, balance, total_days

        ruined, passed, balance, phase_days = simulate_phase(
            target_phase_3_pct,
            min_days_phase_3,
            min_profitable_days_phase_3,
            min_profit_day_pct_phase_3,
            False,
            outcome_probabilities,
        )
        total_days += phase_days
        return ruined, passed, balance, total_days if passed else None

    def simulate_funded_account(
        outcome_probabilities: tuple[float, ...],
        funded_start_balance: float,
    ) -> tuple[bool, int, int | None, float]:
        """Simulate a funded account and settle only newly earned payout profit."""
        initial_balance = funded_start_balance
        balance = initial_balance
        overall_floor = initial_balance * (1.0 - float(overall_drawdown_pct) / 100.0)
        payout_hits = 0
        first_payout_day = None
        total_payout_amount = 0.0

        for day in range(1, int(funded_max_days) + 1):
            day_start_balance = balance
            if rng.random() <= setup_day_probability:
                for r_multiple, _ in draw_trade_day(outcome_probabilities):
                    balance += risk_amount(balance, initial_balance) * r_multiple
                    if balance <= overall_floor or balance <= daily_floor(day_start_balance, initial_balance):
                        return True, payout_hits, first_payout_day, total_payout_amount

            current_profit = balance - initial_balance
            if (
                day % payout_interval_days(funded_payout_frequency) == 0
                and current_profit >= float(funded_min_profit)
                and current_profit > 0
            ):
                payout_amount, balance = settle_profit_payout(
                    balance,
                    initial_balance,
                    float(funded_payout_split_pct),
                )
                total_payout_amount += payout_amount
                payout_hits += 1
                if first_payout_day is None:
                    first_payout_day = day

        return False, payout_hits, first_payout_day, total_payout_amount

    # ----------------------------------------------------------------------
    #   RUN BUTTON – collect results and display them
    # ----------------------------------------------------------------------
    if st.button("Run CFD Simulation", type="primary", key="cfd_run_sim_button"):
        rng = random.Random(int(random_seed))
        ruined_count = 0
        passed_count = 0
        ending_balances: list[float] = []
        pass_days: list[int] = []
        funded_payout_reached_count = 0
        funded_payout_hits: list[int] = []
        funded_first_payout_days: list[int] = []
        funded_ruin_after_pass_count = 0
        funded_payout_amounts: list[float] = []
        base_outcome_probabilities = (
            float(win_rate_pct) / 100.0,
            float(partial_win_rate_pct) / 100.0,
            float(breakeven_rate_pct) / 100.0,
            float(loss_rate_pct) / 100.0,
        )

        for _ in range(int(simulation_runs)):
            if include_input_uncertainty and not use_journal_bootstrap:
                run_outcome_probabilities = sample_dirichlet_probabilities(
                    rng,
                    base_outcome_probabilities,
                    int(journal_sample_size),
                )
            else:
                run_outcome_probabilities = base_outcome_probabilities

            ruined, passed, final_balance, days_to_pass = simulate_challenge(run_outcome_probabilities)

            ruined_count += int(ruined)
            passed_count += int(passed)
            ending_balances.append(float(final_balance))

            if passed:
                pass_days.append(int(days_to_pass))
                if enable_funded_mode:
                    funded_start_balance = (
                        float(final_balance)
                        if funded_start_mode == "Challenge pass balance"
                        else float(starting_balance)
                    )
                    funded_ruined, payout_hit_count, first_payout_day, total_payout_amount = simulate_funded_account(
                        run_outcome_probabilities,
                        funded_start_balance,
                    )
                    funded_ruin_after_pass_count += int(funded_ruined)
                    funded_payout_hits.append(payout_hit_count)
                    funded_payout_amounts.append(total_payout_amount)
                    if payout_hit_count > 0:
                        funded_payout_reached_count += 1
                    if first_payout_day is not None:
                        funded_first_payout_days.append(int(first_payout_day))

        # ---------- Summary statistics ----------
        risk_of_ruin = ruined_count / float(simulation_runs)
        chance_to_pass = passed_count / float(simulation_runs)
        unresolved_count = int(simulation_runs) - ruined_count - passed_count
        avg_ending_balance = (
            sum(ending_balances) / len(ending_balances) if ending_balances else 0.0
        )
        ruin_interval = wilson_interval(ruined_count, int(simulation_runs))
        pass_interval = wilson_interval(passed_count, int(simulation_runs))

        st.markdown("### CFD Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
        m2.metric("Chance to Pass", f"{chance_to_pass:.2%}")
        m3.metric("Avg Ending Balance", f"${avg_ending_balance:,.2f}")
        m4.metric("Not Resolved by Safety Guard", f"{unresolved_count / float(simulation_runs):.2%}")
        st.caption(
            f"Monte Carlo sampling interval (95%) — ruin: **{ruin_interval[0]:.2%} to {ruin_interval[1]:.2%}** | "
            f"pass: **{pass_interval[0]:.2%} to {pass_interval[1]:.2%}**. "
            "This measures simulation precision, not uncertainty in market conditions."
        )

        avg_days_to_pass = (
            sum(pass_days) / len(pass_days) if pass_days else None
        )
        if avg_days_to_pass is not None:
            weeks, months = days_to_weeks_months(avg_days_to_pass)
            pass_day_p10 = percentile(pass_days, 0.10)
            pass_day_p50 = percentile(pass_days, 0.50)
            pass_day_p90 = percentile(pass_days, 0.90)
            st.success(
                f"Average time to pass the entire challenge: **{avg_days_to_pass:.1f} trading days** "
                f"(~**{weeks:.1f} weeks** / ~**{months:.1f} months**)"
            )
            st.caption(
                f"Pass-time distribution — 10th percentile: **{pass_day_p10:.0f} days** | "
                f"median: **{pass_day_p50:.0f} days** | 90th percentile: **{pass_day_p90:.0f} days**."
            )
        else:
            st.warning(
                "No passing paths in this run, so average time‑to‑pass is unavailable."
            )

        # ---------- Funded‑account results (if enabled) ----------
        if enable_funded_mode and passed_count > 0:
            st.markdown("### Funded Account Results")
            fm1, fm2, fm3, fm4 = st.columns(4)
            fm1.metric(
                "Payout Reach During Projection",
                f"{funded_payout_reached_count / passed_count:.2%}",
            )
            fm2.metric(
                "Overall Payout Rate During Projection",
                f"{funded_payout_reached_count / simulation_runs:.2%}",
            )
            fm3.metric(
                "Avg Payouts During Projection",
                f"{(sum(funded_payout_hits) / len(funded_payout_hits)) if funded_payout_hits else 0.0:.2f}",
            )
            fm4.metric(
                "Funded Ruin During Projection",
                f"{funded_ruin_after_pass_count / passed_count:.2%}",
            )
            st.metric(
                "Avg Total Trader Payout (Projection)",
                f"${sum(funded_payout_amounts) / passed_count:,.2f}",
            )
            st.caption(
                f"Projection horizon: **{int(funded_max_days)} market days**. "
                f"Accounts still active at the horizon: **{1 - (funded_ruin_after_pass_count / passed_count):.2%}** of passed runs."
            )

            if funded_first_payout_days:
                avg_first_payout_days = sum(funded_first_payout_days) / len(
                    funded_first_payout_days
                )
                payout_weeks, payout_months = days_to_weeks_months(
                    avg_first_payout_days
                )
                st.success(
                    f"Average time to first payout: **{avg_first_payout_days:.1f} trading days** "
                    f"(~**{payout_weeks:.1f} weeks** / ~**{payout_months:.1f} months**)"
                )

        # ------------------------------------------------------------------
        #   Copy‑able summary
        # ------------------------------------------------------------------
        summary_lines = [
            "CFD Challenge Summary",
            f"Challenge type: {challenge_type}",
            f"Starting balance: ${float(starting_balance):,.2f}",
            f"Phase 1 target: {float(target_phase_1_pct):.2f}%",
            f"Phase 1 minimum active trading days: {int(min_days_phase_1)}",
            f"Phase 1 qualifying profitable days: {int(min_profitable_days_phase_1)} @ {float(min_profit_day_pct_phase_1):.2f}%",
        ]
        if challenge_type in ("2-Phase Challenge", "3-Phase Challenge"):
            summary_lines.append(f"Phase 2 target: {float(target_phase_2_pct):.2f}%")
            summary_lines.append(
                f"Phase 2 minimum active trading days: {int(min_days_phase_2)}"
            )
            summary_lines.append(
                f"Phase 2 qualifying profitable days: {int(min_profitable_days_phase_2)} @ {float(min_profit_day_pct_phase_2):.2f}%"
            )
        if challenge_type == "3-Phase Challenge":
            summary_lines.append(f"Phase 3 target: {float(target_phase_3_pct):.2f}%")
            summary_lines.append(
                f"Phase 3 minimum active trading days: {int(min_days_phase_3)}"
            )
            summary_lines.append(
                f"Phase 3 qualifying profitable days: {int(min_profitable_days_phase_3)} @ {float(min_profit_day_pct_phase_3):.2f}%"
            )
        summary_lines.extend(
            [
                f"Daily drawdown: {float(daily_drawdown_pct):.2f}%",
                f"Overall drawdown: {float(overall_drawdown_pct):.2f}%",
                f"Win rate: {float(win_rate_pct):.2f}% @ +{float(reward_risk):.2f}R",
                f"Partial win rate: {float(partial_win_rate_pct):.2f}% @ +{float(partial_win_r):.2f}R",
                f"Breakeven rate: {float(breakeven_rate_pct):.2f}%",
                f"Loss rate: {float(loss_rate_pct):.2f}% @ -1R",
                f"Risk per trade: {float(risk_per_trade_pct):.2f}% ({risk_sizing})",
                f"Daily drawdown basis: {daily_drawdown_basis}",
                f"Avg trades/month: {int(avg_trades_per_month)}",
                f"Expected active days/month: {expected_setup_days:.1f}",
                f"Trade-day model: {'Journal day bootstrap' if use_journal_bootstrap else day_model}",
                f"Stop when phase pass rules are met: {'yes' if stop_when_phase_rules_met else 'no'}",
                f"Second trade after first loss or BE: {second_trade_after_non_profit_pct:.1f}%",
                f"Second trade after first win or partial: {second_trade_after_profit_pct:.1f}%",
                f"Outcome-rate uncertainty: {'on' if include_input_uncertainty and not use_journal_bootstrap else 'off'}",
                f"Journal sample size: {int(journal_sample_size)}",
                "Phase deadline: none",
                f"Internal phase safety guard: {PHASE_SIMULATION_SAFETY_MARKET_DAYS:,} market days",
                f"Simulation seed: {int(random_seed)}",
                f"Simulation runs: {int(simulation_runs)}",
                f"Risk of ruin: {risk_of_ruin:.2%}",
                f"Ruin 95% simulation interval: {ruin_interval[0]:.2%} to {ruin_interval[1]:.2%}",
                f"Chance to pass: {chance_to_pass:.2%}",
                f"Pass 95% simulation interval: {pass_interval[0]:.2%} to {pass_interval[1]:.2%}",
                f"Not resolved by safety guard: {unresolved_count / float(simulation_runs):.2%}",
                f"Avg ending balance: ${avg_ending_balance:,.2f}",
            ]
        )
        if avg_days_to_pass is not None:
            summary_lines.append(
                f"Avg days to pass: {avg_days_to_pass:.1f} trading days (~{weeks:.1f} weeks / ~{months:.1f} months)"
            )
        if enable_funded_mode and passed_count > 0:
            summary_lines.extend(
                [
                    "Funded continuation enabled",
                    f"Funded starting balance: {funded_start_mode}",
                    f"Funded payout frequency: {funded_payout_frequency}",
                    f"Funded minimum profit before payout: ${float(funded_min_profit):,.2f}",
                    f"Funded projection horizon: {int(funded_max_days)} market days",
                    f"Payout reach rate during projection: {funded_payout_reached_count / passed_count:.2%}",
                    f"Overall payout rate during projection: {funded_payout_reached_count / simulation_runs:.2%}",
                    f"Funded ruin during projection: {funded_ruin_after_pass_count / passed_count:.2%}",
                    f"Avg total trader payout (projection): ${sum(funded_payout_amounts) / passed_count:,.2f}",
                ]
            )
        st.markdown("### Copyable Summary")
        st.text_area(
            "Copy this into another chat for analysis",
            value="\n".join(summary_lines),
            height=300,
            key="cfd_copyable_summary",
        )


# ----------------------------------------------------------------------
#   FUTURES TAB
# ----------------------------------------------------------------------
def render_futures_tab() -> None:
    st.caption(
        "Estimate ruin risk, pass probability, and expected time‑to‑pass for prop‑firm Futures challenges."
    )

    # ------------------------------------------------------------------
    #   Account & risk profile inputs
    # ------------------------------------------------------------------
    st.markdown("### Account & Risk Profile")
    left_col, right_col = st.columns(2)

    with left_col:
        futures_balance = st.number_input(
            "Starting Balance ($)",
            min_value=1000.0,
            value=50000.0,
            step=1000.0,
            key="futures_balance",
        )
        futures_profit_target_pct = st.number_input(
            "Profit Target (%)",
            min_value=0.1,
            max_value=100.0,
            value=10.0,
            step=0.1,
            key="futures_profit_target_pct",
        )
        futures_max_drawdown_pct = st.number_input(
            "Max Drawdown (%)",
            min_value=0.1,
            max_value=30.0,
            value=6.0,
            step=0.1,
            key="futures_max_drawdown_pct",
        )
        futures_drawdown_mode = st.radio(
            "Drawdown Mode",
            options=["Static", "Trailing"],
            horizontal=True,
            key="futures_drawdown_mode",
        )

    with right_col:
        futures_win_rate_pct = st.number_input(
            "Full Win Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=0.01,
            format="%.2f",
            key="futures_win_rate_pct",
        )
        futures_avg_win_r = st.number_input(
            "Full Win Avg R",
            min_value=0.1,
            max_value=10.0,
            value=1.5,
            step=0.01,
            format="%.2f",
            key="futures_avg_win_r",
        )
        futures_partial_win_rate_pct = st.number_input(
            "Partial Win Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="futures_partial_win_rate_pct",
        )
        futures_partial_win_r = st.number_input(
            "Partial Win Avg R",
            min_value=0.01,
            max_value=10.0,
            value=0.5,
            step=0.01,
            format="%.2f",
            key="futures_partial_win_r",
        )
        futures_breakeven_rate_pct = st.number_input(
            "Breakeven Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="futures_breakeven_rate_pct",
        )
        futures_avg_loss_r = st.number_input(
            "Avg Loss R",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.01,
            format="%.2f",
            key="futures_avg_loss_r",
        )

    # ------------------------------------------------------------------
    #   Risk mode
    # ------------------------------------------------------------------
    st.markdown("### Risk Settings")
    futures_risk_mode = st.radio(
        "Risk Mode",
        options=["Percent of Balance", "Fixed Amount"],
        horizontal=True,
        key="futures_risk_mode",
    )
    if futures_risk_mode == "Percent of Balance":
        futures_risk_per_trade_pct = st.number_input(
            "Risk Per Trade (% of balance)",
            min_value=0.1,
            max_value=5.0,
            value=1.0,
            step=0.1,
            key="futures_risk_per_trade_pct",
        )
        futures_risk_per_trade_amount = None
    else:
        futures_risk_per_trade_amount = st.number_input(
            "Risk Per Trade ($)",
            min_value=10.0,
            max_value=10000.0,
            value=500.0,
            step=10.0,
            key="futures_risk_per_trade_amount",
        )
        futures_risk_per_trade_pct = None

    futures_avg_trades_per_month = st.number_input(
        "Average Trades Per Month",
        min_value=1,
        max_value=200,
        value=22,
        step=1,
        key="futures_avg_trades_per_month",
    )
    futures_random_seed = st.number_input(
        "Simulation Random Seed",
        min_value=0,
        value=42,
        step=1,
        key="futures_random_seed",
        help="Use the same seed to reproduce a result; change it to sample a different path set.",
    )

    # ------------------------------------------------------------------
    #   Validation
    # ------------------------------------------------------------------
    total_non_loss = (
        futures_win_rate_pct
        + futures_partial_win_rate_pct
        + futures_breakeven_rate_pct
    )
    if total_non_loss > 100:
        st.error(
            "Full Win % + Partial Win % + Breakeven % cannot exceed 100%."
        )
        st.stop()

    futures_loss_rate_pct = 100.0 - total_non_loss
    futures_ev = (
        (futures_win_rate_pct / 100.0) * float(futures_avg_win_r)
        + (futures_partial_win_rate_pct / 100.0) * float(futures_partial_win_r)
        - (futures_loss_rate_pct / 100.0) * float(futures_avg_loss_r)
    )
    st.caption(
        f"Outcome split — Full Win: **{futures_win_rate_pct:.2f}%** @ +{futures_avg_win_r:.2f}R | "
        f"Partial Win: **{futures_partial_win_rate_pct:.2f}%** @ +{futures_partial_win_r:.2f}R | "
        f"BE: **{futures_breakeven_rate_pct:.2f}%** | "
        f"Loss: **{futures_loss_rate_pct:.2f}%** @ -{futures_avg_loss_r:.2f}R | "
        f"Expected Value per trade: **{futures_ev:+.4f}R**"
    )
    futures_setup_day_probability, futures_expected_setup_days = estimate_setup_day_probability(
        float(futures_avg_trades_per_month),
        float(futures_win_rate_pct),
        float(futures_partial_win_rate_pct),
    )
    st.caption(
        f"Trade-frequency model: about **{futures_expected_setup_days:.1f}** active days per month "
        f"to target **{int(futures_avg_trades_per_month)}** trades."
    )

    # ------------------------------------------------------------------
    #   Simulation parameters
    # ------------------------------------------------------------------
    st.markdown("### Simulation")
    futures_simulation_runs = st.slider(
        "Simulation Runs",
        min_value=100,
        max_value=10000,
        value=2000,
        step=100,
        key="futures_simulation_runs",
    )
    futures_max_days = st.slider(
        "Max Trading Days",
        min_value=5,
        max_value=180,
        value=30,
        key="futures_max_days",
    )

    # ------------------------------------------------------------------
    #   Funded continuation
    # ------------------------------------------------------------------
    st.markdown("### Funded Account Continuation")
    futures_enable_funded_mode = st.toggle(
        "Continue Passed Runs Into Funded Account",
        value=False,
        key="futures_enable_funded_mode",
    )
    if futures_enable_funded_mode:
        futures_funded_col1, futures_funded_col2 = st.columns(2)
        with futures_funded_col1:
            futures_funded_payout_split_pct = st.number_input(
                "Payout Split (%)",
                min_value=1.0,
                max_value=100.0,
                value=80.0,
                step=1.0,
                key="futures_funded_payout_split_pct",
            )
        with futures_funded_col2:
            futures_funded_payout_frequency = st.selectbox(
                "Payout Frequency",
                options=["Weekly", "Biweekly", "Monthly"],
                index=2,
                key="futures_funded_payout_frequency",
            )
        futures_funded_max_days = st.number_input(
            "Funded Projection Horizon (Market Days)",
            min_value=21,
            max_value=1260,
            value=252,
            step=21,
            key="futures_funded_max_days",
            help="This is a reporting horizon, not an account expiry. Accounts still above their drawdown floor remain active at its end.",
        )

    # ----------------------------------------------------------------------
    #   FUTURES SIMULATION
    # ----------------------------------------------------------------------
    def simulate_futures_run() -> tuple[bool, bool, float, int, float, float]:
        """
        Simulate a single futures challenge run.

        Returns:
            ruined, passed, final_balance, days_elapsed, total_profit, best_day_profit
        """
        balance = float(futures_balance)
        initial_balance = float(futures_balance)
        target_balance = balance * (1.0 + float(futures_profit_target_pct) / 100.0)

        if futures_drawdown_mode == "Static":
            floor_balance = balance * (1.0 - float(futures_max_drawdown_pct) / 100.0)
            peak_balance = None
        else:
            peak_balance = balance
            floor_balance = peak_balance * (1.0 - float(futures_max_drawdown_pct) / 100.0)

        thresh_win = float(futures_win_rate_pct) / 100.0
        thresh_partial_win = thresh_win + float(futures_partial_win_rate_pct) / 100.0
        thresh_be = thresh_partial_win + float(futures_breakeven_rate_pct) / 100.0

        best_day_profit = 0.0

        for day in range(1, int(futures_max_days) + 1):
            day_start_balance = balance
            if rng.random() > futures_setup_day_probability:
                continue

            for trade_index in range(2):
                if futures_risk_mode == "Percent of Balance":
                    risk_amount = balance * (float(futures_risk_per_trade_pct) / 100.0)
                else:
                    risk_amount = float(futures_risk_per_trade_amount)

                r = rng.random()
                if r < thresh_win:
                    pnl = risk_amount * float(futures_avg_win_r)
                elif r < thresh_partial_win:
                    pnl = risk_amount * float(futures_partial_win_r)
                elif r < thresh_be:
                    pnl = 0.0
                else:
                    pnl = -risk_amount * float(futures_avg_loss_r)

                balance += pnl

                if balance <= floor_balance:
                    return True, False, balance, day, balance - initial_balance, best_day_profit
                if trade_index == 0 and r < thresh_partial_win:
                    break

            day_profit = balance - day_start_balance
            if day_profit > best_day_profit:
                best_day_profit = day_profit

            if futures_drawdown_mode == "Trailing" and balance > peak_balance:
                peak_balance = balance
                floor_balance = peak_balance * (1.0 - float(futures_max_drawdown_pct) / 100.0)

            if balance >= target_balance:
                return False, True, balance, day, balance - initial_balance, best_day_profit

        return False, False, balance, int(futures_max_days), balance - initial_balance, best_day_profit

    # ----------------------------------------------------------------------
    #   FUTURES FUNDED ACCOUNT
    # ----------------------------------------------------------------------
    def simulate_funded_futures_run() -> tuple[bool, int, int | None, float]:
        """
        Simulate funded account continuation for futures.

        Returns:
            ruined, payout_hits, first_payout_day
        """
        balance = float(futures_balance)
        initial_balance = float(futures_balance)

        if futures_drawdown_mode == "Static":
            floor_balance = balance * (1.0 - float(futures_max_drawdown_pct) / 100.0)
            peak_balance = None
        else:
            peak_balance = balance
            floor_balance = peak_balance * (1.0 - float(futures_max_drawdown_pct) / 100.0)

        thresh_win = float(futures_win_rate_pct) / 100.0
        thresh_partial_win = thresh_win + float(futures_partial_win_rate_pct) / 100.0
        thresh_be = thresh_partial_win + float(futures_breakeven_rate_pct) / 100.0

        payout_hits = 0
        first_payout_day = None
        total_payout_amount = 0.0

        for day in range(1, int(futures_funded_max_days) + 1):
            if rng.random() > futures_setup_day_probability:
                continue

            for trade_index in range(2):
                if futures_risk_mode == "Percent of Balance":
                    risk_amount = balance * (float(futures_risk_per_trade_pct) / 100.0)
                else:
                    risk_amount = float(futures_risk_per_trade_amount)

                r = rng.random()
                if r < thresh_win:
                    pnl = risk_amount * float(futures_avg_win_r)
                elif r < thresh_partial_win:
                    pnl = risk_amount * float(futures_partial_win_r)
                elif r < thresh_be:
                    pnl = 0.0
                else:
                    pnl = -risk_amount * float(futures_avg_loss_r)

                balance += pnl

                if balance <= floor_balance:
                    return True, payout_hits, first_payout_day, total_payout_amount
                if trade_index == 0 and r < thresh_partial_win:
                    break

            if futures_drawdown_mode == "Trailing" and balance > peak_balance:
                peak_balance = balance
                floor_balance = peak_balance * (1.0 - float(futures_max_drawdown_pct) / 100.0)

            # ----- payout check -----
            current_profit = balance - initial_balance
            if (
                day % payout_interval_days(futures_funded_payout_frequency) == 0
                and current_profit > 0
            ):
                current_payout_amount, balance = settle_profit_payout(
                    balance, initial_balance, float(futures_funded_payout_split_pct)
                )
                total_payout_amount += current_payout_amount
                payout_hits += 1
                if first_payout_day is None:
                    first_payout_day = day

        return False, payout_hits, first_payout_day, total_payout_amount

    # ------------------------------------------------------------------
    #   Run futures simulation
    # ------------------------------------------------------------------
    if st.button("Run Futures Simulation", type="primary", key="futures_run_sim_button"):
        rng = random.Random(int(futures_random_seed))
        ruined_count = 0
        passed_count = 0
        ending_balances: list[float] = []
        passing_profits: list[float] = []
        passing_best_days: list[float] = []
        funded_payout_reached_count = 0
        funded_payout_hits: list[int] = []
        funded_first_payout_days: list[int] = []
        funded_ruin_after_pass_count = 0
        funded_payout_amounts: list[float] = []

        for _ in range(int(futures_simulation_runs)):
            ruined, passed, final_balance, days_elapsed, total_profit, best_day_profit = simulate_futures_run()
            ruined_count += int(ruined)
            passed_count += int(passed)
            ending_balances.append(float(final_balance))

            if passed:
                passing_profits.append(float(total_profit))
                passing_best_days.append(float(best_day_profit))
                if futures_enable_funded_mode:
                    funded_ruined, payout_hit_count, first_payout_day, total_payout_amount = simulate_funded_futures_run()
                    funded_ruin_after_pass_count += int(funded_ruined)
                    funded_payout_hits.append(payout_hit_count)
                    funded_payout_amounts.append(total_payout_amount)
                    if payout_hit_count > 0:
                        funded_payout_reached_count += 1
                    if first_payout_day is not None:
                        funded_first_payout_days.append(int(first_payout_day))

        risk_of_ruin = ruined_count / float(futures_simulation_runs)
        chance_to_pass = passed_count / float(futures_simulation_runs)
        avg_ending_balance = (
            sum(ending_balances) / len(ending_balances) if ending_balances else 0.0
        )
        avg_profit_when_pass = (
            sum(passing_profits) / len(passing_profits) if passing_profits else 0.0
        )
        avg_best_day_when_pass = (
            sum(passing_best_days) / len(passing_best_days) if passing_best_days else 0.0
        )
        avg_best_day_share = (
            sum(
                (best_day / profit)
                for best_day, profit in zip(passing_best_days, passing_profits)
                if profit > 0
            )
            / len(passing_profits)
            if passing_profits
            else 0.0
        )

        st.markdown("### Futures Results")
        m1, m2, m3 = st.columns(3)
        m1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
        m2.metric("Chance to Pass", f"{chance_to_pass:.2%}")
        m3.metric("Avg Ending Balance", f"${avg_ending_balance:,.2f}")

        if passed_count > 0:
            st.metric("Avg Profit When Pass", f"${avg_profit_when_pass:,.2f}")
            st.metric("Avg Best‑Day Profit When Pass", f"${avg_best_day_when_pass:,.2f}")
            st.metric("Avg Best‑Day Share When Pass", f"{avg_best_day_share:.2%}")

        if futures_enable_funded_mode and passed_count > 0:
            st.markdown("### Funded Futures Results")
            fm1, fm2, fm3, fm4 = st.columns(4)
            fm1.metric(
                "Payout Reach During Projection",
                f"{funded_payout_reached_count / passed_count:.2%}",
            )
            fm2.metric(
                "Overall Payout Rate During Projection",
                f"{funded_payout_reached_count / futures_simulation_runs:.2%}",
            )
            fm3.metric(
                "Avg Payouts During Projection",
                f"{(sum(funded_payout_hits) / len(funded_payout_hits)) if funded_payout_hits else 0.0:.2f}",
            )
            fm4.metric(
                "Funded Ruin During Projection",
                f"{funded_ruin_after_pass_count / passed_count:.2%}",
            )
            st.metric(
                "Avg Total Trader Payout (Projection)",
                f"${sum(funded_payout_amounts) / passed_count:,.2f}",
            )
            st.caption(
                f"Projection horizon: **{int(futures_funded_max_days)} market days**. "
                f"Accounts still active at the horizon: **{1 - (funded_ruin_after_pass_count / passed_count):.2%}** of passed runs."
            )

            if funded_first_payout_days:
                avg_first_payout_days = sum(funded_first_payout_days) / len(
                    funded_first_payout_days
                )
                payout_weeks, payout_months = days_to_weeks_months(
                    avg_first_payout_days
                )
                st.success(
                    f"Average time to first payout: **{avg_first_payout_days:.1f} trading days** "
                    f"(~**{payout_weeks:.1f} weeks** / ~**{payout_months:.1f} months**)"
                )

        # ------------------------------------------------------------------
        #   Copy‑able summary
        # ------------------------------------------------------------------
        fut_summary = [
            "Futures Evaluation Summary",
            f"Starting balance: ${float(futures_balance):,.2f}",
            f"Profit target: {float(futures_profit_target_pct):.2f}%",
            f"Max drawdown: {float(futures_max_drawdown_pct):.2f}%",
            f"Drawdown mode: {futures_drawdown_mode}",
            f"Win rate: {float(futures_win_rate_pct):.2f}% @ +{float(futures_avg_win_r):.2f}R",
            f"Partial win rate: {float(futures_partial_win_rate_pct):.2f}% @ +{float(futures_partial_win_r):.2f}R",
            f"Breakeven rate: {float(futures_breakeven_rate_pct):.2f}%",
            f"Loss rate: {float(futures_loss_rate_pct):.2f}% @ -{float(futures_avg_loss_r):.2f}R",
            f"Risk mode: {futures_risk_mode}",
            f"Risk per trade: {float(futures_risk_per_trade_pct) if futures_risk_mode == 'Percent of Balance' else float(futures_risk_per_trade_amount):.2f}"
            + ("%" if futures_risk_mode == "Percent of Balance" else "$"),
            f"Avg trades/month: {int(futures_avg_trades_per_month)}",
            f"Simulation runs: {int(futures_simulation_runs)}",
            f"Risk of ruin: {risk_of_ruin:.2%}",
            f"Chance to pass: {chance_to_pass:.2%}",
            f"Avg ending balance: ${avg_ending_balance:,.2f}",
        ]
        if passed_count > 0:
            fut_summary.extend(
                [
                    f"Avg profit when pass: ${avg_profit_when_pass:,.2f}",
                    f"Avg best‑day profit when pass: ${avg_best_day_when_pass:,.2f}",
                    f"Avg best‑day share when pass: {avg_best_day_share:.2%}",
                ]
            )
        if futures_enable_funded_mode and passed_count > 0:
            fut_summary.extend(
                [
                    "Funded continuation enabled",
                    f"Funded projection horizon: {int(futures_funded_max_days)} market days",
                    f"Payout reach rate during projection: {funded_payout_reached_count / passed_count:.2%}",
                    f"Overall payout rate during projection: {funded_payout_reached_count / futures_simulation_runs:.2%}",
                    f"Funded ruin during projection: {funded_ruin_after_pass_count / passed_count:.2%}",
                ]
            )
        st.markdown("### Copyable Summary")
        st.text_area(
            "Copy this into another chat for analysis",
            value="\n".join([ln for ln in fut_summary if ln]),
            height=300,
            key="futures_copyable_summary",
        )


# ----------------------------------------------------------------------
#   MAIN APP LAYOUT
# ----------------------------------------------------------------------
st.title("Risk of Ruin Calculator")
mode_tabs = st.tabs(["CFD", "Futures"])

with mode_tabs[0]:
    render_cfd_tab()

with mode_tabs[1]:
    render_futures_tab()
