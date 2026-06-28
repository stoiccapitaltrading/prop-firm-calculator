import streamlit as st

# Page configuration for a professional clean layout
st.set_page_config(page_title="Prop Firm account ROI compare", layout="wide")
st.title("⚖️ Custom Prop Firm Strategy & Profit comparison")
st.subheader("Stoic Capital Account Comparison Analytics")
st.write("---")

# Layout columns for splitting inputs and results visually
col_inputs, col_results = st.columns([1, 2], gap="large")

with col_inputs:
    st.header("1. Global Settings")
    account_size = st.number_input("Account Size ($)", value=10000, step=1000)
    target_return_pct = st.slider("Your Strategy Return Target (%)", min_value=1, max_value=40, value=15)
    
    st.write("---")
    st.header("2. Two-Step Settings")
    twostep_cost = st.number_input("Two-Step Cost ($)", value=35)
    
    # Individual phase controls
    p1_target = st.number_input("Phase 1 Target (%)", value=8.0, step=0.5)
    p2_target = st.number_input("Phase 2 Target (%)", value=5.0, step=0.5)
    total_eval_pct_required = p1_target + p2_target
    st.caption(f"**Total Required Evaluation Growth:** {total_eval_pct_required}%")
    
    twostep_split = st.slider("Two-Step Profit Split (%)", 50, 100, 85)
    
    # Flexible Risk Selection for Two-Step
    twostep_risk_type = st.radio("Two-Step Risk Entry Mode", ["% of Account Size", "Fixed Dollar Amount ($)"], key="ts_risk")
    if twostep_risk_type == "% of Account Size":
        twostep_risk_pct = st.number_input("Risk per Trade (% of Account)", value=1.0, step=0.1)
        twostep_risk_per_trade = account_size * (twostep_risk_pct / 100)
    else:
        twostep_risk_per_trade = st.number_input("Risk per Trade ($ Amount)", value=100.0, step=10.0)

    st.write("---")
    st.header("3. Instant Settings")
    instant_cost = st.number_input("Instant Cost ($)", value=84)
    instant_drawdown_pct = st.number_input("Instant Max Drawdown (%)", value=6.0, step=1.0)
    instant_split = st.slider("Instant Profit Split (%)", 50, 100, 85)
    
    # Flexible Risk Selection for Instant
    instant_risk_type = st.radio("Instant Risk Entry Mode", ["% of Available Drawdown Pool", "Fixed Dollar Amount ($)"], key="inst_risk")
    instant_total_drawdown_dollars = account_size * (instant_drawdown_pct / 100)
    
    if instant_risk_type == "% of Available Drawdown Pool":
        instant_risk_pct = st.number_input("Risk per Trade (% of Drawdown Pool)", value=10.0, step=1.0)
        instant_risk_per_trade = instant_total_drawdown_dollars * (instant_risk_pct / 100)
    else:
        instant_risk_per_trade = st.number_input("Instant Risk per Trade ($ Amount)", value=60.0, step=5.0)
        
    st.caption(f"**Instant Absolute Drawdown Pool:** ${instant_total_drawdown_dollars:,.2f}")
    
    st.write("---")
    st.header("4. Rules & Rules Controls")
    consistency_pct = st.number_input("Consistency Rule Limit (%)", value=15.0, step=1.0)
    best_day_r = st.number_input("Best Day Net Wins (+R)", value=1, min_value=1)

with col_results:
    st.header("Performance Comparison Outputs")
    st.write(f"**Calculated Dollars Risked Per Trade:** Two-Step = `${twostep_risk_per_trade:,.2f}` | Instant = `${instant_risk_per_trade:,.2f}`")
    
    # --- TWO-STEP CALCULATIONS ---
    if target_return_pct <= total_eval_pct_required:
        twostep_net_payout = -twostep_cost
        twostep_status = "Evaluating Stage ($0 payouts unlocked)"
    else:
        funded_growth_pct = target_return_pct - total_eval_pct_required
        # Converting strategy growth percentage to equivalent dollar growth on total account, then measuring by risk units
        total_growth_dollars = account_size * (funded_growth_pct / 100)
        # Assuming the strategy targets a 1% account growth step as a benchmark R unit
        live_r_wins = total_growth_dollars / (account_size * 0.01)
        twostep_gross_funded_profit = live_r_wins * twostep_risk_per_trade
        twostep_net_payout = (twostep_gross_funded_profit * (twostep_split / 100))
        twostep_status = "Live Stage Unlocked (Fee Refunded)"

    # --- INSTANT CALCULATIONS ---
    instant_total_r_wins = target_return_pct
    instant_gross_profit = (account_size * (target_return_pct / 100) / (account_size * 0.01)) * instant_risk_per_trade
    instant_net_payout = (instant_gross_profit * (instant_split / 100)) - instant_cost

    # --- CONSISTENCY METRICS ---
    best_day_profit = best_day_r * instant_risk_per_trade
    actual_consistency_ratio = (best_day_profit / instant_gross_profit) * 100 if instant_gross_profit > 0 else 0
    violates_consistency = actual_consistency_ratio > consistency_pct

    # --- SCOREBOARD DISPLAY ---
    c1, c2 = st.columns(2)
    with c1:
        st.metric(label="Two-Step Net Pocket Profit", value=f"${twostep_net_payout:,.2f}")
        st.info(f"**Two-Step Status:** {twostep_status}")
    with c2:
        st.metric(label="Instant Net Pocket Profit", value=f"${instant_net_payout:,.2f}")
        st.info("**Instant Status:** Live from Day 1")

    st.write("---")
    st.subheader("Compliance & Execution Insights")
    
    if violates_consistency:
        st.error(f"⚠️ **Instant Consistency Violation:** Your best single day ({best_day_r}R = ${best_day_profit:,.2f}) makes up **{actual_consistency_ratio:.1f}%** of your account profit pool. To satisfy the {consistency_pct}% rule, you must trade onwards until your total account gross profit reaches at least **${(best_day_profit / (consistency_pct / 100)):,.2f}**.")
    else:
        st.success(f"✅ **Instant Consistency Compliant:** Your best day represents {actual_consistency_ratio:.1f}% of total profits, staying clear of the safety ceiling.")

    # Strategic advice engine
    if twostep_net_payout > instant_net_payout:
        st.warning(f"📈 **Verdict:** The **Two-Step** configuration scales higher at this level because your selected risk size (${twostep_risk_per_trade:,.2f}) completely bypasses the Instant account's lower sizing limit over extended targets.")
    else:
        st.success(f"🎯 **Verdict:** The **Instant** account is superior here. It side-steps the combined {total_eval_pct_required}% evaluation requirement entirely, letting you keep immediate profits.")
