# Prop Firm Calculator

A Streamlit decision-support app for prop-firm traders.

## Tools

- **Payout Calculator** — converts a projected USD payout into a selected currency using hourly exchange rates.
- **Risk of Ruin Calculator** — Monte Carlo models for CFD and futures evaluations, including pass probability, drawdown failure and optional funded-account continuation.
- **Strategy & ROI Comparison** — compares two-step and instant accounts using the same net-profit-after-cost basis.

## Important modelling assumptions

This is an educational calculator, not financial advice. Prop-firm rules differ materially. Before relying on any result, set the values to the rules of the particular firm and verify:

- Drawdown type: static, end-of-day trailing, or intraday trailing.
- Whether drawdown is percentage-based or fixed-dollar.
- Minimum *trading* days and consistency rules.
- Payout split, payout interval, profit buffer and post-payout balance treatment.

For the funded-continuation model, profit is settled at each payout event and the simulated balance resets to its starting level. This avoids treating the firm's share of a previous profit split as new trader profit in a later payout.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest
```
