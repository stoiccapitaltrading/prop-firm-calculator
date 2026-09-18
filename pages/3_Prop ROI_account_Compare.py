import streamlit as st

from calculator_models import (
    net_profit,
    r_required_for_percentage_target,
    return_on_cost,
)

# Configure wide page layout to maximize horizontal viewing space
st.set_page_config(page_title="Stoic Capital Dashboard", layout="wide")

st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>⚖️ Prop Firm Strategy & ROI Analytics Dashboard</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Compare Two-Step vs. Instant Funding using Custom Budgets & Risk Normalization</p>", unsafe_allow_html=True)
st.write("---")

# Splitting controls into 3 columns to eliminate vertical scrolling and keep inputs immediately visible
col_global, col_twostep, col_instant = st.columns(3, gap="medium")

with col_global:
    st.markdown("### 🌐 Strategy Targets")
    target_return_r = st.slider(
        "Strategy Target (Net R Wins)",
        min_value=1,
        max_value=40,
        value=15,
        help="Total strategy performance in R. Evaluation targets consume R using evaluation-stage risk.",
    )

with col_twostep:
    st.markdown("### 🥈 Two-Step Configuration")
    
    # Decouple Two-Step Account Size
    ts_size, ts_cost = st.columns(2)
    with ts_size:
        twostep_account_size = st.number_input("TS Account Size ($)", min_value=1000, value=10000, step=1000)
    with ts_cost:
        twostep_cost = st.number_input("Two-Step Cost ($)", min_value=1, value=35)
        
    p1, p2 = st.columns(2)
    with p1:
        p1_target_pct = st.number_input("Phase 1 Target (%)", value=8.0, step=0.5)
    with p2:
        p2_target_pct = st.number_input("Phase 2 Target (%)", value=5.0, step=0.5)
    total_eval_target_pct = p1_target_pct + p2_target_pct
    
    twostep_split = st.slider("Two-Step Split (%)", 50, 100, 85)

    eval_risk_col, funded_risk_col = st.columns(2)
    with eval_risk_col:
        st.caption("Evaluation Risk")
        twostep_eval_risk_type = st.radio(
            "Risk Mode (Evaluation)",
            ["% of Account", "Fixed $ Amount"],
            horizontal=True,
            key="ts_eval_risk_mode",
        )
        if twostep_eval_risk_type == "% of Account":
            twostep_eval_risk_pct = st.number_input(
                "Evaluation Risk Per Trade (%)", value=1.0, step=0.1
            )
            twostep_eval_risk_per_trade = twostep_account_size * (
                twostep_eval_risk_pct / 100
            )
        else:
            twostep_eval_risk_per_trade = st.number_input(
                "Evaluation Risk Per Trade ($)", value=100.0, step=10.0
            )

    with funded_risk_col:
        st.caption("Funded-Stage Risk")
        twostep_funded_risk_type = st.radio(
            "Risk Mode (Funded Stage)",
            ["% of Account", "Fixed $ Amount"],
            horizontal=True,
            key="ts_funded_risk_mode",
        )
        if twostep_funded_risk_type == "% of Account":
            twostep_funded_risk_pct = st.number_input(
                "Funded Risk Per Trade (%)", value=1.0, step=0.1
            )
            twostep_funded_risk_per_trade = twostep_account_size * (
                twostep_funded_risk_pct / 100
            )
        else:
            twostep_funded_risk_per_trade = st.number_input(
                "Funded Risk Per Trade ($)", value=100.0, step=10.0
            )

    phase_one_required_r = r_required_for_percentage_target(
        twostep_account_size, p1_target_pct, twostep_eval_risk_per_trade
    )
    phase_two_required_r = r_required_for_percentage_target(
        twostep_account_size, p2_target_pct, twostep_eval_risk_per_trade
    )
    total_eval_r_required = phase_one_required_r + phase_two_required_r
    st.caption(
        f"Evaluation requirement: {p1_target_pct:.1f}% = {phase_one_required_r:.2f}R "
        f"and {p2_target_pct:.1f}% = {phase_two_required_r:.2f}R "
        f"({total_eval_r_required:.2f}R total)"
    )

with col_instant:
    st.markdown("### 🚀 Instant Configuration")
    
    # Decouple Instant Account Size
    i_size, i_cost = st.columns(2)
    with i_size:
        instant_account_size = st.number_input("Instant Account Size ($)", min_value=1000, value=5000, step=1000)
    with i_cost:
        instant_cost = st.number_input("Instant Cost ($)", min_value=1, value=84)
        
    i_dd, i_buf = st.columns(2)
    with i_dd:
        instant_drawdown_pct = st.number_input("Max Drawdown (%)", min_value=0.1, max_value=100.0, value=6.0, step=1.0)
    with i_buf:
        instant_buffer_pct = st.number_input("Withdrawal Buffer (%)", value=0.0, step=1.0, help="Firms that don't reset trailing drawdown require you to leave this profit buffer in the account upon withdrawal.")
        
    instant_split = st.slider("Instant Split (%)", 50, 100, 85)

    instant_consistency_col, instant_best_day_col = st.columns(2)
    with instant_consistency_col:
        instant_consistency_pct = st.number_input(
            "Instant Consistency Limit (%)",
            min_value=0.1,
            max_value=100.0,
            value=15.0,
            step=1.0,
        )
    with instant_best_day_col:
        instant_best_day_r = st.number_input(
            "Instant Best-Day Net Wins (+R)", value=1, min_value=1
        )

    instant_risk_type = st.radio("Risk Mode (Instant)", ["% of Drawdown", "Fixed $ Amount"], horizontal=True, key="inst_risk_mode")
    instant_total_drawdown_dollars = instant_account_size * (instant_drawdown_pct / 100)
    
    if instant_risk_type == "% of Drawdown":
        instant_risk_pct = st.number_input("Instant Risk Per Trade (%)", value=10.0, step=1.0)
        instant_risk_per_trade = instant_total_drawdown_dollars * (instant_risk_pct / 100)
    else:
        instant_risk_per_trade = st.number_input("Instant Risk Per Trade ($)", value=30.0, step=5.0)

st.write("---")

# 1. Two-Step Performance Engine
# Percentage phase targets are converted to R using the evaluation-stage risk.
if target_return_r <= total_eval_r_required:
    twostep_cash_received = 0.0
    twostep_net_profit = -twostep_cost
    twostep_roi = return_on_cost(twostep_net_profit, twostep_cost)
    twostep_status = f"Evaluating (Needs +{total_eval_r_required - target_return_r:.1f} R)"
else:
    funded_r_wins = target_return_r - total_eval_r_required
    twostep_gross_funded_profit = funded_r_wins * twostep_funded_risk_per_trade
    # Cash received includes the returned fee; net profit correctly removes
    # the original fee once, making the comparison consistent with Instant.
    twostep_cash_received = (
        twostep_gross_funded_profit * (twostep_split / 100)
    ) + twostep_cost
    twostep_net_profit = net_profit(twostep_cash_received, twostep_cost)
    twostep_roi = return_on_cost(twostep_net_profit, twostep_cost)
    twostep_status = "Funded Stage Unlocked (Fee Refunded)"

# 2. Instant Performance Engine with Trailing Buffer Protection
instant_gross_profit = target_return_r * instant_risk_per_trade
buffer_dollars = instant_account_size * (instant_buffer_pct / 100)

# The buffer remains in the account and is not treated as withdrawable cash.
withdrawable_profit = max(0.0, instant_gross_profit - buffer_dollars)
instant_cash_received = withdrawable_profit * (instant_split / 100)
instant_net_profit = net_profit(instant_cash_received, instant_cost)
instant_roi = return_on_cost(instant_net_profit, instant_cost)

# 3. Consistency Rule Verification
best_day_profit = instant_best_day_r * instant_risk_per_trade
actual_consistency_ratio = (best_day_profit / instant_gross_profit) * 100 if instant_gross_profit > 0 else 0
violates_consistency = actual_consistency_ratio > instant_consistency_pct

st.markdown("### 📊 Live Performance & Return on Investment (ROI) Matrix")
st.write(
    "**Sizing Normalization:** "
    f"Evaluation = `${twostep_eval_risk_per_trade:,.2f}/trade` | "
    f"Funded Stage = `${twostep_funded_risk_per_trade:,.2f}/trade` | "
    f"Instant = `${instant_risk_per_trade:,.2f}/trade`"
)

# Three balanced columns displaying Two-step, Instant, and the side-by-side verdict
out_ts, out_inst, out_verdict = st.columns([1, 1, 1.2], gap="medium")

with out_ts:
    st.markdown(f"#### 🥈 Two-Step ({twostep_account_size/1000:,.0f}k Account)")
    st.metric(label="Net Profit After Cost", value=f"${twostep_net_profit:,.2f}")
    st.metric(label="Return on Cost (ROI)", value=f"{twostep_roi:,.1f}%")
    st.caption(f"**Status:** {twostep_status}")
    st.caption(
        f"Evaluation required: {total_eval_target_pct:.1f}% = {total_eval_r_required:.2f}R"
    )
    if twostep_cash_received > 0:
        st.caption(f"Cash received (including fee refund): `${twostep_cash_received:,.2f}`")

with out_inst:
    st.markdown(f"#### 🚀 Instant ({instant_account_size/1000:,.0f}k Account)")
    st.metric(label="Net Profit After Cost", value=f"${instant_net_profit:,.2f}")
    st.metric(label="Return on Cost (ROI)", value=f"{instant_roi:,.1f}%")
    if buffer_dollars > 0:
        st.caption(f"**Locked Buffer:** `${buffer_dollars:,.2f}` active inside account")
    else:
        st.caption("**Status:** Reset on payout (No Trailing Buffer)")
    st.caption(f"Cash received before account cost: `${instant_cash_received:,.2f}`")

with out_verdict:
    st.markdown("#### 🎯 Strategic Analysis Verdict")
    
    # Evaluate which option is mathematically superior based on ROI
    if twostep_roi > instant_roi:
        st.error(f"📈 **Winner: Two-Step** (+{twostep_roi - instant_roi:,.1f}% ROI advantage)")
        st.info("💡 **Why:** Even with the evaluation phase, the larger account size your budget unlocked on the Two-Step leverages your strategy's wins into massive relative payouts.")
    elif instant_roi > twostep_roi:
        st.success(f"🎯 **Winner: Instant** (+{instant_roi - twostep_roi:,.1f}% ROI advantage)")
        st.info("💡 **Why:** Starting live from day 1 allows you to extract cash immediately, making the Instant account highly cost-effective at this target range.")
    else:
        st.info("⚖️ **Models Balanced Perfectly**")

st.write("---")

if violates_consistency:
    st.error(f"⚠️ **Instant Consistency Warning:** Your best day ({instant_best_day_r}R = ${best_day_profit:,.2f}) accounts for **{actual_consistency_ratio:.1f}%** of your total profit pool. To successfully withdraw, target must increase until your gross profit hits **${(best_day_profit / (instant_consistency_pct / 100)):,.2f}**.")
else:
    st.success(f"✅ **Instant Consistency Compliant:** Best day represents {actual_consistency_ratio:.1f}% of profit pool, staying safely below the {instant_consistency_pct}% rule.")
