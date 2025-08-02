import streamlit as st

# Currency conversion (placeholder if API isn't working)
usd_to_zar = 18.50  # fallback rate

st.set_page_config(page_title="Prop Firm Calculator by Stoic Capital", layout="centered")

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
        .main {
            background-color: #1E1E2F;
            color: white;
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3 {
            color: #FFB703;
        }
        .stButton>button {
            background-color: #219EBC;
            color: white;
            border-radius: 12px;
            padding: 10px 20px;
            font-size: 16px;
        }
        .stTextInput>div>div>input, .stNumberInput>div>div>input {
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
        }
        .result-box {
            background-color: #073B4C;
            padding: 20px;
            border-radius: 15px;
            margin-top: 30px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("📊 Prop Firm Calculator")
st.subheader("by Stoic Capital")
st.markdown("Calculate your payouts in USD and ZAR based on your account size and profit target.")

# --- Input Section ---
col1, col2 = st.columns(2)
with col1:
    account_size = st.number_input("💼 Account Size (USD)", min_value=0, step=1000)
with col2:
    profit_percent = st.number_input("🎯 Profit Target (%)", min_value=0.0, max_value=100.0, step=1.0)

profit_split = st.slider("🤝 Profit Split (%)", min_value=50, max_value=100, value=80)

# --- Calculation ---
total_profit = (account_size * profit_percent) / 100
trader_share = total_profit * (profit_split / 100)
zar_amount = trader_share * usd_to_zar

# --- Result Box ---
st.markdown(f"""
<div class="result-box">
    <h3>💰 Results</h3>
    <p>Total Profit (USD): <strong>${total_profit:,.2f}</strong></p>
    <p>Your Share ({profit_split}%): <strong>${trader_share:,.2f}</strong></p>
    <p>Estimated ZAR Payout: <strong>R{zar_amount:,.2f}</strong></p>
</div>
""", unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("🔄 Currency rate uses fallback of $1 = R18.50")
st.markdown("Built by Stoic Capital")
st.markdown("---")
st.markdown("### 📲 Connect with Stoic Capital")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        "[![Twitter](https://img.shields.io/badge/Twitter-%231DA1F2.svg?style=for-the-badge&logo=twitter&logoColor=white)](https://x.com/Stoiccapital)"
    )

with col2:
    st.markdown(
        "[![YouTube](https://img.shields.io/badge/YouTube-%23FF0000.svg?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@stoiccapital)"
    )
