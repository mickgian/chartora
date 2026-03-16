"""Unit tests for the GovernmentContract domain entity."""

from datetime import date
from decimal import Decimal

import pytest

from src.domain.models.entities import GovernmentContract


class TestGovernmentContract:
    def test_valid_contract(self):
        contract = GovernmentContract(
            company_id=1,
            award_id="AWD-001",
            title="Quantum Research Grant",
            amount=Decimal("1500000.00"),
            awarding_agency="Department of Defense",
            start_date=date(2025, 1, 15),
            end_date=date(2026, 1, 15),
            description="Research into quantum computing",
        )
        assert contract.award_id == "AWD-001"
        assert contract.amount == Decimal("1500000.00")
        assert contract.awarding_agency == "Department of Defense"

    def test_contract_without_end_date(self):
        contract = GovernmentContract(
            company_id=1,
            award_id="AWD-002",
            title="Ongoing Contract",
            amount=Decimal("500000"),
            awarding_agency="DOE",
            start_date=date(2025, 6, 1),
        )
        assert contract.end_date is None

    def test_empty_award_id_raises(self):
        with pytest.raises(ValueError, match="Award ID cannot be empty"):
            GovernmentContract(
                company_id=1,
                award_id="",
                title="Test",
                amount=Decimal("100"),
                awarding_agency="DOD",
                start_date=date(2025, 1, 1),
            )

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="Contract amount cannot be negative"):
            GovernmentContract(
                company_id=1,
                award_id="AWD-001",
                title="Test",
                amount=Decimal("-100"),
                awarding_agency="DOD",
                start_date=date(2025, 1, 1),
            )

    def test_zero_amount_is_valid(self):
        contract = GovernmentContract(
            company_id=1,
            award_id="AWD-003",
            title="Zero Value Contract",
            amount=Decimal("0"),
            awarding_agency="DOD",
            start_date=date(2025, 1, 1),
        )
        assert contract.amount == Decimal("0")
