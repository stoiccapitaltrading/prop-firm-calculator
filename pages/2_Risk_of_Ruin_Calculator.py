import random
import streamlit as st

st.set_page_config(page_title="Risk of Ruin Calculator", layout="centered")

st.title("⚠️ Risk of Ruin Calculator")
st.caption("Estimate your chance of violating prop-firm drawdown rules.")

st.markdown(
    """
This simulator uses your win rate, risk size, and reward/risk profile to run many account paths.
A run is marked **ruined** if it breaches either:
- **Daily drawdown limit** (loss from start-of-day balance), or
- **Overall drawdown limit** (loss from initial balance).
"""
)

challenge_type = st.radio(
    "Challenge Type",
    options=["1-Phase Challenge", "2-Phase Challenge"],
    horizontal=True,
)

col1, col2 = st.columns(2)
with col1:
    starting_balance = st.number_input("Starting Balance ($)", min_value=1000, value=100000, step=1000)
    daily_drawdown_pct = st.number_input("Daily Drawdown Limit (%)", min_value=0.1, max_value=20.0, value=5.0, step=0.1)
    overall_drawdown_pct = st.number_input("Overall Drawdown Limit (%)", min_value=0.1, max_value=30.0, value=10.0, step=0.1)

with col2:
    win_rate_pct = st.number_input("Win Rate (%)", min_value=1.0, max_value=99.0, value=50.0, step=1.0)
    reward_risk = st.number_input("Average Reward:Risk (R)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
    risk_per_trade_pct = st.number_input("Risk Per Trade (% of balance)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    trades_per_day = st.number_input("Trades Per Day", min_value=1, max_value=20, value=3, step=1)

if challenge_type == "1-Phase Challenge":
    target_phase_1_pct = st.number_input("Phase 1 Target Profit (%)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)
    target_phase_2_pct = 0.0
else:
    phase_col1, phase_col2 = st.columns(2)
    with phase_col1:
        target_phase_1_pct = st.number_input("Phase 1 Target Profit (%)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)
    with phase_col2:
        target_phase_2_pct = st.number_input("Phase 2 Target Profit (%)", min_value=0.1, max_value=100.0, value=5.0, step=0.1)

sim_col1, sim_col2 = st.columns(2)
with sim_col1:
    simulation_runs = st.slider("Simulation Runs", min_value=100, max_value=10000, value=2000, step=100)
with sim_col2:
    max_days_per_phase = st.slider("Max Trading Days (per phase)", min_value=5, max_value=180, value=30)


def simulate_phase(target_profit_pct: float) -> tuple[bool, bool, float]:
    balance = float(starting_balance)
    initial_balance = float(starting_balance)
    target_balance = initial_balance * (1 + target_profit_pct / 100)

    overall_floor = initial_balance * (1 - overall_drawdown_pct / 100)
    win_prob = win_rate_pct / 100
    risk_fraction = risk_per_trade_pct / 100

    for _day in range(1, max_days_per_phase + 1):
        day_start_balance = balance
        daily_floor = day_start_balance * (1 - daily_drawdown_pct / 100)

        for _ in range(int(trades_per_day)):
            risk_amount = balance * risk_fraction
            pnl = (risk_amount * reward_risk) if random.random() <= win_prob else -risk_amount
            balance += pnl

            if balance <= overall_floor or balance <= daily_floor:
                return True, False, balance

            if balance >= target_balance:
                return False, True, balance

    return False, False, balance


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


if st.button("Run Simulation", type="primary"):
    ruined = 0
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
    survival_probability = 1 - ruin_probability
    avg_ending_balance = sum(ending_balances) / len(ending_balances)

    st.subheader("Results")
    m1, m2, m3 = st.columns(3)
    m1.metric("Risk of Ruin", f"{ruin_probability:.2%}")
    m2.metric("Chance to Pass Challenge", f"{pass_probability:.2%}")
    m3.metric("Survival Rate", f"{survival_probability:.2%}")

    if challenge_type == "2-Phase Challenge":
        phase_2_probability = reached_phase_2 / simulation_runs
        st.metric("Reached Phase 2", f"{phase_2_probability:.2%}")

    st.metric("Average Ending Balance", f"${avg_ending_balance:,.2f}")

    st.info("Tip: Lower risk per trade and/or reduce trades per day to lower your risk of ruin.")
