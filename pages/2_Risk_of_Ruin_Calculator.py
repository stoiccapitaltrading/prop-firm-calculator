 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/pages/2_Risk_of_Ruin_Calculator.py b/pages/2_Risk_of_Ruin_Calculator.py
new file mode 100644
index 0000000000000000000000000000000000000000..4f8b2ec79ac56d8246fb34e4b91903eac3b72d6f
--- /dev/null
+++ b/pages/2_Risk_of_Ruin_Calculator.py
@@ -0,0 +1,277 @@
+import random
+import statistics
+
+import streamlit as st
+
+st.set_page_config(page_title="Risk of Ruin (Prop Firm)", layout="centered")
+
+st.markdown(
+    """
+<style>
+.block-container {
+    padding-top: 2rem;
+    padding-bottom: 2rem;
+}
+.main-title {
+    font-size: 2rem;
+    font-weight: 800;
+    margin-bottom: 0.25rem;
+}
+.subtitle {
+    color: #9ca3af;
+    margin-bottom: 1rem;
+}
+.panel {
+    background: linear-gradient(140deg, #3f1212 0%, #6a1f1f 100%);
+    padding: 1.05rem 1.2rem;
+    border-radius: 14px;
+    border: 1px solid rgba(255,255,255,0.08);
+    box-shadow: 0 8px 24px rgba(0,0,0,0.16);
+}
+.metric-label {
+    color: #f3d9d9;
+    font-size: 0.9rem;
+}
+.metric-value {
+    color: #ffffff;
+    font-size: 1.1rem;
+    font-weight: 700;
+    margin-bottom: 0.45rem;
+}
+</style>
+""",
+    unsafe_allow_html=True,
+)
+
+st.markdown('<div class="main-title">⚠️ Risk of Ruin + Challenge Probability</div>', unsafe_allow_html=True)
+st.markdown('<div class="subtitle">Prop Firm Model</div>', unsafe_allow_html=True)
+st.markdown(
+    "Estimate breach risk and your probability of passing a **1-step** or **2-step** prop challenge."
+)
+
+
+def simulate_phase(
+    starting_balance: float,
+    profit_target_pct: float,
+    max_drawdown_pct: float,
+    daily_loss_limit_pct: float,
+    risk_per_trade_pct: float,
+    win_rate_pct: float,
+    reward_to_risk: float,
+    trades_per_day: int,
+    max_trades: int,
+    rng: random.Random,
+):
+    min_balance_allowed = starting_balance * (1 - max_drawdown_pct / 100)
+    daily_loss_amount = starting_balance * (daily_loss_limit_pct / 100)
+    target_balance = starting_balance * (1 + profit_target_pct / 100)
+
+    balance = starting_balance
+    daily_pnl = 0.0
+
+    for trade_num in range(1, max_trades + 1):
+        if (trade_num - 1) % trades_per_day == 0:
+            daily_pnl = 0.0
+
+        risk_amount = balance * (risk_per_trade_pct / 100)
+        is_win = rng.random() < (win_rate_pct / 100)
+        trade_result = risk_amount * reward_to_risk if is_win else -risk_amount
+
+        balance += trade_result
+        daily_pnl += trade_result
+
+        if balance >= target_balance:
+            return "pass", trade_num
+
+        if balance <= min_balance_allowed or daily_pnl <= -daily_loss_amount:
+            return "fail", trade_num
+
+    return "incomplete", max_trades
+
+
+def simulate_challenge(
+    challenge_type: str,
+    phase1_target_pct: float,
+    phase2_target_pct: float,
+    starting_balance: float,
+    max_drawdown_pct: float,
+    daily_loss_limit_pct: float,
+    risk_per_trade_pct: float,
+    win_rate_pct: float,
+    reward_to_risk: float,
+    trades_per_day: int,
+    max_trades: int,
+    simulations: int,
+    seed: int = 42,
+):
+    rng = random.Random(seed)
+
+    phase1_counts = {"pass": 0, "fail": 0, "incomplete": 0}
+    phase2_counts = {"pass": 0, "fail": 0, "incomplete": 0}
+    overall_counts = {"pass": 0, "fail": 0, "incomplete": 0}
+    fail_trade_counts = []
+
+    for _ in range(simulations):
+        p1_outcome, p1_trades = simulate_phase(
+            starting_balance=starting_balance,
+            profit_target_pct=phase1_target_pct,
+            max_drawdown_pct=max_drawdown_pct,
+            daily_loss_limit_pct=daily_loss_limit_pct,
+            risk_per_trade_pct=risk_per_trade_pct,
+            win_rate_pct=win_rate_pct,
+            reward_to_risk=reward_to_risk,
+            trades_per_day=trades_per_day,
+            max_trades=max_trades,
+            rng=rng,
+        )
+        phase1_counts[p1_outcome] += 1
+
+        if p1_outcome == "fail":
+            overall_counts["fail"] += 1
+            fail_trade_counts.append(p1_trades)
+            continue
+
+        if p1_outcome == "incomplete":
+            overall_counts["incomplete"] += 1
+            continue
+
+        if challenge_type == "1-Step":
+            overall_counts["pass"] += 1
+            continue
+
+        p2_outcome, p2_trades = simulate_phase(
+            starting_balance=starting_balance,
+            profit_target_pct=phase2_target_pct,
+            max_drawdown_pct=max_drawdown_pct,
+            daily_loss_limit_pct=daily_loss_limit_pct,
+            risk_per_trade_pct=risk_per_trade_pct,
+            win_rate_pct=win_rate_pct,
+            reward_to_risk=reward_to_risk,
+            trades_per_day=trades_per_day,
+            max_trades=max_trades,
+            rng=rng,
+        )
+        phase2_counts[p2_outcome] += 1
+
+        if p2_outcome == "pass":
+            overall_counts["pass"] += 1
+        elif p2_outcome == "fail":
+            overall_counts["fail"] += 1
+            fail_trade_counts.append(p1_trades + p2_trades)
+        else:
+            overall_counts["incomplete"] += 1
+
+    fail_only = fail_trade_counts if fail_trade_counts else []
+    median_trades_to_fail = statistics.median(fail_only) if fail_only else None
+
+    return {
+        "phase1": phase1_counts,
+        "phase2": phase2_counts,
+        "overall": overall_counts,
+        "simulations": simulations,
+        "median_trades_to_fail": median_trades_to_fail,
+    }
+
+
+col1, col2 = st.columns(2)
+with col1:
+    starting_balance = st.number_input("💼 Starting Balance (USD)", min_value=1000, value=100000, step=1000)
+    challenge_type = st.selectbox("🏁 Challenge Type", ["1-Step", "2-Step"], index=1)
+    phase1_target_pct = st.number_input("🎯 Phase 1 Profit Target (%)", min_value=1.0, max_value=50.0, value=8.0, step=0.5)
+    phase2_target_pct = st.number_input(
+        "🎯 Phase 2 Profit Target (%)",
+        min_value=1.0,
+        max_value=50.0,
+        value=5.0 if challenge_type == "2-Step" else phase1_target_pct,
+        step=0.5,
+        disabled=challenge_type == "1-Step",
+    )
+
+with col2:
+    max_drawdown_pct = st.number_input("📉 Max Overall Drawdown (%)", min_value=1.0, max_value=50.0, value=10.0, step=0.5)
+    daily_loss_limit_pct = st.number_input("🛑 Daily Loss Limit (%)", min_value=0.5, max_value=20.0, value=5.0, step=0.5)
+    risk_per_trade_pct = st.number_input("🎯 Risk per Trade (%)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
+    win_rate_pct = st.slider("✅ Win Rate (%)", min_value=1, max_value=99, value=45)
+
+col3, col4 = st.columns(2)
+with col3:
+    reward_to_risk = st.number_input("⚖️ Reward:Risk Ratio", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
+    trades_per_day = st.number_input("📅 Trades per Day", min_value=1, max_value=50, value=3, step=1)
+with col4:
+    max_trades = st.number_input("🔢 Max Trades per Phase", min_value=10, max_value=5000, value=300, step=10)
+    simulations = st.slider("🧪 Monte Carlo Simulations", min_value=500, max_value=20000, value=5000, step=500)
+
+if st.button("Run Challenge Probability Simulation"):
+    results = simulate_challenge(
+        challenge_type=challenge_type,
+        phase1_target_pct=float(phase1_target_pct),
+        phase2_target_pct=float(phase2_target_pct),
+        starting_balance=float(starting_balance),
+        max_drawdown_pct=float(max_drawdown_pct),
+        daily_loss_limit_pct=float(daily_loss_limit_pct),
+        risk_per_trade_pct=float(risk_per_trade_pct),
+        win_rate_pct=float(win_rate_pct),
+        reward_to_risk=float(reward_to_risk),
+        trades_per_day=int(trades_per_day),
+        max_trades=int(max_trades),
+        simulations=int(simulations),
+    )
+
+    phase1_pass_pct = results["phase1"]["pass"] / results["simulations"] * 100
+    phase1_fail_pct = results["phase1"]["fail"] / results["simulations"] * 100
+    overall_pass_pct = results["overall"]["pass"] / results["simulations"] * 100
+    overall_fail_pct = results["overall"]["fail"] / results["simulations"] * 100
+
+    st.markdown(
+        f"""
+<div class="panel">
+    <div class="metric-label">Phase 1 Pass Probability</div>
+    <div class="metric-value">{phase1_pass_pct:.2f}%</div>
+    <div class="metric-label">Phase 1 Fail Probability</div>
+    <div class="metric-value">{phase1_fail_pct:.2f}%</div>
+""",
+        unsafe_allow_html=True,
+    )
+
+    if challenge_type == "2-Step":
+        phase2_reached = results["phase1"]["pass"]
+        phase2_pass_pct_unconditional = results["phase2"]["pass"] / results["simulations"] * 100
+        phase2_pass_pct_conditional = (
+            (results["phase2"]["pass"] / phase2_reached) * 100 if phase2_reached else 0.0
+        )
+
+        st.markdown(
+            f"""
+<div class="panel" style="margin-top:12px;">
+    <div class="metric-label">Phase 2 Reached (after passing P1)</div>
+    <div class="metric-value">{phase2_reached:,} / {results['simulations']:,}</div>
+    <div class="metric-label">Phase 2 Pass Probability (overall)</div>
+    <div class="metric-value">{phase2_pass_pct_unconditional:.2f}%</div>
+    <div class="metric-label">Phase 2 Pass Probability (given P1 pass)</div>
+    <div class="metric-value">{phase2_pass_pct_conditional:.2f}%</div>
+</div>
+""",
+            unsafe_allow_html=True,
+        )
+
+    st.markdown(
+        f"""
+<div class="panel" style="margin-top:12px;">
+    <div class="metric-label">Challenge Pass Probability (overall)</div>
+    <div class="metric-value">{overall_pass_pct:.2f}%</div>
+    <div class="metric-label">Challenge Fail Probability (overall)</div>
+    <div class="metric-value">{overall_fail_pct:.2f}%</div>
+    <div class="metric-label">Median Trades to Failure (failed paths only)</div>
+    <div class="metric-value">{results['median_trades_to_fail'] if results['median_trades_to_fail'] is not None else 'Not reached'}</div>
+</div>
+""",
+        unsafe_allow_html=True,
+    )
+
+st.markdown("---")
+st.caption(
+    "Tip: For your strategy profile (wins, losses, breakeven, partials), use expectancy-adjusted Win Rate and Reward:Risk until multi-outcome modeling is added."
+)
+st.caption(
+    "This is a probabilistic estimate, not financial advice. Actual results vary with execution, slippage, and prop-firm rule interpretation."
+)
 
EOF
)