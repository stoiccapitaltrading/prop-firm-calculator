import streamlit as st
import requests

st.set_page_config(page_title="Prop Firm Calculator by Stoic Capital", layout="centered")

@st.cache_data(ttl=3600)
def get_exchange_rates():
    url = "https://open.er-api.com/v6/latest/USD"  # no key required
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

st.caption(f"✅ Currencies loaded: {len(rates)}")

st.title("📊 Prop Firm Calculator")
st.subheader("by Stoic Capital")
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
    index=available_currencies.index("ZAR") if "ZAR" in available_currencies else 0
)

exchange_rate = float(rates[selected_currency])

total_profit = (account_size * profit_percent) / 100
trader_share = total_profit * (profit_split / 100)
converted_amount = trader_share * exchange_rate

st.markdown(
    f"""
<div style="background-color:#073B4C;padding:20px;border-radius:15px;margin-top:30px">
    <h3>💰 Results</h3>
    <p>Total Profit (USD): <strong>${total_profit:,.2f}</strong></p>
    <p>Your Share ({profit_split}%): <strong>${trader_share:,.2f}</strong></p>
    <p>Payout in {selected_currency} (Rate: {exchange_rate:.4f}):
       <strong>{converted_amount:,.2f} {selected_currency}</strong></p>
</div>
""",
    unsafe_allow_html=True
)

st.markdown("---")
st.caption("🔄 Live exchange rates updated hourly • Fallback used if API fails")
st.caption("Built by Stoic Capital")

