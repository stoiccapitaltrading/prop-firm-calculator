# -*- coding: utf-8 -*-
import random

import streamlit as st

st.set_page_config(page_title="Risk of Ruin Calculator", layout="wide")

TRADING_DAYS_PER_WEEK = 5
TRADING_DAYS_PER_MONTH = 21


def days_to_weeks_months(trading_days: float) -> tuple[float, float]:
    return trading_days / TRADING_DAYS_PER_WEEK, trading_days / TRADING_DAYS_PER_MONTH


def render_cfd_tab() -> None:
    st.caption("Estimate ruin risk, pass probability, and expected time-to-pass for prop-firm CFD challenges.")

    st.markdown(
        """
    This simulator models many account paths using your trading profile.
    A run is marked as **ruined** if it breaches either:
    - **Daily drawdown limit** (relative to start-of-day balance), or
    - **Overall drawdown limit** (relative to initial balance).
    """
    )

    challenge_type = st.radio(
        "Challenge Type",
        options=["1-Phase Challenge", "2-Phase Challenge", "3-Phase Challenge"],
        horizontal=True,
        key="cfd_challenge_type",
    )

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
        trades_per_day = st.number_input(
            "Trades Per Day",
            min_value=1,
            max_value=20,
            value=3,
            step=1,
            key="cfd_trades_per_day",
        )

    total_non_loss = win_rate_pct + partial_win_rate_pct + breakeven_rate_pct
    if total_non_loss > 100:
        st.error("Full Win % + Partial Win % + Breakeven % cannot exceed 100%.")
        st.stop()

    loss_rate_pct = 100.0 - total_non_loss
    ev = (
        (win_rate_pct / 100.0) * float(reward_risk)
        + (partial_win_rate_pct / 100.0) * float(partial_win_r)
        - (loss_rate_pct / 100.0) * 1.0
    )

    st.caption(
        f"Outcome split — Full Win: **{win_rate_pct:.2f}%** @ +{reward_risk:.2f}R | "
        f"Partial Win: **{partial_win_rate_pct:.2f}%** @ +{partial_win_r:.2f}R | "
        f"BE: **{breakeven_rate_pct:.2f}%** | "
        f"Loss: **{loss_rate_pct:.2f}%** @ -1R | "
        f"Expected Value per trade: **{ev:+.4f}R**"
    )

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
    else:
        target_phase_2_pct = 0.0

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
    else:
        target_phase_3_pct = 0.0

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

    def simulate_phase(target_profit_pct: float, use_trailing: bool = False) -> tuple[bool, bool, float, int, int]:
        balance = float(starting_balance)
        initial_balance = float(starting_balance)
        target_balance = initial_balance * (1.0 + target_profit_pct / 100.0)
        overall_floor = initial_balance * (1.0 - float(overall_drawdown_pct) / 100.0)
        peak_balance = initial_balance

        thresh_win = float(win_rate_pct) / 100.0
        thresh_partial_win = thresh_win + float(partial_win_rate_pct) / 100.0
        thresh_be = thresh_partial_win + float(breakeven_rate_pct) / 100.0

        risk_fraction = float(risk_per_trade_pct) / 100.0
        max_consec_losses = 0
        current_consec_losses = 0

        for day in range(1, int(max_days_per_phase) + 1):
            day_start_balance = balance
            daily_floor = day_start_balance * (1.0 - float(daily_drawdown_pct) / 100.0)

            for _ in range(int(trades_per_day)):
                risk_amount = balance * risk_fraction
                r = random.random()

                if r < thresh_win:
                    pnl = risk_amount * float(reward_risk)
                    current_consec_losses = 0
                elif r < thresh_partial_win:
                    pnl = risk_amount * float(partial_win_r)
                    current_consec_losses = 0
                elif r < thresh_be:
                    pnl = 0.0
                else:
                    pnl = -risk_amount
                    current_consec_losses += 1
                    if current_consec_losses > max_consec_losses:
                        max_consec_losses = current_consec_losses

                balance += pnl

                if balance <= overall_floor or balance <= daily_floor:
                    return True, False, balance, day, max_consec_losses
                if balance >= target_balance:
                    return False, True, balance, day, max_consec_losses

            if use_trailing and balance > peak_balance:
                peak_balance = balance
                new_floor = peak_balance * (1.0 - float(overall_drawdown_pct) / 100.0)
                if new_floor > overall_floor:
                    overall_floor = new_floor

        return False, False, balance, int(max_days_per_phase), max_consec_losses

    def simulate_challenge() -> tuple[bool, bool, bool, bool, float, int | None, int, int]:
        ruined, p1_passed, bal1, p1_days, p1_consec = simulate_phase(
            target_phase_1_pct,
            use_trailing=use_eod_trailing_stop,
        )
        if ruined:
            return True, False, False, False, bal1, None, p1_days, p1_consec
        if not p1_passed:
            return False, False, False, False, bal1, None, p1_days, p1_consec
        if challenge_type == "1-Phase Challenge":
            return False, True, False, False, bal1, p1_days, p1_days, p1_consec

        ruined, p2_passed, bal2, p2_days, p2_consec = simulate_phase(target_phase_2_pct, use_trailing=False)
        total_days = p1_days + p2_days
        max_consec = max(p1_consec, p2_consec)
        if ruined:
            return True, False, True, False, bal2, None, total_days, max_consec
        if not p2_passed:
            return False, False, True, False, bal2, None, total_days, max_consec
        if challenge_type == "2-Phase Challenge":
            return False, True, True, False, bal2, total_days, total_days, max_consec

        ruined, p3_passed, bal3, p3_days, p3_consec = simulate_phase(target_phase_3_pct, use_trailing=False)
        total_days = p1_days + p2_days + p3_days
        max_consec = max(max_consec, p3_consec)
        if ruined:
            return True, False, True, True, bal3, None, total_days, max_consec
        if p3_passed:
            return False, True, True, True, bal3, total_days, total_days, max_consec
        return False, False, True, True, bal3, None, total_days, max_consec

    if st.button("Run CFD Simulation", type="primary", key="cfd_run_sim_button"):
        ruined_count = 0
        passed_count = 0
        reached_phase_2_count = 0
        reached_phase_3_count = 0
        ending_balances: list[float] = []
        pass_days: list[int] = []
        all_consec_losses: list[int] = []

        for _ in range(int(simulation_runs)):
            ruined, passed, reached_p2, reached_p3, final_balance, days_to_pass, _total_days, max_consec = (
                simulate_challenge()
            )
            ruined_count += int(ruined)
            passed_count += int(passed)
            reached_phase_2_count += int(reached_p2)
            reached_phase_3_count += int(reached_p3)
            ending_balances.append(float(final_balance))
            all_consec_losses.append(max_consec)
            if days_to_pass is not None:
                pass_days.append(int(days_to_pass))

        risk_of_ruin = ruined_count / float(simulation_runs)
        chance_to_pass = passed_count / float(simulation_runs)
        survival_rate = 1.0 - risk_of_ruin
        avg_ending_balance = sum(ending_balances) / len(ending_balances) if ending_balances else 0.0

        st.markdown("### CFD Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
        m2.metric("Chance to Pass", f"{chance_to_pass:.2%}")
        m3.metric("Survival Rate", f"{survival_rate:.2%}")
        m4.metric("Avg Ending Balance", f"${avg_ending_balance:,.2f}")

        if challenge_type in ("2-Phase Challenge", "3-Phase Challenge"):
            p2_prob = reached_phase_2_count / float(simulation_runs)
            if challenge_type == "3-Phase Challenge":
                pm1, pm2 = st.columns(2)
                pm1.metric("Reached Phase 2", f"{p2_prob:.2%}")
                pm2.metric("Reached Phase 3", f"{reached_phase_3_count / float(simulation_runs):.2%}")
            else:
                st.metric("Reached Phase 2", f"{p2_prob:.2%}")

        avg_days_to_pass = (sum(pass_days) / len(pass_days)) if pass_days else None
        if avg_days_to_pass is not None:
            weeks, months = days_to_weeks_months(avg_days_to_pass)
            st.success(
                f"Average time to pass: **{avg_days_to_pass:.1f} trading days** "
                f"(~**{weeks:.1f} weeks** / ~**{months:.1f} months**)"
            )
        else:
            st.warning("No passing paths in this run, so average time-to-pass is unavailable.")

        st.markdown("### Consecutive Loss Streak Analysis")

        avg_consec = sum(all_consec_losses) / len(all_consec_losses) if all_consec_losses else 0
        max_consec_overall = max(all_consec_losses) if all_consec_losses else 0

        buckets = {"1-3": 0, "4-6": 0, "7-10": 0, "11+": 0}
        for value in all_consec_losses:
            if value <= 3:
                buckets["1-3"] += 1
            elif value <= 6:
                buckets["4-6"] += 1
            elif value <= 10:
                buckets["7-10"] += 1
            else:
                buckets["11+"] += 1

        cl1, cl2, cl3, cl4, cl5 = st.columns(5)
        cl1.metric("Avg Max Streak", f"{avg_consec:.1f} losses")
        cl2.metric("Worst Streak (all runs)", f"{max_consec_overall} losses")
        cl3.metric("Streak 1-3", f"{buckets['1-3'] / simulation_runs:.1%} of runs")
        cl4.metric("Streak 4-6", f"{buckets['4-6'] / simulation_runs:.1%} of runs")
        cl5.metric("Streak 7+", f"{(buckets['7-10'] + buckets['11+']) / simulation_runs:.1%} of runs")

        st.caption(
            "The streak tracker counts the longest consecutive losing run encountered across the entire challenge path. "
            "Breakeven trades do not reset or extend the streak."
        )

        st.info("Tip: Lower risk per trade and/or fewer trades per day usually lowers ruin risk.")


def render_futures_tab() -> None:
    st.caption("Estimate ruin risk and pass probability for a one-step futures evaluation.")

    st.markdown(
        """
    This simulator uses a dedicated futures rule set.
    A run only **passes** when the account hits the profit target and, if enabled,
    also satisfies the consistency rule. If the target is reached first but the
    consistency rule is still broken, the simulation keeps trading until both
    conditions are met or the account fails.
    """
    )

    st.markdown("### Futures Evaluation Setup")
    left_col, right_col = st.columns(2)

    with left_col:
        futures_balance = st.number_input(
            "Starting Balance ($)",
            min_value=1000.0,
            value=50000.0,
            step=1000.0,
            key="futures_starting_balance",
        )
        futures_profit_target_pct = st.number_input(
            "Profit Target (%)",
            min_value=0.1,
            max_value=100.0,
            value=6.0,
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
        futures_drawdown_mode = st.selectbox(
            "Drawdown Mode",
            options=["Static", "Trailing Equity", "Trailing EOD Equity"],
            index=1,
            key="futures_drawdown_mode",
            help="Static keeps the floor fixed. Trailing Equity follows intraday balance highs. Trailing EOD Equity only updates from end-of-day closing highs.",
        )
        use_consistency_rule = st.toggle(
            "Enable Consistency Rule",
            value=True,
            key="futures_use_consistency_rule",
            help="When enabled, no single trading day may contribute more than the allowed percentage of total profit at pass.",
        )
        consistency_threshold_pct = st.number_input(
            "Max Profit From One Day (%)",
            min_value=1.0,
            max_value=100.0,
            value=40.0,
            step=1.0,
            key="futures_consistency_threshold_pct",
            disabled=not use_consistency_rule,
        )

    with right_col:
        futures_win_rate_pct = st.number_input(
            "Win Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=45.0,
            step=0.01,
            format="%.2f",
            key="futures_win_rate_pct",
        )
        futures_avg_win_r = st.number_input(
            "Average Win (R)",
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
            "Average Partial Win (R)",
            min_value=0.01,
            max_value=10.0,
            value=0.5,
            step=0.01,
            format="%.2f",
            key="futures_partial_win_r",
        )
        futures_avg_loss_r = st.number_input(
            "Average Loss (R)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.01,
            format="%.2f",
            key="futures_avg_loss_r",
        )
        futures_risk_per_trade_pct = st.number_input(
            "Risk Per Trade (% of balance)",
            min_value=0.1,
            max_value=5.0,
            value=0.5,
            step=0.1,
            key="futures_risk_per_trade_pct",
        )
        futures_trades_per_day = st.number_input(
            "Trades Per Day",
            min_value=1,
            max_value=20,
            value=2,
            step=1,
            key="futures_trades_per_day",
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

    futures_non_loss_pct = futures_win_rate_pct + futures_partial_win_rate_pct + futures_breakeven_rate_pct
    if futures_non_loss_pct > 100:
        st.error("Win Rate % + Partial Win Rate % + Breakeven Rate % cannot exceed 100%.")
        st.stop()

    futures_profit_target_amount = float(futures_balance) * (float(futures_profit_target_pct) / 100.0)
    futures_max_drawdown_amount = float(futures_balance) * (float(futures_max_drawdown_pct) / 100.0)

    amount_col1, amount_col2 = st.columns(2)
    amount_col1.metric("Profit Target ($)", f"${futures_profit_target_amount:,.2f}")
    amount_col2.metric("Max Drawdown ($)", f"${futures_max_drawdown_amount:,.2f}")

    futures_loss_rate_pct = 100.0 - futures_non_loss_pct
    futures_ev = (
        (futures_win_rate_pct / 100.0) * float(futures_avg_win_r)
        + (futures_partial_win_rate_pct / 100.0) * float(futures_partial_win_r)
        - (futures_loss_rate_pct / 100.0) * float(futures_avg_loss_r)
    )
    consistency_summary = (
        f"Consistency: on ({consistency_threshold_pct:.0f}% max one-day contribution)"
        if use_consistency_rule
        else "Consistency: off"
    )

    st.caption(
        f"Starting balance: **${futures_balance:,.0f}** | "
        f"Target: **{futures_profit_target_pct:.1f}%** | "
        f"Drawdown: **{futures_max_drawdown_pct:.1f}%** ({futures_drawdown_mode}) | "
        f"{consistency_summary} | "
        f"Expected Value per trade: **{futures_ev:+.4f}R**"
    )

    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        futures_simulation_runs = st.slider(
            "Simulation Runs",
            min_value=100,
            max_value=10000,
            value=2000,
            step=100,
            key="futures_simulation_runs",
        )
    with sim_col2:
        futures_max_days = st.slider(
            "Max Trading Days",
            min_value=5,
            max_value=180,
            value=30,
            key="futures_max_days",
        )

    run_futures_simulation = st.button("Run Futures Simulation", type="primary", key="futures_run_sim_button")

    def consistency_is_met(total_profit: float, best_day_profit: float) -> bool:
        if not use_consistency_rule:
            return True
        if total_profit <= 0:
            return False
        return best_day_profit <= total_profit * (float(consistency_threshold_pct) / 100.0)

    def simulate_futures_run() -> tuple[bool, bool, float, int, float, float]:
        balance = float(futures_balance)
        initial_balance = float(futures_balance)
        profit_target = initial_balance * (float(futures_profit_target_pct) / 100.0)
        drawdown_amount = initial_balance * (float(futures_max_drawdown_pct) / 100.0)
        floor_balance = initial_balance - drawdown_amount
        peak_balance = initial_balance

        win_threshold = float(futures_win_rate_pct) / 100.0
        partial_win_threshold = win_threshold + float(futures_partial_win_rate_pct) / 100.0
        breakeven_threshold = partial_win_threshold + float(futures_breakeven_rate_pct) / 100.0
        risk_fraction = float(futures_risk_per_trade_pct) / 100.0
        best_day_profit = 0.0

        for day in range(1, int(futures_max_days) + 1):
            day_profit = 0.0

            for _ in range(int(futures_trades_per_day)):
                risk_amount = balance * risk_fraction
                outcome = random.random()

                if outcome < win_threshold:
                    pnl = risk_amount * float(futures_avg_win_r)
                elif outcome < partial_win_threshold:
                    pnl = risk_amount * float(futures_partial_win_r)
                elif outcome < breakeven_threshold:
                    pnl = 0.0
                else:
                    pnl = -risk_amount * float(futures_avg_loss_r)

                balance += pnl
                day_profit += pnl

                if futures_drawdown_mode == "Trailing Equity" and balance > peak_balance:
                    peak_balance = balance
                    trailing_floor = peak_balance - drawdown_amount
                    if trailing_floor > floor_balance:
                        floor_balance = trailing_floor

                if balance <= floor_balance:
                    total_profit = balance - initial_balance
                    return True, False, balance, day, total_profit, best_day_profit

            if day_profit > best_day_profit:
                best_day_profit = day_profit

            if futures_drawdown_mode == "Trailing EOD Equity" and balance > peak_balance:
                peak_balance = balance
                trailing_floor = peak_balance - drawdown_amount
                if trailing_floor > floor_balance:
                    floor_balance = trailing_floor

            total_profit = balance - initial_balance
            if total_profit >= profit_target and consistency_is_met(total_profit, best_day_profit):
                return False, True, balance, day, total_profit, best_day_profit

        total_profit = balance - initial_balance
        return False, False, balance, int(futures_max_days), total_profit, best_day_profit

    if run_futures_simulation:
        ruined_count = 0
        passed_count = 0
        ending_balances: list[float] = []
        pass_days: list[int] = []
        ending_profits: list[float] = []
        passing_profits: list[float] = []
        passing_best_days: list[float] = []

        for _ in range(int(futures_simulation_runs)):
            ruined, passed, final_balance, days_elapsed, total_profit, best_day_profit = simulate_futures_run()
            ruined_count += int(ruined)
            passed_count += int(passed)
            ending_balances.append(float(final_balance))
            ending_profits.append(float(total_profit))
            if passed:
                pass_days.append(int(days_elapsed))
                passing_profits.append(float(total_profit))
                passing_best_days.append(float(best_day_profit))

        risk_of_ruin = ruined_count / float(futures_simulation_runs)
        chance_to_pass = passed_count / float(futures_simulation_runs)
        survival_rate = 1.0 - risk_of_ruin
        avg_ending_balance = sum(ending_balances) / len(ending_balances) if ending_balances else 0.0
        avg_ending_profit = sum(ending_profits) / len(ending_profits) if ending_profits else 0.0

        st.markdown("### Futures Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
        m2.metric("Chance to Pass", f"{chance_to_pass:.2%}")
        m3.metric("Survival Rate", f"{survival_rate:.2%}")
        m4.metric("Avg Ending Balance", f"${avg_ending_balance:,.2f}")

        st.metric("Avg Ending Profit", f"${avg_ending_profit:,.2f}")

        avg_days_to_pass = (sum(pass_days) / len(pass_days)) if pass_days else None
        if avg_days_to_pass is not None:
            weeks, months = days_to_weeks_months(avg_days_to_pass)
            st.success(
                f"Average time to pass: **{avg_days_to_pass:.1f} trading days** "
                f"(~**{weeks:.1f} weeks** / ~**{months:.1f} months**)"
            )
        else:
            st.warning("No passing paths in this run, so average time-to-pass is unavailable.")

        if use_consistency_rule and passing_profits:
            avg_profit_at_pass = sum(passing_profits) / len(passing_profits)
            avg_best_day_profit = sum(passing_best_days) / len(passing_best_days)
            avg_best_day_share = sum(
                (best_day / profit) for best_day, profit in zip(passing_best_days, passing_profits) if profit > 0
            ) / len(passing_profits)

            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Profit at Pass", f"${avg_profit_at_pass:,.2f}")
            c2.metric("Avg Best Day Profit", f"${avg_best_day_profit:,.2f}")
            c3.metric("Avg Best Day Share", f"{avg_best_day_share:.2%}")

            st.caption(
                "Consistency is checked at pass time by comparing your best single trading day to total profit. "
                "If the threshold is still broken after hitting target, the simulation keeps trading until the ratio improves or the account fails."
            )


st.title("Risk of Ruin Calculator")
mode_tabs = st.tabs(["CFD", "Futures"])

with mode_tabs[0]:
    render_cfd_tab()

with mode_tabs[1]:
    render_futures_tab()
