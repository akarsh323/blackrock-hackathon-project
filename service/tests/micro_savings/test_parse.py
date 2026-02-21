from service.micro_savings.app.models.transaction import (
    RawTransaction,
)
from service.micro_savings.app.transaction_engine.ceiling_processor.ceiling_service import (
    compute_ceiling,
    compute_remanent,
    parse_all,
)


class TestComputeCeiling:
    def test_rounds_up_normally(self):
        assert compute_ceiling(250) == 300

    def test_exact_multiple_unchanged(self):
        assert compute_ceiling(300) == 300

    def test_large_amount(self):
        assert compute_ceiling(847) == 900

    def test_just_above_multiple(self):
        assert compute_ceiling(101) == 200

    def test_just_below_multiple(self):
        assert compute_ceiling(199) == 200


class TestComputeRemanent:
    def test_normal_remanent(self):
        assert compute_remanent(250, 300) == 50

    def test_zero_remanent_on_exact(self):
        assert compute_remanent(300, 300) == 0

    def test_large_remanent(self):
        assert compute_remanent(101, 200) == 99


class TestParseAll:
    def test_parse_single_transaction(self):
        txns = [RawTransaction(date="2023-10-12 20:15:30", amount=250)]
        result = parse_all(txns)
        assert len(result) == 1
        assert result[0].ceiling == 300
        assert result[0].remanent == 50

    def test_parse_multiple_transactions(self):
        txns = [
            RawTransaction(date="2023-01-01 00:00:00", amount=100),
            RawTransaction(date="2023-01-02 00:00:00", amount=847),
        ]
        result = parse_all(txns)
        assert result[0].remanent == 100  # 200 - 100
        assert result[1].remanent == 53  # 900 - 847

    def test_preserves_order(self):
        txns = [
            RawTransaction(date="2023-03-01 00:00:00", amount=500),
            RawTransaction(date="2023-01-01 00:00:00", amount=200),
        ]
        result = parse_all(txns)
        assert result[0].date == "2023-03-01 00:00:00"
        assert result[1].date == "2023-01-01 00:00:00"
