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

col1, col2 = st.columns(2)
with col1:
    starting_balance = st.number_input("Starting Balance ($)", min_value=1000, value=100000, step=1000)
    daily_drawdown_pct = st.number_input("Daily Drawdown Limit (%)", min_value=0.1, max_value=20.0, value=5.0, step=0.1)
    overall_drawdown_pct = st.number_input("Overall Drawdown Limit (%)", min_value=0.1, max_value=30.0, value=10.0, step=0.1)
    target_profit_pct = st.number_input("Target Profit (%)", min_value=0.1, max_value=100.0, value=8.0, step=0.1)

with col2:
    win_rate_pct = st.number_input("Win Rate (%)", min_value=1.0, max_value=99.0, value=50.0, step=1.0)
    reward_risk = st.number_input("Average Reward:Risk (R)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
    risk_per_trade_pct = st.number_input("Risk Per Trade (% of balance)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    trades_per_day = st.number_input("Trades Per Day", min_value=1, max_value=20, value=3, step=1)

sim_col1, sim_col2 = st.columns(2)
with sim_col1:
    simulation_runs = st.slider("Simulation Runs", min_value=100, max_value=10000, value=2000, step=100)
with sim_col2:
    max_days = st.slider("Max Trading Days", min_value=5, max_value=180, value=30)


def simulate_path() -> tuple[bool, bool, int, float]:
    balance = float(starting_balance)
    initial_balance = float(starting_balance)
    target_balance = initial_balance * (1 + target_profit_pct / 100)

    overall_floor = initial_balance * (1 - overall_drawdown_pct / 100)
    win_prob = win_rate_pct / 100
    risk_fraction = risk_per_trade_pct / 100

    for day in range(1, max_days + 1):
        day_start_balance = balance
        daily_floor = day_start_balance * (1 - daily_drawdown_pct / 100)

        for _ in range(int(trades_per_day)):
            risk_amount = balance * risk_fraction
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


if st.button("Run Simulation", type="primary"):
    ruined = 0
    hit_target = 0
    ending_balances = []

    for _ in range(simulation_runs):
        is_ruined, reached_target, _, final_balance = simulate_path()
        ruined += int(is_ruined)
        hit_target += int(reached_target)
        ending_balances.append(final_balance)

    ruin_probability = ruined / simulation_runs
    target_probability = hit_target / simulation_runs
    survival_probability = 1 - ruin_probability
    avg_ending_balance = sum(ending_balances) / len(ending_balances)

    st.subheader("Results")
    m1, m2, m3 = st.columns(3)
    m1.metric("Risk of Ruin", f"{ruin_probability:.2%}")
    m2.metric("Chance to Hit Target", f"{target_probability:.2%}")
    m3.metric("Survival Rate", f"{survival_probability:.2%}")

    st.metric("Average Ending Balance", f"${avg_ending_balance:,.2f}")

    st.info(
        "Tip: Lower risk per trade and/or reduce trades per day to dramatically lower your risk of ruin."
    )
