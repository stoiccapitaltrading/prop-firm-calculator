from calculator_models import (
    estimate_setup_day_probability,
    expected_trades_per_active_day,
    net_profit,
    percentile,
    r_required_for_percentage_target,
    return_on_cost,
    sample_dirichlet_probabilities,
    settle_profit_payout,
    wilson_interval,
)
from random import Random


def test_setup_probability_matches_selected_monthly_trade_count():
    probability, active_days = estimate_setup_day_probability(22, 50, 0)
    expected_trades_per_active_day = 1.5
    assert round(probability * 21 * expected_trades_per_active_day, 8) == 22
    assert active_days > 0


def test_historical_second_trade_pattern_matches_journal_frequency():
    expected_count = expected_trades_per_active_day(35.1, 15.9, 0.333, 0.077)
    assert round(expected_count, 4) == 1.2024

    probability, _ = estimate_setup_day_probability(22, 35.1, 15.9, 21, 0.333, 0.077)
    assert round(probability * 21 * expected_count, 8) == 22


def test_dirichlet_sample_is_a_valid_probability_vector():
    probabilities = sample_dirichlet_probabilities(Random(42), (0.351, 0.159, 0.146, 0.344), 151)
    assert len(probabilities) == 4
    assert all(value > 0 for value in probabilities)
    assert round(sum(probabilities), 12) == 1


def test_wilson_interval_contains_observed_rate():
    lower, upper = wilson_interval(1, 2000)
    assert lower <= 1 / 2000 <= upper
    assert lower < upper


def test_percentile_interpolates_between_values():
    assert percentile([1, 2, 3, 4], 0.5) == 2.5


def test_payout_does_not_leave_firm_share_to_be_paid_again():
    payout, new_balance = settle_profit_payout(101_000, 100_000, 80)
    assert payout == 800
    assert new_balance == 100_000


def test_roi_uses_net_profit_after_cost():
    profit = net_profit(cash_received=1_035, purchase_cost=35)
    assert profit == 1_000
    assert return_on_cost(profit, 35) == (1_000 / 35) * 100


def test_percentage_phase_targets_convert_to_r_at_evaluation_risk():
    assert r_required_for_percentage_target(50_000, 8, 1_000) == 4
    assert r_required_for_percentage_target(50_000, 5, 1_000) == 2.5
