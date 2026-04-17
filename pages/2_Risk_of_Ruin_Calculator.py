# -*- coding: utf-8 -*-
import random

import streamlit as st

st.set_page_config(page_title="Risk of Ruin Calculator", layout="wide")

TRADING_DAYS_PER_WEEK = 5
TRADING_DAYS_PER_MONTH = 21
BIWEEKLY_TRADING_DAYS = 10


def days_to_weeks_months(trading_days: float) -> tuple[float, float]:
    """Convert trading‑days to weeks and months (approx)."""
    return trading_days / TRADING_DAYS_PER_WEEK, trading_days / TRADING_DAYS_PER_MONTH


def estimate_setup_day_probability(
    avg_trades_per_month: float, win_rate_pct: float, partial_win_rate_pct: float
) -> tuple[float, float]:
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
    ev = (
        (win_rate_pct / 100.0) * float(reward_risk)
        + (partial_win_rate_pct / 100.0) * float(partial_win_r)
        - (loss_rate_pct / 100.0) * 1.0
    )
    setup_day_probability, expected_setup_days = estimate_setup_day_probability(
        float(avg_trades_per_month),
        float(win_rate_pct),
        float(partial_win_rate_pct),
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
        min_profit_day_pct_phase_1 = st.number_input(
            "Min Profitable‑Day % (Phase 1)",
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
            min_profit_day_pct_phase_2 = st.number_input(
                "Min Profitable‑Day % (Phase 2)",
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
            min_profit_day_pct_phase_3 = st.number_input(
                "Min Profitable‑Day % (Phase 3)",
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
            "EOD trailing stop is active for Phase 1. At the end of each trading day, "
            "if your closing balance is a new equity high, the overall floor moves up to "
            "`new_high x (1 - overall_drawdown_pct%)`. The floor never moves down."
        )

    # ------------------------------------------------------------------
    #   Funded‑account continuation toggle (no payout target)
    # ------------------------------------------------------------------
    st.markdown("### Funded Account Continuation")
    enable_funded_mode = st.toggle(
        "Continue Passed Runs Into Funded Account",
        value=False,
        key="cfd_enable_funded_mode",
        help="After a challenge pass, continue the same Monte Carlo run **but start from a fresh balance**. "
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
            funded_payout_frequency = st.selectbox(
                "Payout Frequency",
                options=["Weekly", "Biweekly", "Monthly"],
                index=2,
                key="cfd_funded_payout_frequency",
            )
        funded_max_days = st.number_input(
            "Max Trading Days (Funded)",
            min_value=10,
            max_value=500,
            value=90,
            step=10,
            key="cfd_funded_max_days",
        )

    # ----------------------------------------------------------------------
    #   PHASE SIMULATION – single phase logic
    # ----------------------------------------------------------------------
    def simulate_phase(
        target_profit_pct: float,
        min_days: int,
        min_profit_day_pct: float,
        use_trailing: bool,
        prev_consec_losses: int,
    ) -> tuple[bool, bool, float, int, int, int]:
        """
        Simulate a single phase.

        Returns:
            ruined, passed, final_balance, days_elapsed, max_consec_losses, current_consec_losses
        """
        # ----- 1️⃣  Initial state -----
        balance = float(starting_balance)
        overall_floor = balance * (1.0 - float(overall_drawdown_pct) / 100.0)
        peak_balance = balance
        target_balance = balance * (1.0 + float(target_profit_pct) / 100.0)

        # ----- 2️⃣  Outcome thresholds -----
        thresh_win = float(win_rate_pct) / 100.0
        thresh_partial_win = thresh_win + float(partial_win_rate_pct) / 100.0
        thresh_be = thresh_partial_win + float(breakeven_rate_pct) / 100.0

        risk_fraction = float(risk_per_trade_pct) / 100.0

        # ----- 3️⃣  Streak bookkeeping – carry over from previous phase -----
        max_consec_losses = prev_consec_losses
        current_consec_losses = prev_consec_losses

        # ----- 4️⃣  Tracking for minimum‑profit‑day requirement -----
        profit_day_met = False
        profit_day_threshold = float(min_profit_day_pct) / 100.0 * starting_balance

        # ----- 5️⃣  Day‑by‑day loop -----
        for day in range(1, int(max_days_per_phase) + 1):
            day_start_balance = balance
            daily_floor = day_start_balance * (1.0 - float(daily_drawdown_pct) / 100.0)

            # ----- 5a.  Setup‑day chance -----
            if random.random() > setup_day_probability:
                # EOD trailing‑stop handling (unchanged)
                if use_trailing and balance > peak_balance:
                    peak_balance = balance
                    new_floor = peak_balance * (1.0 - float(overall_drawdown_pct) / 100.0)
                    if new_floor > overall_floor:
                        overall_floor = new_floor
                continue

            # ----- 5b.  Up to two trades per day -----
            for trade_index in range(2):
                risk_amount = balance * risk_fraction
                r = random.random()

                if r < thresh_win:
                    pnl = risk_amount * float(reward_risk)
                    outcome = "full_win"
                    current_consec_losses = 0
                elif r < thresh_partial_win:
                    pnl = risk_amount * float(partial_win_r)
                    outcome = "partial_win"
                    current_consec_losses = 0
                elif r < thresh_be:
                    pnl = 0.0
                    outcome = "breakeven"
                    # breakeven does NOT reset the streak
                else:
                    pnl = -risk_amount
                    outcome = "loss"
                    current_consec_losses += 1
                    if current_consec_losses > max_consec_losses:
                        max_consec_losses = current_consec_losses

                balance += pnl

                # ----- 5c.  Draw‑down checks -----
                if balance <= overall_floor or balance <= daily_floor:
                    return True, False, balance, day, max_consec_losses, current_consec_losses
                # Do NOT prematurely return on profit target—still need min‑day constraints

                # ----- 5d.  Full/partial win ends the day -----
                if trade_index == 0 and outcome in ("full_win", "partial_win"):
                    break

            # ----- 5e.  End‑of‑day processing -----
            day_profit = balance - day_start_balance
            if day_profit > 0 and day_profit >= profit_day_threshold:
                profit_day_met = True

            if use_trailing and balance > peak_balance:
                peak_balance = balance
                new_floor = peak_balance * (1.0 - float(overall_drawdown_pct) / 100.0)
                if new_floor > overall_floor:
                    overall_floor = new_floor

            # ----- 5f.  Check whether the phase can be considered passed -----
            if (
                balance >= target_balance          # hit profit target
                and day >= min_days                # satisfied minimum trading days
                and (min_profit_day_pct == 0.0 or profit_day_met)  # optional profitable‑day rule
            ):
                return False, True, balance, day, max_consec_losses, current_consec_losses

        # ---------- Phase finished without hitting target or ruin ----------
        return False, False, balance, int(max_days_per_phase), max_consec_losses, current_consec_losses

    # ----------------------------------------------------------------------
    #   CHALLENGE orchestrator (runs 1‑, 2‑, or 3‑phase challenge)
    # ----------------------------------------------------------------------
    def simulate_challenge() -> tuple[bool, bool, float, int | None]:
        """
        Run the selected challenge.

        Returns:
            ruined, passed, final_balance, days_to_pass (cumulative days when the pass occurs)
        """
        # ---------- Phase 1 ----------
        ruined, passed, bal, days, max_consec, cur_consec = simulate_phase(
            target_phase_1_pct,
            min_days_phase_1,
            min_profit_day_pct_phase_1,
            use_trailing=use_eod_trailing_stop,
            prev_consec_losses=0,
        )
        total_days = days
        days_to_pass = None

        if ruined:
            return True, False, bal, None
        if not passed:
            return False, False, bal, None
        if challenge_type == "1-Phase Challenge":
            return False, True, bal, total_days

        # ---------- Phase 2 ----------
        ruined, passed, bal, days, max_consec, cur_consec = simulate_phase(
            target_phase_2_pct,
            min_days_phase_2,
            min_profit_day_pct_phase_2,
            use_trailing=False,
            prev_consec_losses=cur_consec,
        )
        total_days += days
        if passed:
            days_to_pass = total_days

        if ruined:
            return True, False, bal, None
        if not passed:
            return False, False, bal, None
        if challenge_type == "2-Phase Challenge":
            return False, True, bal, days_to_pass

        # ---------- Phase 3 ----------
        ruined, passed, bal, days, max_consec, cur_consec = simulate_phase(
            target_phase_3_pct,
            min_days_phase_3,
            min_profit_day_pct_phase_3,
            use_trailing=False,
            prev_consec_losses=cur_consec,
        )
        total_days += days
        if passed:
            days_to_pass = total_days

        if ruined:
            return True, False, bal, None
        if passed:
            return False, True, bal, days_to_pass

        # If we get here the 3‑phase challenge never passed
        return False, False, bal, None

    # ----------------------------------------------------------------------
    #   FUNDED‑ACCOUNT simulation – start from a *reset* balance, withdraw whatever profit
    # ----------------------------------------------------------------------
    def simulate_funded_account() -> tuple[bool, int, int | None]:
        """
        Run the funded‑account portion **continuing the same random stream**,
        but **resetting the balance to the original starting balance**.
        Withdraw whatever profit is available on each payout‑check day.

        Returns:
            ruined, payout_hits, first_payout_day
        """
        balance = float(starting_balance)
        initial_balance = float(starting_balance)

        overall_floor = initial_balance * (1.0 - float(overall_drawdown_pct) / 100.0)

        thresh_win = float(win_rate_pct) / 100.0
        thresh_partial_win = thresh_win + float(partial_win_rate_pct) / 100.0
        thresh_be = thresh_partial_win + float(breakeven_rate_pct) / 100.0

        risk_fraction = float(risk_per_trade_pct) / 100.0

        payout_hits = 0
        first_payout_day = None

        for day in range(1, int(funded_max_days) + 1):
            day_start_balance = balance
            daily_floor = day_start_balance * (1.0 - float(daily_drawdown_pct) / 100.0)

            if random.random() > setup_day_probability:
                continue

            for trade_index in range(2):
                risk_amount = balance * risk_fraction
                outcome = random.random()

                if outcome < thresh_win:
                    pnl = risk_amount * float(reward_risk)
                    outcome_type = "full_win"
                elif outcome < thresh_partial_win:
                    pnl = risk_amount * float(partial_win_r)
                    outcome_type = "partial_win"
                elif outcome < thresh_be:
                    pnl = 0.0
                    outcome_type = "breakeven"
                else:
                    pnl = -risk_amount
                    outcome_type = "loss"

                balance += pnl

                if balance <= overall_floor or balance <= daily_floor:
                    return True, payout_hits, first_payout_day

                if trade_index == 0 and outcome_type in ("full_win", "partial_win"):
                    break

            # ----- payout check : withdraw whatever profit is present -----
            current_profit = balance - initial_balance
            if (
                day % payout_interval_days(funded_payout_frequency) == 0
                and current_profit > 0
            ):
                balance -= current_profit * (float(funded_payout_split_pct) / 100.0)
                payout_hits += 1
                if first_payout_day is None:
                    first_payout_day = day

        return False, payout_hits, first_payout_day

    # ----------------------------------------------------------------------
    #   RUN BUTTON – collect results and display them
    # ----------------------------------------------------------------------
    if st.button("Run CFD Simulation", type="primary", key="cfd_run_sim_button"):
        ruined_count = 0
        passed_count = 0
        ending_balances: list[float] = []
        pass_days: list[int] = []
        funded_payout_reached_count = 0
        funded_payout_hits: list[int] = []
        funded_first_payout_days: list[int] = []
        funded_ruin_after_pass_count = 0

        for _ in range(int(simulation_runs)):
            ruined, passed, final_balance, days_to_pass = simulate_challenge()

            ruined_count += int(ruined)
            passed_count += int(passed)
            ending_balances.append(float(final_balance))

            if passed:
                pass_days.append(int(days_to_pass))
                if enable_funded_mode:
                    funded_ruined, payout_hit_count, first_payout_day = simulate_funded_account()
                    funded_ruin_after_pass_count += int(funded_ruined)
                    funded_payout_hits.append(payout_hit_count)
                    if payout_hit_count > 0:
                        funded_payout_reached_count += 1
                    if first_payout_day is not None:
                        funded_first_payout_days.append(int(first_payout_day))

        # ---------- Summary statistics ----------
        risk_of_ruin = ruined_count / float(simulation_runs)
        chance_to_pass = passed_count / float(simulation_runs)
        avg_ending_balance = (
            sum(ending_balances) / len(ending_balances) if ending_balances else 0.0
        )

        st.markdown("### CFD Results")
        m1, m2, m3 = st.columns(3)
        m1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
        m2.metric("Chance to Pass", f"{chance_to_pass:.2%}")
        m3.metric("Avg Ending Balance", f"${avg_ending_balance:,.2f}")

        avg_days_to_pass = (
            sum(pass_days) / len(pass_days) if pass_days else None
        )
        if avg_days_to_pass is not None:
            weeks, months = days_to_weeks_months(avg_days_to_pass)
            st.success(
                f"Average time to pass the entire challenge: **{avg_days_to_pass:.1f} trading days** "
                f"(~**{weeks:.1f} weeks** / ~**{months:.1f} months**)"
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
                "Payout Reach Rate",
                f"{funded_payout_reached_count / passed_count:.2%}",
            )
            fm2.metric(
                "Overall Payout Rate",
                f"{funded_payout_reached_count / simulation_runs:.2%}",
            )
            fm3.metric(
                "Avg Payouts After Pass",
                f"{(sum(funded_payout_hits) / len(funded_payout_hits)) if funded_payout_hits else 0.0:.2f}",
            )
            fm4.metric(
                "Funded Ruin After Pass",
                f"{funded_ruin_after_pass_count / passed_count:.2%}",
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
        ]
        if challenge_type in ("2-Phase Challenge", "3-Phase Challenge"):
            summary_lines.append(f"Phase 2 target: {float(target_phase_2_pct):.2f}%")
        if challenge_type == "3-Phase Challenge":
            summary_lines.append(f"Phase 3 target: {float(target_phase_3_pct):.2f}%")
        summary_lines.extend(
            [
                f"Daily drawdown: {float(daily_drawdown_pct):.2f}%",
                f"Overall drawdown: {float(overall_drawdown_pct):.2f}%",
                f"Win rate: {float(win_rate_pct):.2f}% @ +{float(reward_risk):.2f}R",
                f"Partial win rate: {float(partial_win_rate_pct):.2f}% @ +{float(partial_win_r):.2f}R",
                f"Breakeven rate: {float(breakeven_rate_pct):.2f}%",
                f"Loss rate: {float(loss_rate_pct):.2f}% @ -1R",
                f"Risk per trade: {float(risk_per_trade_pct):.2f}%",
                f"Avg trades/month: {int(avg_trades_per_month)}",
                f"Simulation runs: {int(simulation_runs)}",
                f"Risk of ruin: {risk_of_ruin:.2%}",
                f"Chance to pass: {chance_to_pass:.2%}",
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
                    f"Payout reach rate after pass: {funded_payout_reached_count / passed_count:.2%}",
                    f"Overall payout rate: {funded_payout_reached_count / simulation_runs:.2%}",
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
            "Max Trading Days (Funded)",
            min_value=10,
            max_value=500,
            value=90,
            step=10,
            key="futures_funded_max_days",
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
            num_trades = random.randint(0, 3)

            for _ in range(num_trades):
                if futures_risk_mode == "Percent of Balance":
                    risk_amount = balance * (float(futures_risk_per_trade_pct) / 100.0)
                else:
                    risk_amount = float(futures_risk_per_trade_amount)

                r = random.random()
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
    def simulate_funded_futures_run() -> tuple[bool, int, int | None]:
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

        for day in range(1, int(futures_funded_max_days) + 1):
            num_trades = random.randint(0, 3)

            for _ in range(num_trades):
                if futures_risk_mode == "Percent of Balance":
                    risk_amount = balance * (float(futures_risk_per_trade_pct) / 100.0)
                else:
                    risk_amount = float(futures_risk_per_trade_amount)

                r = random.random()
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
                    return True, payout_hits, first_payout_day

            if futures_drawdown_mode == "Trailing" and balance > peak_balance:
                peak_balance = balance
                floor_balance = peak_balance * (1.0 - float(futures_max_drawdown_pct) / 100.0)

            # ----- payout check -----
            current_profit = balance - initial_balance
            if (
                day % payout_interval_days(futures_funded_payout_frequency) == 0
                and current_profit > 0
            ):
                current_payout_amount = current_profit * (
                    float(futures_funded_payout_split_pct) / 100.0
                )
                balance -= current_payout_amount
                payout_hits += 1
                if first_payout_day is None:
                    first_payout_day = day

        return False, payout_hits, first_payout_day

    # ------------------------------------------------------------------
    #   Run futures simulation
    # ------------------------------------------------------------------
    if st.button("Run Futures Simulation", type="primary", key="futures_run_sim_button"):
        ruined_count = 0
        passed_count = 0
        ending_balances: list[float] = []
        passing_profits: list[float] = []
        passing_best_days: list[float] = []
        funded_payout_reached_count = 0
        funded_payout_hits: list[int] = []
        funded_first_payout_days: list[int] = []
        funded_ruin_after_pass_count = 0

        for _ in range(int(futures_simulation_runs)):
            ruined, passed, final_balance, days_elapsed, total_profit, best_day_profit = simulate_futures_run()
            ruined_count += int(ruined)
            passed_count += int(passed)
            ending_balances.append(float(final_balance))

            if passed:
                passing_profits.append(float(total_profit))
                passing_best_days.append(float(best_day_profit))
                if futures_enable_funded_mode:
                    funded_ruined, payout_hit_count, first_payout_day = simulate_funded_futures_run()
                    funded_ruin_after_pass_count += int(funded_ruined)
                    funded_payout_hits.append(payout_hit_count)
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
                "Payout Reach Rate",
                f"{funded_payout_reached_count / passed_count:.2%}",
            )
            fm2.metric(
                "Overall Payout Rate",
                f"{funded_payout_reached_count / futures_simulation_runs:.2%}",
            )
            fm3.metric(
                "Avg Payouts After Pass",
                f"{(sum(funded_payout_hits) / len(funded_payout_hits)) if funded_payout_hits else 0.0:.2f}",
            )
            fm4.metric(
                "Funded Ruin After Pass",
                f"{funded_ruin_after_pass_count / passed_count:.2%}",
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
                    f"Payout reach rate after pass: {funded_payout_reached_count / passed_count:.2%}",
                    f"Overall payout rate: {funded_payout_reached_count / futures_simulation_runs:.2%}",
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
