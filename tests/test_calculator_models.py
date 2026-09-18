from calculator_models import (
    estimate_setup_day_probability,
    net_profit,
    return_on_cost,
    settle_profit_payout,
)


def test_setup_probability_matches_selected_monthly_trade_count():
    probability, active_days = estimate_setup_day_probability(22, 50, 0)
    expected_trades_per_active_day = 1.5
    assert round(probability * 21 * expected_trades_per_active_day, 8) == 22
    assert active_days > 0


def test_payout_does_not_leave_firm_share_to_be_paid_again():
    payout, new_balance = settle_profit_payout(101_000, 100_000, 80)
    assert payout == 800
    assert new_balance == 100_000


def test_roi_uses_net_profit_after_cost():
    profit = net_profit(cash_received=1_035, purchase_cost=35)
    assert profit == 1_000
    assert return_on_cost(profit, 35) == (1_000 / 35) * 100
