"""Pure, testable calculation helpers used by the Streamlit pages."""


def estimate_setup_day_probability(
    avg_trades_per_month: float,
    full_win_rate_pct: float,
    partial_win_rate_pct: float,
    trading_days_per_month: int = 21,
) -> tuple[float, float]:
    """Return setup-day probability and expected active trading days per month.

    A full or partial win ends the day; a breakeven or loss permits one
    additional trade. This keeps the simulated average trade count aligned
    with the value selected by the user.
    """
    win_probability = (full_win_rate_pct + partial_win_rate_pct) / 100.0
    expected_trades_per_active_day = 2.0 - win_probability
    if expected_trades_per_active_day <= 0 or trading_days_per_month <= 0:
        return 0.0, 0.0
    probability = min(
        max(avg_trades_per_month / (trading_days_per_month * expected_trades_per_active_day), 0.0),
        1.0,
    )
    return probability, probability * trading_days_per_month


def settle_profit_payout(
    balance: float, starting_balance: float, payout_split_pct: float
) -> tuple[float, float]:
    """Pay the trader's share of profit and reset the simulated account balance.

    The gross profit is treated as withdrawn or removed by the firm at the
    payout event. Leaving the firm's share in the account would allow it to
    be paid to the trader again on a later payout cycle.
    """
    gross_profit = balance - starting_balance
    if gross_profit <= 0:
        return 0.0, balance
    payout = gross_profit * (payout_split_pct / 100.0)
    return payout, starting_balance


def net_profit(cash_received: float, purchase_cost: float) -> float:
    """Return profit after the account purchase or evaluation cost."""
    return cash_received - purchase_cost


def return_on_cost(net_cash_profit: float, purchase_cost: float) -> float:
    """Return ROI percentage, safely handling a missing purchase cost."""
    return (net_cash_profit / purchase_cost) * 100.0 if purchase_cost > 0 else 0.0
