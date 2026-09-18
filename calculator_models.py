"""Pure, testable calculation helpers used by the Streamlit pages."""

from math import sqrt
from random import Random
from typing import Sequence


def expected_trades_per_active_day(
    full_win_rate_pct: float,
    partial_win_rate_pct: float,
    second_trade_after_non_profit_rate: float = 1.0,
    second_trade_after_profit_rate: float = 0.0,
) -> float:
    """Estimate trades on an active day from the selected day-management rules.

    The first trade always occurs. A second trade is then taken with a
    user-specified probability based on whether the first trade was profitable.
    Rates for the second trade are decimal probabilities, not percentages.
    """
    positive_probability = (full_win_rate_pct + partial_win_rate_pct) / 100.0
    positive_probability = min(max(positive_probability, 0.0), 1.0)
    non_profit_probability = 1.0 - positive_probability
    after_non_profit = min(max(second_trade_after_non_profit_rate, 0.0), 1.0)
    after_profit = min(max(second_trade_after_profit_rate, 0.0), 1.0)
    return 1.0 + (non_profit_probability * after_non_profit) + (positive_probability * after_profit)


def estimate_setup_day_probability(
    avg_trades_per_month: float,
    full_win_rate_pct: float,
    partial_win_rate_pct: float,
    trading_days_per_month: int = 21,
    second_trade_after_non_profit_rate: float = 1.0,
    second_trade_after_profit_rate: float = 0.0,
) -> tuple[float, float]:
    """Return setup-day probability and expected active trading days per month.

    This keeps the simulated average trade count aligned with the selected
    value while allowing the day-management rules to match a journal.
    """
    expected_trade_count = expected_trades_per_active_day(
        full_win_rate_pct,
        partial_win_rate_pct,
        second_trade_after_non_profit_rate,
        second_trade_after_profit_rate,
    )
    if expected_trade_count <= 0 or trading_days_per_month <= 0:
        return 0.0, 0.0
    probability = min(
        max(avg_trades_per_month / (trading_days_per_month * expected_trade_count), 0.0),
        1.0,
    )
    return probability, probability * trading_days_per_month


def sample_dirichlet_probabilities(
    rng: Random,
    probabilities: Sequence[float],
    sample_size: int,
    prior_strength: float = 0.5,
) -> tuple[float, ...]:
    """Sample a categorical probability vector with journal-rate uncertainty.

    A symmetric Dirichlet prior keeps every outcome possible while allowing
    small journals to produce a wider range of plausible outcome mixes.
    """
    if not probabilities:
        raise ValueError("At least one outcome probability is required.")
    if sample_size <= 0:
        return tuple(probabilities)

    total = sum(probabilities)
    if total <= 0:
        raise ValueError("Outcome probabilities must sum to a positive value.")

    alphas = [max((probability / total) * sample_size + prior_strength, 0.000001) for probability in probabilities]
    draws = [rng.gammavariate(alpha, 1.0) for alpha in alphas]
    draw_total = sum(draws)
    return tuple(draw / draw_total for draw in draws)


def wilson_interval(successes: int, total: int, z_score: float = 1.96) -> tuple[float, float]:
    """Return a Wilson confidence interval for a simulated proportion."""
    if total <= 0:
        return 0.0, 0.0
    proportion = min(max(successes / total, 0.0), 1.0)
    denominator = 1.0 + (z_score**2 / total)
    center = (proportion + (z_score**2 / (2.0 * total))) / denominator
    margin = (
        z_score
        * sqrt((proportion * (1.0 - proportion) / total) + (z_score**2 / (4.0 * total**2)))
        / denominator
    )
    return max(center - margin, 0.0), min(center + margin, 1.0)


def percentile(values: Sequence[float], percentile_rank: float) -> float:
    """Return a linearly interpolated percentile without a NumPy dependency."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = min(max(percentile_rank, 0.0), 1.0) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * weight)


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


def r_required_for_percentage_target(
    account_size: float, target_pct: float, risk_per_trade: float
) -> float:
    """Convert an account-percentage target into R at the selected risk size."""
    if account_size <= 0:
        raise ValueError("Account size must be positive.")
    if risk_per_trade <= 0:
        raise ValueError("Risk per trade must be positive.")
    return (account_size * (target_pct / 100.0)) / risk_per_trade
