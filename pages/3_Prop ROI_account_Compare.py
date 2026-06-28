import streamlit as st

# Force wide mode to utilize the full screen space horizontally
st.set_page_config(page_title="Stoic Capital Dashboard", layout="wide")

st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>⚖️ Prop Firm Strategy & Risk Analytics Dashboard</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Designed for 1:1 Risk-to-Reward Execution Models</p>", unsafe_allow_html=True)
st.write("---")

# --- HORIZONTAL INPUT CONTROL CENTER ---
# Splitting controls into 3 tight columns to eliminate vertical scrolling
col_global, col_twostep, col_instant = st.columns(3, gap="medium")

with col_global:
    st.markdown("### 🌐 Global & Targets")
    account_size = st.number_input("Account Size ($)", value=10000, step=1000)
    target_return_pct = st.slider("Strategy Return Target (%)", min_value=1, max_value=40, value=15)
    
    # Pack consistency items tightly
    c_left, c_right = st.columns(2)
    with c_left:
        consistency_pct = st.number_input("Consistency Limit (%)", value=15.0, step=1.0)
    with c_right:
        best_day_r = st.number_input("Best Day Net Wins (+R)", value=1, min_value=1)

with col_twostep:
    st.markdown("### 🥈 Two-Step Configuration")
    
    t_cost, t_split = st.columns(2)
    with t_cost:
        twostep_cost = st.number_input("Two-Step Cost ($)", value=35)
    with t_split:
        twostep_split = st.slider("Two-Step Split (%)", 50, 100, 85)
        
    p1, p2 = st.columns(2)
    with p1:
        p1_target = st.number_input("Phase 1 Target (%)", value=8.0, step=0.5)
    with p2:
        p2_target = st.number_input("Phase 2 Target (%)", value=5.0, step=0.5)
    total_eval_pct_required = p1_target + p2_target

    twostep_risk_type = st.radio("Risk Mode (Two-Step)", ["% of Account", "Fixed $ Amount"], horizontal=True)
    if twostep_risk_type == "% of Account":
        twostep_risk_pct = st.number_input("TS Risk Per Trade (%)", value=1.0, step=0.1)
        twostep_risk_per_trade = account_size * (twostep_risk_pct / 100)
    else:
        twostep_risk_per_trade = st.number_input("TS Risk Per Trade ($)", value=100.0, step=10.0)

with col_instant:
    st.markdown("### 🚀 Instant Configuration")
    
    i_cost, i_split = st.columns(2)
    with i_cost:
        instant_cost = st.number_input("Instant Cost ($)", value=84)
    with i_split:
        instant_split = st.slider("Instant Split (%)", 50, 100, 85)
        
    i_dd, i_buf = st.columns(2)
    with i_dd:
        instant_drawdown_pct = st.number_input("Max Drawdown (%)", value=6.0, step=1.0)
    with i_buf:
        instant_buffer_pct = st.number_input("Withdrawal Buffer (%)", value=0.0, step=1.0, help="Firms that don't reset trailing drawdown require you to leave this profit buffer in the account upon withdrawal.")

    instant_risk_type = st.radio("Risk Mode (Instant)", ["% of Drawdown", "Fixed $ Amount"], horizontal=True)
    instant_total_drawdown_dollars = account_size * (instant_drawdown_pct / 100)
    
    if instant_risk_type == "% of Drawdown":
        instant_risk_pct = st.number_input("Instant Risk Per Trade (%)", value=10.0, step=1.0)
        instant_risk_per_trade = instant_total_drawdown_dollars * (instant_risk_pct / 100)
    else:
        instant_risk_per_trade = st.number_input("Instant Risk Per Trade ($)", value=60.0, step=5.0)

st.write("---")

# --- MATH LOGIC & METRICS ---
# Two-Step Payout
if target_return_pct <= total_eval_pct_required:
    twostep_net_payout = -twostep_cost
    twostep_status = f"Evaluating (Needs +{total_eval_pct_required - target_return_pct:.1f}%)"
else:
    funded_growth_pct = target_return_pct - total_eval_pct_required
    total_growth_dollars = account_size * (funded_growth_pct / 100)
    live_r_wins = total_growth_dollars / (account_size * 0.01)
    twostep_gross_funded_profit = live_r_wins * twostep_risk_per_trade
    twostep_net_payout = (twostep_gross_funded_profit * (twostep_split / 100))
    twostep_status = "Live Stage Unlocked (Fee Refunded)"

# Instant Payout incorporating the buffer system
instant_gross_profit = (account_size * (target_return_pct / 100) / (account_size * 0.01)) * instant_risk_per_trade
buffer_dollars = account_size * (instant_buffer_pct / 100)

# Calculate what is actually safe to pull out
withdrawable_profit = max(0.0, instant_gross_profit - buffer_dollars)
instant_net_payout = (withdrawable_profit * (instant_split / 100)) - instant_cost

# Consistency check calculations
best_day_profit = best_day_r * instant_risk_per_trade
actual_consistency_ratio = (best_day_profit / instant_gross_profit) * 100 if instant_gross_profit > 0 else 0
violates_consistency = actual_consistency_ratio > consistency_pct

# --- VISUAL RESULTS MATRIX ---
st.markdown("### 📊 Live Performance Metrics")
st.write(f"**Calculated Risk Units:** Two-Step Sizing = `${twostep_risk_per_trade:,.2f}` | Instant Sizing = `${instant_risk_per_trade:,.2f}`")

out_ts, out_inst, out_verdict = st.columns([1, 1, 1.2], gap="medium")

with out_ts:
    st.metric(label="Two-Step Pocket Return", value=f"${twostep_net_payout:,.2f}")
    st.caption(f"**Status:** {twostep_status}")

with out_inst:
    st.metric(label="Instant Pocket Return", value=f"${instant_net_payout:,.2f}")
    if buffer_dollars > 0:
        st.caption(f"**Locked Buffer:** `${buffer_dollars:,.0f}` inside account")
    else:
        st.caption("**Status:** Account resets on payout (No Buffer)")

with out_verdict:
    if twostep_net_payout > instant_net_payout:
        st.error(f"📈 **Winner: Two-Step** (+${twostep_net_payout - instant_net_payout:,.2f} advantage)")
    elif instant_net_payout > twostep_net_payout:
        st.success(f"🎯 **Winner: Instant** (+${instant_net_payout - twostep_net_payout:,.2f} advantage)")
    else:
        st.info("⚖️ **Models Balanced Perfectly**")

# --- COMPLIANCE FOOTER ---
if violates_consistency:
    st.error(f"⚠️ **Instant Consistency Warning:** Your best day ({best_day_r}R = ${best_day_profit:,.2f}) accounts for **{actual_consistency_ratio:.1f}%** of your profit pool. To withdraw, target must increase until your gross profit hits **${(best_day_profit / (consistency_pct / 100)):,.2f}**.")
else:
    st.success(f"✅ **Instant Consistency Compliant:** Best day is {actual_consistency_ratio:.1f}% of profit pool (safely below the {consistency_pct}% rule).")
