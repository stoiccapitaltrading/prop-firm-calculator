import random
 codex/fix-risk-of-ruin-page-issue-4hzh5f


 main
import streamlit as st

st.set_page_config(page_title="Risk of Ruin Calculator", layout="centered")

 codex/fix-risk-of-ruin-page-issue-4hzh5f
st.title("Risk of Ruin Calculator")

st.title("⚠️ Risk of Ruin Calculator")
 main
st.caption("Estimate your chance of violating prop-firm drawdown rules.")

st.markdown(
    """
This simulator uses your win rate, risk size, and reward/risk profile to run many account paths.
A run is marked **ruined** if it breaches either:
- **Daily drawdown limit** (loss from start-of-day balance), or
- **Overall drawdown limit** (loss from initial balance).
"""
)

 codex/fix-risk-of-ruin-page-issue-4hzh5f

codex/fix-risk-of-ruin-page-issue-iyl7gn
 main
challenge_type = st.radio(
    "Challenge Type",
    options=["1-Phase Challenge", "2-Phase Challenge"],
    horizontal=True,
)

 codex/fix-risk-of-ruin-page-issue-4hzh5f
phase_presets = {
    "1-Phase Challenge": {"phase_1": 8.0, "phase_2": 0.0},
    "2-Phase Challenge": {"phase_1": 8.0, "phase_2": 5.0},
}

use_defaults = st.checkbox("Use default phase targets for selected challenge", value=True)
default_targets = phase_presets[challenge_type]



 main
 main
col1, col2 = st.columns(2)
with col1:
    starting_balance = st.number_input("Starting Balance ($)", min_value=1000, value=100000, step=1000)
    daily_drawdown_pct = st.number_input("Daily Drawdown Limit (%)", min_value=0.1, max_value=20.0, value=5.0, step=0.1)
    overall_drawdown_pct = st.number_input("Overall Drawdown Limit (%)", min_value=0.1, max_value=30.0, value=10.0, step=0.1)
 codex/fix-risk-of-ruin-page-issue-4hzh5f

 codex/fix-risk-of-ruin-page-issue-iyl7gn

    target_profit_pct = st.number_input("Target Profit (%)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)
 main
 main

with col2:
    win_rate_pct = st.number_input("Win Rate (%)", min_value=1.0, max_value=99.0, value=50.0, step=1.0)
    reward_risk = st.number_input("Average Reward:Risk (R)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
    risk_per_trade_pct = st.number_input("Risk Per Trade (% of balance)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    trades_per_day = st.number_input("Trades Per Day", min_value=1, max_value=20, value=3, step=1)

 codex/fix-risk-of-ruin-page-issue-4hzh5f
phase_col1, phase_col2 = st.columns(2)
with phase_col1:
    target_phase_1_pct = st.number_input(
        "Phase 1 Target Profit (%)",
        min_value=0.1,
        max_value=100.0,
        value=default_targets["phase_1"] if use_defaults else 8.0,
        step=0.1,
    )
with phase_col2:
    if challenge_type == "2-Phase Challenge":
        target_phase_2_pct = st.number_input(
            "Phase 2 Target Profit (%)",
            min_value=0.1,
            max_value=100.0,
            value=default_targets["phase_2"] if use_defaults else 5.0,
            step=0.1,
        )
    else:
        target_phase_2_pct = 0.0
        st.caption("Phase 2 not used in 1-Phase mode.")


codex/fix-risk-of-ruin-page-issue-iyl7gn
if challenge_type == "1-Phase Challenge":
    target_phase_1_pct = st.number_input("Phase 1 Target Profit (%)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)
    target_phase_2_pct = 0.0
else:
    phase_col1, phase_col2 = st.columns(2)
    with phase_col1:
        target_phase_1_pct = st.number_input("Phase 1 Target Profit (%)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)
    with phase_col2:
        target_phase_2_pct = st.number_input("Phase 2 Target Profit (%)", min_value=0.1, max_value=100.0, value=5.0, step=0.1)


 main
 main
sim_col1, sim_col2 = st.columns(2)
with sim_col1:
    simulation_runs = st.slider("Simulation Runs", min_value=100, max_value=10000, value=2000, step=100)
with sim_col2:
 codex/fix-risk-of-ruin-page-issue-4hzh5f
    max_days_per_phase = st.slider("Max Trading Days (per phase)", min_value=5, max_value=180, value=30)


def simulate_phase(target_profit_pct):
    balance = float(starting_balance)
    initial_balance = float(starting_balance)
    target_balance = initial_balance * (1 + target_profit_pct / 100)

codex/fix-risk-of-ruin-page-issue-iyl7gn
    max_days_per_phase = st.slider("Max Trading Days (per phase)", min_value=5, max_value=180, value=30)


def simulate_phase(target_profit_pct: float) -> tuple[bool, bool, float]:

    max_days = st.slider("Max Trading Days", min_value=5, max_value=180, value=30)


def simulate_path() -> tuple[bool, bool, int, float]:
main
    balance = float(starting_balance)
    initial_balance = float(starting_balance)
    target_balance = initial_balance * (1 + target_profit_pct / 100)

 main
    overall_floor = initial_balance * (1 - overall_drawdown_pct / 100)
    win_prob = win_rate_pct / 100
    risk_fraction = risk_per_trade_pct / 100

 codex/fix-risk-of-ruin-page-issue-4hzh5f
    for _ in range(max_days_per_phase):

 codex/fix-risk-of-ruin-page-issue-iyl7gn
    for _day in range(1, max_days_per_phase + 1):

    for day in range(1, max_days + 1):
 main
 main
        day_start_balance = balance
        daily_floor = day_start_balance * (1 - daily_drawdown_pct / 100)

        for _ in range(int(trades_per_day)):
            risk_amount = balance * risk_fraction
 codex/fix-risk-of-ruin-page-issue-4hzh5f
            pnl = risk_amount * reward_risk if random.random() <= win_prob else -risk_amount

 codex/fix-risk-of-ruin-page-issue-iyl7gn
            pnl = (risk_amount * reward_risk) if random.random() <= win_prob else -risk_amount
 main
            balance += pnl

            if balance <= overall_floor or balance <= daily_floor:
                return True, False, balance

            if balance >= target_balance:
                return False, True, balance

    return False, False, balance


 codex/fix-risk-of-ruin-page-issue-4hzh5f
def simulate_challenge():
    ruined, passed_phase_1, end_balance = simulate_phase(target_phase_1_pct)
    if ruined:
        return True, False, False, end_balance
    if not passed_phase_1:
        return False, False, False, end_balance
    if challenge_type == "1-Phase Challenge":
        return False, True, False, end_balance

    ruined, passed_phase_2, end_balance = simulate_phase(target_phase_2_pct)
    if ruined:
        return True, False, True, end_balance
    if passed_phase_2:
        return False, True, True, end_balance
    return False, False, True, end_balance


if st.button("Run Simulation", type="primary"):
    ruined_count = 0
    passed_count = 0
    reached_phase_2_count = 0
    ending_balances = []

    for _ in range(simulation_runs):
        ruined, passed, reached_phase_2, final_balance = simulate_challenge()
        ruined_count += int(ruined)
        passed_count += int(passed)
        reached_phase_2_count += int(reached_phase_2)
        ending_balances.append(final_balance)

    risk_of_ruin = ruined_count / simulation_runs
    pass_probability = passed_count / simulation_runs
    survival_rate = 1 - risk_of_ruin
    avg_ending_balance = sum(ending_balances) / len(ending_balances)

    st.subheader("Results")
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Risk of Ruin", f"{risk_of_ruin:.2%}")
    metric_col2.metric("Chance to Pass Challenge", f"{pass_probability:.2%}")
    metric_col3.metric("Survival Rate", f"{survival_rate:.2%}")

    if challenge_type == "2-Phase Challenge":
        reached_phase_2_probability = reached_phase_2_count / simulation_runs
        st.metric("Reached Phase 2", f"{reached_phase_2_probability:.2%}")

    st.metric("Average Ending Balance", f"${avg_ending_balance:,.2f}")
    st.info("Tip: Lower risk per trade and/or reduce trades per day to lower your risk of ruin.")

def simulate_challenge() -> tuple[bool, bool, bool, float]:
    phase_1_ruined, phase_1_passed, phase_1_end_balance = simulate_phase(target_phase_1_pct)

    if phase_1_ruined:
        return True, False, False, phase_1_end_balance

    if not phase_1_passed:
        return False, False, False, phase_1_end_balance

    if challenge_type == "1-Phase Challenge":
        return False, True, False, phase_1_end_balance

    phase_2_ruined, phase_2_passed, phase_2_end_balance = simulate_phase(target_phase_2_pct)

    if phase_2_ruined:
        return True, False, True, phase_2_end_balance

    if phase_2_passed:
        return False, True, True, phase_2_end_balance

    return False, False, True, phase_2_end_balance

            if random.random() <= win_prob:
                pnl = risk_amount * reward_risk
            else:
                pnl = -risk_amount

            balance += pnl

            if balance <= overall_floor or balance <= daily_floor:
                return True, False, day, balance

            if balance >= target_balance:
                return False, True, day, balance

    return False, False, max_days, balance
main


if st.button("Run Simulation", type="primary"):
    ruined = 0
codex/fix-risk-of-ruin-page-issue-iyl7gn
    passed_challenge = 0
    reached_phase_2 = 0
    ending_balances = []

    for _ in range(simulation_runs):
        is_ruined, is_passed, got_to_phase_2, final_balance = simulate_challenge()
        ruined += int(is_ruined)
        passed_challenge += int(is_passed)
        reached_phase_2 += int(got_to_phase_2)
        ending_balances.append(final_balance)

    ruin_probability = ruined / simulation_runs
    pass_probability = passed_challenge / simulation_runs

    hit_target = 0
    ending_balances = []

    for _ in range(simulation_runs):
        is_ruined, reached_target, _, final_balance = simulate_path()
        ruined += int(is_ruined)
        hit_target += int(reached_target)
        ending_balances.append(final_balance)

    ruin_probability = ruined / simulation_runs
    target_probability = hit_target / simulation_runs
main
    survival_probability = 1 - ruin_probability
    avg_ending_balance = sum(ending_balances) / len(ending_balances)

    st.subheader("Results")
    m1, m2, m3 = st.columns(3)
    m1.metric("Risk of Ruin", f"{ruin_probability:.2%}")
codex/fix-risk-of-ruin-page-issue-iyl7gn
    m2.metric("Chance to Pass Challenge", f"{pass_probability:.2%}")
    m3.metric("Survival Rate", f"{survival_probability:.2%}")

    if challenge_type == "2-Phase Challenge":
        phase_2_probability = reached_phase_2 / simulation_runs
        st.metric("Reached Phase 2", f"{phase_2_probability:.2%}")

    st.metric("Average Ending Balance", f"${avg_ending_balance:,.2f}")

    st.info("Tip: Lower risk per trade and/or reduce trades per day to lower your risk of ruin.")

    m2.metric("Chance to Hit Target", f"{target_probability:.2%}")
    m3.metric("Survival Rate", f"{survival_probability:.2%}")

    st.metric("Average Ending Balance", f"${avg_ending_balance:,.2f}")

    st.info(
        "Tip: Lower risk per trade and/or reduce trades per day to dramatically lower your risk of ruin."
    )
main
 main
