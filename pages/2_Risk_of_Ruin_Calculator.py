import random
import statistics

import streamlit as st


st.set_page_config(page_title="Risk of Ruin (Prop Firm)", layout="centered")
st.title("⚠️ Risk of Ruin Calculator")
st.subheader("Prop Firm Model")
st.markdown(
    "Estimate the chance of breaching **daily** or **overall drawdown** rules "
    "using a Monte Carlo simulation."
)


def simulate_prop_risk_of_ruin(
    starting_balance: float,
    max_drawdown_pct: float,
    daily_loss_limit_pct: float,
    risk_per_trade_pct: float,
    win_rate_pct: float,
    reward_to_risk: float,
    trades_per_day: int,
    max_trades: int,
    simulations: int,
    seed: int = 42,
):
    """Run Monte Carlo paths and return ruin metrics.

    Ruin happens when either:
    - Balance falls below the max drawdown threshold, or
    - Daily PnL breaches the daily loss limit.
    """

    rng = random.Random(seed)
    min_balance_allowed = starting_balance * (1 - max_drawdown_pct / 100)
    daily_loss_amount = starting_balance * (daily_loss_limit_pct / 100)

    ruin_count = 0
    ruin_trade_counts = []

    for _ in range(simulations):
        balance = starting_balance
        daily_pnl = 0.0
        ruined = False

        for trade_num in range(1, max_trades + 1):
            if (trade_num - 1) % trades_per_day == 0:
                daily_pnl = 0.0

            risk_amount = balance * (risk_per_trade_pct / 100)
            is_win = rng.random() < (win_rate_pct / 100)
            trade_result = risk_amount * reward_to_risk if is_win else -risk_amount

            balance += trade_result
            daily_pnl += trade_result

            if balance <= min_balance_allowed or daily_pnl <= -daily_loss_amount:
                ruin_count += 1
                ruin_trade_counts.append(trade_num)
                ruined = True
                break

        if not ruined:
            ruin_trade_counts.append(None)

    risk_of_ruin_pct = (ruin_count / simulations) * 100
    ruined_only = [count for count in ruin_trade_counts if count is not None]

    median_trades_to_ruin = statistics.median(ruined_only) if ruined_only else None

    return {
        "risk_of_ruin_pct": risk_of_ruin_pct,
        "ruin_count": ruin_count,
        "simulations": simulations,
        "median_trades_to_ruin": median_trades_to_ruin,
        "min_balance_allowed": min_balance_allowed,
        "daily_loss_amount": daily_loss_amount,
    }


col1, col2 = st.columns(2)
with col1:
    starting_balance = st.number_input(
        "💼 Starting Balance (USD)", min_value=1000, value=100000, step=1000
    )
    max_drawdown_pct = st.number_input(
        "📉 Max Overall Drawdown (%)", min_value=1.0, max_value=50.0, value=10.0, step=0.5
    )
    daily_loss_limit_pct = st.number_input(
        "🛑 Daily Loss Limit (%)", min_value=0.5, max_value=20.0, value=5.0, step=0.5
    )
    trades_per_day = st.number_input(
        "📅 Trades per Day", min_value=1, max_value=50, value=3, step=1
    )

with col2:
    risk_per_trade_pct = st.number_input(
        "🎯 Risk per Trade (%)", min_value=0.1, max_value=10.0, value=1.0, step=0.1
    )
    win_rate_pct = st.slider("✅ Win Rate (%)", min_value=1, max_value=99, value=45)
    reward_to_risk = st.number_input(
        "⚖️ Reward:Risk Ratio", min_value=0.1, max_value=10.0, value=1.5, step=0.1
    )
    max_trades = st.number_input(
        "🔢 Trades to Simulate per Path", min_value=10, max_value=5000, value=300, step=10
    )

simulations = st.slider("🧪 Monte Carlo Simulations", min_value=500, max_value=20000, value=5000, step=500)

if st.button("Run Risk of Ruin Simulation"):
    results = simulate_prop_risk_of_ruin(
        starting_balance=float(starting_balance),
        max_drawdown_pct=float(max_drawdown_pct),
        daily_loss_limit_pct=float(daily_loss_limit_pct),
        risk_per_trade_pct=float(risk_per_trade_pct),
        win_rate_pct=float(win_rate_pct),
        reward_to_risk=float(reward_to_risk),
        trades_per_day=int(trades_per_day),
        max_trades=int(max_trades),
        simulations=int(simulations),
    )

    st.markdown(
        f"""
<div style="background-color:#3a0f0f;padding:20px;border-radius:15px;margin-top:20px">
    <h3>📌 Risk Results</h3>
    <p>Estimated Risk of Ruin: <strong>{results['risk_of_ruin_pct']:.2f}%</strong></p>
    <p>Ruin Paths: <strong>{results['ruin_count']:,}</strong> / {results['simulations']:,}</p>
    <p>Max Allowed Balance (Overall DD): <strong>${results['min_balance_allowed']:,.2f}</strong></p>
    <p>Daily Loss Amount: <strong>${results['daily_loss_amount']:,.2f}</strong></p>
    <p>Median Trades to Ruin (ruined paths only):
       <strong>{results['median_trades_to_ruin'] if results['median_trades_to_ruin'] is not None else 'Not reached'}</strong></p>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption(
    "This is a probabilistic estimate, not financial advice. Actual results vary with execution, slippage, and rule interpretations."
)
