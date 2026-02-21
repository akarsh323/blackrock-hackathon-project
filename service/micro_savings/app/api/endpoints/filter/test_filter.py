import pytest
from service.micro_savings.app.api.endpoints.qpk.qpk_service import apply_qpk, sum_remanents_for_k_period
from service.micro_savings.app.api.endpoints.transaction.transaction import ValidatedTransaction
from service.micro_savings.app.api.endpoints.periods.periods import QPeriod, PPeriod, KPeriod


def make_tx(date, amount=300, ceiling=400, remanent=100):
    return ValidatedTransaction(date=date, amount=amount, ceiling=ceiling, remanent=remanent)


K_FULL_YEAR = KPeriod(start="2023-01-01 00:00:00", end="2023-12-31 23:59:59")


class TestQRule:
    def test_q_overrides_remanent(self):
        txns    = [make_tx("2023-07-15 12:00:00", remanent=50)]
        q       = [QPeriod(fixed=0, start="2023-07-01 00:00:00", end="2023-07-31 23:59:59")]
        valid, _ = apply_qpk(txns, q, [], [K_FULL_YEAR])
        assert valid[0].remanent == 0
        assert valid[0].appliedQ.fixed == 0

    def test_latest_q_wins_on_overlap(self):
        txns = [make_tx("2023-07-15 12:00:00", remanent=50)]
        q = [
            QPeriod(fixed=30, start="2023-01-01 00:00:00", end="2023-12-31 23:59:59"),
            QPeriod(fixed=10, start="2023-06-01 00:00:00", end="2023-08-31 23:59:59"),  # later start
        ]
        valid, _ = apply_qpk(txns, q, [], [K_FULL_YEAR])
        assert valid[0].remanent == 10   # Later start wins

    def test_no_q_match_leaves_remanent_unchanged(self):
        txns    = [make_tx("2023-07-15 12:00:00", remanent=50)]
        valid, _ = apply_qpk(txns, [], [], [K_FULL_YEAR])
        assert valid[0].remanent == 50


class TestPRule:
    def test_p_adds_extra_after_q(self):
        txns = [make_tx("2023-10-15 12:00:00", remanent=50)]
        p    = [PPeriod(extra=25, start="2023-10-01 00:00:00", end="2023-12-31 23:59:59")]
        valid, _ = apply_qpk(txns, [], p, [K_FULL_YEAR])
        assert valid[0].remanent == 75   # 50 + 25

    def test_multiple_p_periods_all_sum(self):
        txns = [make_tx("2023-10-15 12:00:00", remanent=50)]
        p = [
            PPeriod(extra=25, start="2023-10-01 00:00:00", end="2023-12-31 23:59:59"),
            PPeriod(extra=10, start="2023-09-01 00:00:00", end="2023-11-30 23:59:59"),
        ]
        valid, _ = apply_qpk(txns, [], p, [K_FULL_YEAR])
        assert valid[0].remanent == 85   # 50 + 25 + 10

    def test_p_applies_even_when_q_sets_zero(self):
        txns = [make_tx("2023-07-15 12:00:00", remanent=50)]
        q    = [QPeriod(fixed=0, start="2023-07-01 00:00:00", end="2023-07-31 23:59:59")]
        p    = [PPeriod(extra=20, start="2023-01-01 00:00:00", end="2023-12-31 23:59:59")]
        valid, _ = apply_qpk(txns, q, p, [K_FULL_YEAR])
        assert valid[0].remanent == 20   # 0 (from Q) + 20 (from P)


class TestKRule:
    def test_transaction_outside_k_goes_invalid(self):
        txns = [make_tx("2022-01-01 12:00:00")]   # 2022, not in 2023 K
        _, invalid = apply_qpk(txns, [], [], [K_FULL_YEAR])
        assert len(invalid) == 1
        assert "K period" in invalid[0].message

    def test_transaction_counted_in_multiple_k(self):
        txns = [make_tx("2023-07-15 12:00:00", remanent=50)]
        k = [
            KPeriod(start="2023-01-01 00:00:00", end="2023-12-31 23:59:59"),
            KPeriod(start="2023-06-01 00:00:00", end="2023-09-30 23:59:59"),
        ]
        valid, _ = apply_qpk(txns, [], [], k)
        total_k1 = sum_remanents_for_k_period(valid, k[0])
        total_k2 = sum_remanents_for_k_period(valid, k[1])
        assert total_k1 == 50   # counted in K1
        assert total_k2 == 50   # also counted in K2
