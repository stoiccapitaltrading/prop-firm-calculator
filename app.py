import requests
import streamlit as st

st.set_page_config(page_title="Prop Firm Payout Calculator by Stoic Capital", layout="centered")

st.markdown(
    """
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}
.subtitle {
    color: #9ca3af;
    margin-bottom: 1rem;
}
.result-card {
    background: linear-gradient(135deg, #0b3b49 0%, #0f5f73 100%);
    padding: 1.1rem 1.2rem;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
.metric-label {
    color: #d1d5db;
    font-size: 0.9rem;
}
.metric-value {
    color: #ffffff;
    font-size: 1.15rem;
    font-weight: 700;
    margin-bottom: 0.45rem;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def get_exchange_rates():
    url = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get("result") != "success" or "rates" not in data:
        raise ValueError(f"Exchange rate API failed: {data}")

    return data["rates"]


try:
    rates = get_exchange_rates()
except Exception as e:
    st.error(f"Could not load live exchange rates. Error: {e}")
    rates = {
        "USD": 1.0,
        "ZAR": 18.50,
        "EUR": 0.92,
        "GBP": 0.78,
        "JPY": 150.00,
        "AUD": 1.55,
        "CAD": 1.35,
        "CHF": 0.90,
        "NZD": 1.65,
    }

st.markdown('<div class="main-title">📈 Prop Firm Profits Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">📈 Profit Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">by Stoic Capital</div>', unsafe_allow_html=True)
st.markdown("Calculate your payouts in USD and your selected currency using **live exchange rates**.")

col1, col2 = st.columns(2)
with col1:
    account_size = st.number_input("💼 Account Size (USD)", min_value=0, step=1000)
with col2:
    profit_percent = st.number_input("🎯 Profit Target (%)", min_value=0.0, max_value=100.0, step=1.0)

profit_split = st.slider("🤝 Profit Split (%)", min_value=50, max_value=100, value=80)

available_currencies = sorted(rates.keys())
selected_currency = st.selectbox(
    "🌍 Select Payout Currency",
    available_currencies,
    index=available_currencies.index("ZAR") if "ZAR" in available_currencies else 0,
)

exchange_rate = float(rates[selected_currency])
total_profit = (account_size * profit_percent) / 100
trader_share = total_profit * (profit_split / 100)
converted_amount = trader_share * exchange_rate

st.markdown(
    f"""
<div class="result-card">
    <div class="metric-label">Total Profit (USD)</div>
    <div class="metric-value">${total_profit:,.2f}</div>
    <div class="metric-label">Your Share ({profit_split}%)</div>
    <div class="metric-value">${trader_share:,.2f}</div>
    <div class="metric-label">Payout in {selected_currency} (Rate: {exchange_rate:.4f})</div>
    <div class="metric-value">{converted_amount:,.2f} {selected_currency}</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("---")
st.caption("🔄 Live exchange rates updated hourly • Fallback used if API fails")
st.caption("Built by Stoic Capital")
