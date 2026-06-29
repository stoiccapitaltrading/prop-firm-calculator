import streamlit as st

# Configure wide page layout to maximize horizontal viewing space
st.set_page_config(page_title="Stoic Capital Dashboard", layout="wide")

st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>⚖️ Prop Firm Strategy & ROI Analytics Dashboard</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Compare Two-Step vs. Instant Funding using Custom Budgets & Risk Normalization</p>", unsafe_allow_html=True)
st.write("---")

# Splitting controls into 3 columns to eliminate vertical scrolling and keep inputs immediately visible
col_global, col_twostep, col_instant = st.columns(3, gap="medium")

with col_global:
    st.markdown("### 🌐 Strategy Targets")
    # Using 'R Units' (Net Wins) to perfectly normalize strategy target across differing account balances
    target_return_r = st.slider("Strategy Target (Net R Wins / % at 1% Risk)", min_value=1, max_value=40, value=15)
    
    # Pack consistency items tightly
    c_left, c_right = st.columns(2)
    with c_left:
        consistency_pct = st.number_input("Consistency Limit (%)", value=15.0, step=1.0)
    with c_right:
        best_day_r = st.number_input("Best Day Net Wins (+R)", value=1, min_value=1)

with col_twostep:
    st.markdown("### 🥈 Two-Step Configuration")
    
    # Decouple Two-Step Account Size
    ts_size, ts_cost = st.columns(2)
    with ts_size:
        twostep_account_size = st.number_input("TS Account Size ($)", value=10000, step=1000)
    with ts_cost:
        twostep_cost = st.number_input("Two-Step Cost ($)", value=35)
        
    p1, p2 = st.columns(2)
    with p1:
        p1_target = st.number_input("Phase 1 Target (R)", value=8.0, step=0.5)
    with p2:
        p2_target = st.number_input("Phase 2 Target (R)", value=5.0, step=0.5)
    total_eval_pct_required = p1_target + p2_target
    
    twostep_split = st.slider("Two-Step Split (%)", 50, 100, 85)

    twostep_risk_type = st.radio("Risk Mode (Two-Step)", ["% of Account", "Fixed $ Amount"], horizontal=True, key="ts_risk_mode")
    if twostep_risk_type == "% of Account":
        twostep_risk_pct = st.number_input("TS Risk Per Trade (%)", value=1.0, step=0.1)
        twostep_risk_per_trade = twostep_account_size * (twostep_risk_pct / 100)
    else:
        twostep_risk_per_trade = st.number_input("TS Risk Per Trade ($)", value=100.0, step=10.0)

with col_instant:
    st.markdown("### 🚀 Instant Configuration")
    
    # Decouple Instant Account Size
    i_size, i_cost = st.columns(2)
    with i_size:
        instant_account_size = st.number_input("Instant Account Size ($)", value=5000, step=1000)
    with i_cost:
        instant_cost = st.number_input("Instant Cost ($)", value=84)
        
    i_dd, i_buf = st.columns(2)
    with i_dd:
        instant_drawdown_pct = st.number_input("Max Drawdown (%)", value=6.0, step=1.0)
    with i_buf:
        instant_buffer_pct = st.number_input("Withdrawal Buffer (%)", value=0.0, step=1.0, help="Firms that don't reset trailing drawdown require you to leave this profit buffer in the account upon withdrawal.")
        
    instant_split = st.slider("Instant Split (%)", 50, 100, 85)

    instant_risk_type = st.radio("Risk Mode (Instant)", ["% of Drawdown", "Fixed $ Amount"], horizontal=True, key="inst_risk_mode")
    instant_total_drawdown_dollars = instant_account_size * (instant_drawdown_pct / 100)
    
    if instant_risk_type == "% of Drawdown":
        instant_risk_pct = st.number_input("Instant Risk Per Trade (%)", value=10.0, step=1.0)
        instant_risk_per_trade = instant_total_drawdown_dollars * (instant_risk_pct / 100)
    else:
        instant_risk_per_trade = st.number_input("Instant Risk Per Trade ($)", value=30.0, step=5.0)

st.write("---")

# 1. Two-Step Performance Engine
if target_return_r <= total_eval_pct_required:
    twostep_net_payout = -twostep_cost
    twostep_roi = -100.0
    twostep_status = f"Evaluating (Needs +{total_eval_pct_required - target_return_r:.1f} R)"
else:
    funded_r_wins = target_return_r - total_eval_pct_required
    twostep_gross_funded_profit = funded_r_wins * twostep_risk_per_trade
    # Profit split + upfront registration fee refund on first payout
    twostep_net_payout = (twostep_gross_funded_profit * (twostep_split / 100)) + twostep_cost
    twostep_roi = (twostep_net_payout / twostep_cost) * 100 if twostep_cost > 0 else 0
    twostep_status = "Funded Stage Unlocked (Fee Refunded!)"

# 2. Instant Performance Engine with Trailing Buffer Protection
instant_gross_profit = target_return_r * instant_risk_per_trade
buffer_dollars = instant_account_size * (instant_buffer_pct / 100)

# Calculate net withdrawable profit (keeping the lock-in buffer inside the account)
withdrawable_profit = max(0.0, instant_gross_profit - buffer_dollars)
instant_net_payout = (withdrawable_profit * (instant_split / 100)) - instant_cost
instant_roi = (instant_net_payout / instant_cost) * 100 if instant_cost > 0 else 0

# 3. Consistency Rule Verification
best_day_profit = best_day_r * instant_risk_per_trade
actual_consistency_ratio = (best_day_profit / instant_gross_profit) * 100 if instant_gross_profit > 0 else 0
violates_consistency = actual_consistency_ratio > consistency_pct

st.markdown("### 📊 Live Performance & Return on Investment (ROI) Matrix")
st.write(f"**Sizing Normalization:** Two-Step Sizing = `${twostep_risk_per_trade:,.2f}/trade` | Instant Sizing = `${instant_risk_per_trade:,.2f}/trade`")

# Three balanced columns displaying Two-step, Instant, and the side-by-side verdict
out_ts, out_inst, out_verdict = st.columns([1, 1, 1.2], gap="medium")

with out_ts:
    st.markdown(f"#### 🥈 Two-Step ({twostep_account_size/1000:,.0f}k Account)")
    st.metric(label="Net Pocket Cash", value=f"${twostep_net_payout:,.2f}")
    st.metric(label="Return on Cost (ROI)", value=f"{twostep_roi:,.1f}%")
    st.caption(f"**Status:** {twostep_status}")

with out_inst:
    st.markdown(f"#### 🚀 Instant ({instant_account_size/1000:,.0f}k Account)")
    st.metric(label="Net Pocket Cash", value=f"${instant_net_payout:,.2f}")
    st.metric(label="Return on Cost (ROI)", value=f"{instant_roi:,.1f}%")
    if buffer_dollars > 0:
        st.caption(f"**Locked Buffer:** `${buffer_dollars:,.2f}` active inside account")
    else:
        st.caption("**Status:** Reset on payout (No Trailing Buffer)")

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
    st.error(f"⚠️ **Instant Consistency Warning:** Your best day ({best_day_r}R = ${best_day_profit:,.2f}) accounts for **{actual_consistency_ratio:.1f}%** of your total profit pool. To successfully withdraw, target must increase until your gross profit hits **${(best_day_profit / (consistency_pct / 100)):,.2f}**.")
else:
    st.success(f"✅ **Instant Consistency Compliant:** Best day represents {actual_consistency_ratio:.1f}% of profit pool, staying safely below the {consistency_pct}% rule.")
