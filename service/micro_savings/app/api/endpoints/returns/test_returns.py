import pytest
from service.micro_savings.app.api.endpoints.returns.returns_service import (
    compute_future_value, adjust_for_inflation,
    compute_nps_returns, compute_index_returns,
    NPS_RATE, INDEX_RATE
)
from service.micro_savings.app.api.endpoints.transaction.transaction import FilteredTransaction
from service.micro_savings.app.api.endpoints.periods.periods import KPeriod


def make_tx(date, amount=300, ceiling=400, remanent=100):
    return FilteredTransaction(
        date=date, amount=amount, ceiling=ceiling,
        remanent=remanent, inKPeriod=True
    )


K = KPeriod(start="2023-01-01 00:00:00", end="2023-12-31 23:59:59")


class TestFutureValue:
    def test_zero_principal_returns_zero(self):
        assert compute_future_value(0, NPS_RATE, 10) == 0.0

    def test_zero_years_returns_zero(self):
        assert compute_future_value(1000, NPS_RATE, 0) == 0.0

    def test_compound_growth_nps(self):
        fv = compute_future_value(1000, NPS_RATE, 10)
        assert fv > 1000                    # Must grow
        assert abs(fv - 1989.15) < 1.0     # ~₹1989 at 7.11% for 10 years

    def test_index_grows_faster_than_nps(self):
        nps_fv   = compute_future_value(1000, NPS_RATE, 20)
        index_fv = compute_future_value(1000, INDEX_RATE, 20)
        assert index_fv > nps_fv


class TestInflationAdjustment:
    def test_inflation_reduces_value(self):
        real = adjust_for_inflation(1000, 5.5, 10)
        assert real < 1000

    def test_zero_inflation_unchanged(self):
        real = adjust_for_inflation(1000, 0, 10)
        assert real == 1000.0


class TestNPSReturns:
    def test_response_has_savings_by_dates(self):
        txns   = [make_tx("2023-06-15 12:00:00", remanent=200)]
        result = compute_nps_returns(txns, [K], age=29, wage=50000, inflation=5.5)
        assert len(result.savingsByDates) == 1
        assert result.savingsByDates[0].amount == 200

    def test_profit_is_positive(self):
        txns   = [make_tx("2023-06-15 12:00:00", remanent=500)]
        result = compute_nps_returns(txns, [K], age=29, wage=50000, inflation=5.5)
        assert result.savingsByDates[0].profit > 0

    def test_nps_has_tax_benefit_field(self):
        txns   = [make_tx("2023-06-15 12:00:00", remanent=500)]
        result = compute_nps_returns(txns, [K], age=29, wage=50000, inflation=5.5)
        assert result.savingsByDates[0].taxBenefit >= 0


class TestIndexReturns:
    def test_index_tax_benefit_always_zero(self):
        txns   = [make_tx("2023-06-15 12:00:00", remanent=500)]
        result = compute_index_returns(txns, [K], age=29, wage=50000, inflation=5.5)
        assert result.savingsByDates[0].taxBenefit == 0.0

    def test_index_profit_higher_than_nps(self):
        txns  = [make_tx("2023-06-15 12:00:00", remanent=1000)]
        nps   = compute_nps_returns(txns, [K], age=29, wage=50000, inflation=5.5)
        index = compute_index_returns(txns, [K], age=29, wage=50000, inflation=5.5)
        assert index.savingsByDates[0].profit > nps.savingsByDates[0].profit
