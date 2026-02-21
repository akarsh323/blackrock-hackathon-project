from service.micro_savings.app.transaction_engine.tax_processor.tax_service import (
    compute_tax,
    compute_nps_tax_benefit,
)


class TestComputeTax:
    def test_below_7L_no_tax(self):
        assert compute_tax(600_000) == 0.0
        assert compute_tax(700_000) == 0.0

    def test_at_8L_10_percent_on_1L(self):
        # ₹8L income → 10% on ₹1L above ₹7L = ₹10,000
        assert compute_tax(800_000) == 10_000.0

    def test_at_11L(self):
        # 10% on 3L (7-10L) + 15% on 1L (10-11L) = 30000 + 15000 = 45000
        assert compute_tax(1_100_000) == 45_000.0

    def test_at_13L(self):
        # 10% on 3L = 30000
        # 15% on 2L = 30000
        # 20% on 1L = 20000
        # Total = 80000
        assert compute_tax(1_300_000) == 80_000.0

    def test_above_15L_max_slab(self):
        # Should use 30% slab for anything above 15L
        tax_15L = compute_tax(1_500_000)
        tax_16L = compute_tax(1_600_000)
        diff = tax_16L - tax_15L
        assert abs(diff - 30_000.0) < 0.01  # 30% of 1L = 30,000

    def test_zero_income_no_tax(self):
        assert compute_tax(0) == 0.0


class TestNPSTaxBenefit:
    def test_below_tax_slab_no_benefit(self):
        # Annual wage = 50000*12 = 6L → below 7L slab → no tax either way
        benefit = compute_nps_tax_benefit(total_invested=10_000, monthly_wage=50_000)
        assert benefit == 0.0

    def test_above_tax_slab_gets_benefit(self):
        # Annual wage = 100000*12 = 12L → in 20% slab
        benefit = compute_nps_tax_benefit(total_invested=50_000, monthly_wage=100_000)
        assert benefit > 0

    def test_benefit_never_negative(self):
        benefit = compute_nps_tax_benefit(total_invested=0, monthly_wage=50_000)
        assert benefit >= 0

    def test_deduction_capped_at_200k(self):
        # Even if we invest 10L, deduction max is 2L
        benefit_small = compute_nps_tax_benefit(200_000, monthly_wage=200_000)
        benefit_large = compute_nps_tax_benefit(1_000_000, monthly_wage=200_000)
        assert benefit_small == benefit_large  # Both capped at 2L deduction
