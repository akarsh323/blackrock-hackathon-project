from service.micro_savings.app.models.transaction import ParsedTransaction
from service.micro_savings.app.transaction_engine.validation_processor.validation_service import (
    validate_transactions,
)


def make_tx(date, amount, ceiling=None, remanent=None):
    import math

    c = ceiling if ceiling is not None else math.ceil(abs(amount) / 100) * 100
    r = remanent if remanent is not None else c - amount
    return ParsedTransaction(date=date, amount=amount, ceiling=c, remanent=r)


class TestNegativeAmount:
    def test_negative_goes_to_invalid(self):
        txns = [make_tx("2023-01-01 10:00:00", -250, ceiling=0, remanent=0)]
        valid, invalid = validate_transactions(txns, wage=50000)
        assert len(valid) == 0
        assert len(invalid) == 1
        assert "negative" in invalid[0].message.lower()


class TestDuplicateTimestamp:
    def test_duplicate_date_flags_both(self):
        txns = [
            make_tx("2023-01-01 10:00:00", 250),
            make_tx("2023-01-01 10:00:00", 800),
        ]
        valid, invalid = validate_transactions(txns, wage=50000)
        assert len(valid) == 0
        assert len(invalid) == 2

    def test_unique_dates_pass(self):
        txns = [
            make_tx("2023-01-01 10:00:00", 250),
            make_tx("2023-01-02 10:00:00", 250),
        ]
        valid, invalid = validate_transactions(txns, wage=50000)
        assert len(valid) == 2
        assert len(invalid) == 0


class TestAmountLimit:
    def test_exactly_500k_is_invalid(self):
        txns = [make_tx("2023-06-01 12:00:00", 500_000, ceiling=500_000, remanent=0)]
        valid, invalid = validate_transactions(txns, wage=50000)
        assert len(invalid) == 1

    def test_just_below_limit_is_valid(self):
        txns = [make_tx("2023-06-01 12:00:00", 499_999)]
        valid, invalid = validate_transactions(txns, wage=50000)
        assert len(valid) == 1


class TestCeilingMismatch:
    def test_wrong_ceiling_is_invalid(self):
        txns = [
            ParsedTransaction(
                date="2023-01-01 00:00:00", amount=250, ceiling=400, remanent=150
            )
        ]
        valid, invalid = validate_transactions(txns, wage=50000)
        assert len(invalid) == 1
        assert "ceiling" in invalid[0].message.lower()
