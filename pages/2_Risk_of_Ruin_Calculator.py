import random
import statistics

import streamlit as st

 codex/create-risk-of-ruin-calculator-for-prop-firms-az1vep
st.set_page_config(page_title="Risk of Ruin (Prop Firm)", layout="centered")

st.markdown(
    """
<style>
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.main-title { font-size: 2rem; font-weight: 800; margin-bottom: 0.25rem; }
.subtitle { color: #9ca3af; margin-bottom: 1rem; }
.panel {
    background: linear-gradient(140deg, #3f1212 0%, #6a1f1f 100%);
    padding: 1.05rem 1.2rem;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 24px rgba(0,0,0,0.16);
}
.metric-label { color: #f3d9d9; font-size: 0.9rem; }
.metric-value { color: #ffffff; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.45rem; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">⚠️ Risk of Ruin + Challenge Probability</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Prop Firm Model</div>', unsafe_allow_html=True)
st.markdown("Estimate breach risk and your probability of passing a **1-step** or **2-step** prop challenge.")


def sample_trade_return_pct(
    rng: random.Random,
    outcome_mode: str,
    win_rate_pct: float,
    reward_to_risk: float,
    risk_per_trade_pct: float,
    loss_rate_pct: float,
    breakeven_rate_pct: float,
    be_partial_rate_pct: float,
    avg_win_pct: float,
    avg_loss_pct: float,
    avg_be_partial_pct: float,
):
    if outcome_mode == "Simple (Win/Loss)":
        is_win = rng.random() < (win_rate_pct / 100)
        return (risk_per_trade_pct * reward_to_risk) if is_win else -risk_per_trade_pct

    roll = rng.random() * 100
    if roll < win_rate_pct:
        return avg_win_pct
    if roll < win_rate_pct + loss_rate_pct:
        return -avg_loss_pct
    if roll < win_rate_pct + loss_rate_pct + breakeven_rate_pct:
        return 0.0
    return avg_be_partial_pct


def simulate_phase(
    starting_balance: float,
    profit_target_pct: float,
    max_drawdown_pct: float,
    daily_loss_limit_pct: float,
    trades_per_day: int,
    max_trades: int,
    rng: random.Random,
    outcome_mode: str,
    win_rate_pct: float,
    reward_to_risk: float,
    risk_per_trade_pct: float,
    loss_rate_pct: float,
    breakeven_rate_pct: float,
    be_partial_rate_pct: float,
    avg_win_pct: float,
    avg_loss_pct: float,
    avg_be_partial_pct: float,
):
    min_balance_allowed = starting_balance * (1 - max_drawdown_pct / 100)
    daily_loss_amount = starting_balance * (daily_loss_limit_pct / 100)
    target_balance = starting_balance * (1 + profit_target_pct / 100)

    balance = starting_balance
    daily_pnl = 0.0

    for trade_num in range(1, max_trades + 1):
        if (trade_num - 1) % trades_per_day == 0:
            daily_pnl = 0.0

        trade_return_pct = sample_trade_return_pct(
            rng=rng,
            outcome_mode=outcome_mode,
            win_rate_pct=win_rate_pct,
            reward_to_risk=reward_to_risk,
            risk_per_trade_pct=risk_per_trade_pct,
            loss_rate_pct=loss_rate_pct,
            breakeven_rate_pct=breakeven_rate_pct,
            be_partial_rate_pct=be_partial_rate_pct,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            avg_be_partial_pct=avg_be_partial_pct,
        )
        trade_result = balance * (trade_return_pct / 100)

        balance += trade_result
        daily_pnl += trade_result

        if balance >= target_balance:
            return "pass", trade_num
        if balance <= min_balance_allowed or daily_pnl <= -daily_loss_amount:
            return "fail", trade_num

    return "incomplete", max_trades


def simulate_challenge(
    challenge_type: str,
    phase1_target_pct: float,
    phase2_target_pct: float,
    starting_balance: float,
    max_drawdown_pct: float,
    daily_loss_limit_pct: float,
    trades_per_day: int,
    max_trades: int,
    simulations: int,
    outcome_mode: str,
    win_rate_pct: float,
    reward_to_risk: float,
    risk_per_trade_pct: float,
    loss_rate_pct: float,
    breakeven_rate_pct: float,
    be_partial_rate_pct: float,
    avg_win_pct: float,
    avg_loss_pct: float,
    avg_be_partial_pct: float,
    seed: int = 42,
):
    rng = random.Random(seed)

    phase1_counts = {"pass": 0, "fail": 0, "incomplete": 0}
    phase2_counts = {"pass": 0, "fail": 0, "incomplete": 0}
    overall_counts = {"pass": 0, "fail": 0, "incomplete": 0}
    fail_trade_counts = []

    for _ in range(simulations):
        p1_outcome, p1_trades = simulate_phase(
            starting_balance=starting_balance,
            profit_target_pct=phase1_target_pct,
            max_drawdown_pct=max_drawdown_pct,
            daily_loss_limit_pct=daily_loss_limit_pct,
            trades_per_day=trades_per_day,
            max_trades=max_trades,
            rng=rng,
            outcome_mode=outcome_mode,
            win_rate_pct=win_rate_pct,
            reward_to_risk=reward_to_risk,
            risk_per_trade_pct=risk_per_trade_pct,
            loss_rate_pct=loss_rate_pct,
            breakeven_rate_pct=breakeven_rate_pct,
            be_partial_rate_pct=be_partial_rate_pct,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            avg_be_partial_pct=avg_be_partial_pct,
        )
        phase1_counts[p1_outcome] += 1

        if p1_outcome == "fail":
            overall_counts["fail"] += 1
            fail_trade_counts.append(p1_trades)
            continue
        if p1_outcome == "incomplete":
            overall_counts["incomplete"] += 1
            continue
        if challenge_type == "1-Step":
            overall_counts["pass"] += 1
            continue

        p2_outcome, p2_trades = simulate_phase(
            starting_balance=starting_balance,
            profit_target_pct=phase2_target_pct,
            max_drawdown_pct=max_drawdown_pct,
            daily_loss_limit_pct=daily_loss_limit_pct,
            trades_per_day=trades_per_day,
            max_trades=max_trades,
            rng=rng,
            outcome_mode=outcome_mode,
            win_rate_pct=win_rate_pct,
            reward_to_risk=reward_to_risk,
            risk_per_trade_pct=risk_per_trade_pct,
            loss_rate_pct=loss_rate_pct,
            breakeven_rate_pct=breakeven_rate_pct,
            be_partial_rate_pct=be_partial_rate_pct,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            avg_be_partial_pct=avg_be_partial_pct,
        )
        phase2_counts[p2_outcome] += 1

        if p2_outcome == "pass":
            overall_counts["pass"] += 1
        elif p2_outcome == "fail":
            overall_counts["fail"] += 1
            fail_trade_counts.append(p1_trades + p2_trades)
        else:
            overall_counts["incomplete"] += 1

    return {
        "phase1": phase1_counts,
        "phase2": phase2_counts,
        "overall": overall_counts,
        "simulations": simulations,
        "median_trades_to_fail": statistics.median(fail_trade_counts) if fail_trade_counts else None,


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
 main
    }


col1, col2 = st.columns(2)
with col1:
codex/create-risk-of-ruin-calculator-for-prop-firms-az1vep
    starting_balance = st.number_input("💼 Starting Balance (USD)", min_value=1000, value=100000, step=1000)
    challenge_type = st.selectbox("🏁 Challenge Type", ["1-Step", "2-Step"], index=1)
    phase1_target_pct = st.number_input("🎯 Phase 1 Profit Target (%)", min_value=1.0, max_value=50.0, value=8.0, step=0.5)
    phase2_target_pct = st.number_input(
        "🎯 Phase 2 Profit Target (%)",
        min_value=1.0,
        max_value=50.0,
        value=5.0,
        step=0.5,
        disabled=challenge_type == "1-Step",
    )

with col2:
    max_drawdown_pct = st.number_input("📉 Max Overall Drawdown (%)", min_value=1.0, max_value=50.0, value=10.0, step=0.5)
    daily_loss_limit_pct = st.number_input("🛑 Daily Loss Limit (%)", min_value=0.5, max_value=20.0, value=5.0, step=0.5)
    trades_per_day = st.number_input("📅 Trades per Day", min_value=1, max_value=50, value=3, step=1)
    max_trades = st.number_input("🔢 Max Trades per Phase", min_value=10, max_value=5000, value=300, step=10)

outcome_mode = st.selectbox("📐 Outcome Modeling", ["Simple (Win/Loss)", "Advanced (Win/Loss/BE/BE+Partial)"])

if outcome_mode == "Simple (Win/Loss)":
    c1, c2 = st.columns(2)
    with c1:
        risk_per_trade_pct = st.number_input("🎯 Risk per Trade (%)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
        win_rate_pct = st.slider("✅ Win Rate (%)", min_value=1, max_value=99, value=45)
    with c2:
        reward_to_risk = st.number_input("⚖️ Reward:Risk Ratio", min_value=0.1, max_value=10.0, value=1.5, step=0.1)

    loss_rate_pct = 100 - win_rate_pct
    breakeven_rate_pct = 0.0
    be_partial_rate_pct = 0.0
    avg_win_pct = risk_per_trade_pct * reward_to_risk
    avg_loss_pct = risk_per_trade_pct
    avg_be_partial_pct = 0.0
else:
    st.info("Advanced mode lets you model your full distribution, including breakeven and BE+partial outcomes.")
    a1, a2 = st.columns(2)
    with a1:
        win_rate_pct = st.number_input("✅ Win Rate (%)", min_value=0.0, max_value=100.0, value=44.0, step=0.5)
        loss_rate_pct = st.number_input("❌ Loss Rate (%)", min_value=0.0, max_value=100.0, value=35.0, step=0.5)
        breakeven_rate_pct = st.number_input("➖ Breakeven Rate (%)", min_value=0.0, max_value=100.0, value=13.0, step=0.5)
        be_partial_rate_pct = st.number_input("🟨 BE + Partial Rate (%)", min_value=0.0, max_value=100.0, value=8.0, step=0.5)
    with a2:
        avg_win_pct = st.number_input("📈 Avg Win (%)", min_value=0.0, max_value=50.0, value=2.57, step=0.01)
        avg_loss_pct = st.number_input("📉 Avg Loss (%)", min_value=0.0, max_value=50.0, value=1.00, step=0.01)
        avg_be_partial_pct = st.number_input("🧩 Avg BE + Partial (%)", min_value=0.0, max_value=50.0, value=0.90, step=0.01)

    total_rate = win_rate_pct + loss_rate_pct + breakeven_rate_pct + be_partial_rate_pct
    if abs(total_rate - 100) > 0.01:
        st.warning(f"Outcome rates currently sum to {total_rate:.2f}%. Please adjust to 100%.")

    risk_per_trade_pct = avg_loss_pct
    reward_to_risk = (avg_win_pct / avg_loss_pct) if avg_loss_pct > 0 else 0.0

simulations = st.slider("🧪 Monte Carlo Simulations", min_value=500, max_value=20000, value=5000, step=500)

if st.button("Run Challenge Probability Simulation"):
    if outcome_mode == "Advanced (Win/Loss/BE/BE+Partial)":
        total_rate = win_rate_pct + loss_rate_pct + breakeven_rate_pct + be_partial_rate_pct
        if abs(total_rate - 100) > 0.01:
            st.error("Please make sure Win + Loss + BE + BE+Partial = 100% before running.")
            st.stop()

    results = simulate_challenge(
        challenge_type=challenge_type,
        phase1_target_pct=float(phase1_target_pct),
        phase2_target_pct=float(phase2_target_pct),
        starting_balance=float(starting_balance),
        max_drawdown_pct=float(max_drawdown_pct),
        daily_loss_limit_pct=float(daily_loss_limit_pct),
        trades_per_day=int(trades_per_day),
        max_trades=int(max_trades),
        simulations=int(simulations),
        outcome_mode=outcome_mode,
        win_rate_pct=float(win_rate_pct),
        reward_to_risk=float(reward_to_risk),
        risk_per_trade_pct=float(risk_per_trade_pct),
        loss_rate_pct=float(loss_rate_pct),
        breakeven_rate_pct=float(breakeven_rate_pct),
        be_partial_rate_pct=float(be_partial_rate_pct),
        avg_win_pct=float(avg_win_pct),
        avg_loss_pct=float(avg_loss_pct),
        avg_be_partial_pct=float(avg_be_partial_pct),
    )

    phase1_pass_pct = results["phase1"]["pass"] / results["simulations"] * 100
    phase1_fail_pct = results["phase1"]["fail"] / results["simulations"] * 100
    overall_pass_pct = results["overall"]["pass"] / results["simulations"] * 100
    overall_fail_pct = results["overall"]["fail"] / results["simulations"] * 100

    st.markdown(
        f"""
<div class="panel">
    <div class="metric-label">Phase 1 Pass Probability</div>
    <div class="metric-value">{phase1_pass_pct:.2f}%</div>
    <div class="metric-label">Phase 1 Fail Probability</div>
    <div class="metric-value">{phase1_fail_pct:.2f}%</div>
""",
        unsafe_allow_html=True,
    )

    if challenge_type == "2-Step":
        phase2_reached = results["phase1"]["pass"]
        phase2_pass_pct_unconditional = results["phase2"]["pass"] / results["simulations"] * 100
        phase2_pass_pct_conditional = (results["phase2"]["pass"] / phase2_reached) * 100 if phase2_reached else 0.0

        st.markdown(
            f"""
<div class="panel" style="margin-top:12px;">
    <div class="metric-label">Phase 2 Reached (after passing P1)</div>
    <div class="metric-value">{phase2_reached:,} / {results['simulations']:,}</div>
    <div class="metric-label">Phase 2 Pass Probability (overall)</div>
    <div class="metric-value">{phase2_pass_pct_unconditional:.2f}%</div>
    <div class="metric-label">Phase 2 Pass Probability (given P1 pass)</div>
    <div class="metric-value">{phase2_pass_pct_conditional:.2f}%</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
<div class="panel" style="margin-top:12px;">
    <div class="metric-label">Challenge Pass Probability (overall)</div>
    <div class="metric-value">{overall_pass_pct:.2f}%</div>
    <div class="metric-label">Challenge Fail Probability (overall)</div>
    <div class="metric-value">{overall_fail_pct:.2f}%</div>
    <div class="metric-label">Median Trades to Failure (failed paths only)</div>
    <div class="metric-value">{results['median_trades_to_fail'] if results['median_trades_to_fail'] is not None else 'Not reached'}</div>

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
 main
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("---")
codex/create-risk-of-ruin-calculator-for-prop-firms-az1vep
st.caption("Advanced mode supports full trade-outcome modeling including take-profits, breakeven, and partial exits.")
st.caption("This is a probabilistic estimate, not financial advice. Actual results vary with execution and rule interpretation.")

st.caption(
    "This is a probabilistic estimate, not financial advice. Actual results vary with execution, slippage, and rule interpretations."
)
 main
