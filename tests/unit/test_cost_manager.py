"""
Tests for CostManager.

Tests usage tracking, cost calculation, budget enforcement,
and reporting functionality.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from hansard_tales.analysis.cost_manager import (
    APIUsage,
    BudgetExceededError,
    CostManager,
)
from hansard_tales.database.models import Base, APIUsageORM


@pytest.fixture
def db_session() -> Session:
    """Create an in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def cost_manager(db_session: Session) -> CostManager:
    """Create a CostManager instance with $20 budget."""
    return CostManager(db=db_session, monthly_budget=20.0)


class TestCostManagerBasics:
    """Test basic CostManager functionality."""

    def test_initialization(self, cost_manager: CostManager):
        """Test CostManager initialization."""
        assert cost_manager.monthly_budget == 20.0
        assert cost_manager.default_model == "claude-3-5-haiku-20241022"

    def test_pricing_constants(self, cost_manager: CostManager):
        """Test pricing constants are properly defined."""
        haiku_pricing = cost_manager.CLAUDE_PRICING["claude-3-5-haiku-20241022"]
        assert haiku_pricing["input"] == 0.80
        assert haiku_pricing["output"] == 4.00


class TestUsageTracking:
    """Test API usage tracking functionality."""

    def test_track_single_usage(self, cost_manager: CostManager, db_session: Session):
        """Test tracking a single API call."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )

        # Cost calculation: (1000/1M * 0.80) + (500/1M * 4.00) = 0.0008 + 0.002 = 0.0028
        monthly = cost_manager.get_monthly_usage()
        assert monthly["input_tokens"] == 1000
        assert monthly["output_tokens"] == 500
        assert monthly["requests"] == 1
        assert abs(monthly["cost_usd"] - 0.0028) < 0.0001

    def test_track_multiple_uses(self, cost_manager: CostManager):
        """Test tracking multiple API calls."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=2000,
            output_tokens=1000,
        )

        monthly = cost_manager.get_monthly_usage()
        assert monthly["input_tokens"] == 3000
        assert monthly["output_tokens"] == 1500
        assert monthly["requests"] == 2

    def test_track_different_models(self, cost_manager: CostManager):
        """Test tracking usage for different models."""
        # Haiku usage
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )

        # Sonnet usage
        cost_manager.track_usage(
            model="claude-3-5-sonnet-20241022",
            input_tokens=1000,
            output_tokens=500,
        )

        monthly = cost_manager.get_monthly_usage()
        assert monthly["requests"] == 2

        by_model = cost_manager.get_usage_by_model()
        assert "claude-3-5-haiku-20241022" in by_model
        assert "claude-3-5-sonnet-20241022" in by_model


class TestBudgetEnforcement:
    """Test budget enforcement functionality."""

    def test_budget_exceeded_error(self, db_session: Session):
        """Test that budget exceeded error is raised."""
        cost_manager = CostManager(db=db_session, monthly_budget=0.01)

        with pytest.raises(BudgetExceededError):
            # This will cost ~$0.002, but we'll try to add $0.01+ worth
            cost_manager.track_usage(
                model="claude-3-5-haiku-20241022",
                input_tokens=10_000_000,  # 10M tokens = $8
                output_tokens=1_000_000,  # 1M tokens = $4
            )

    def test_budget_remaining_calculation(self, cost_manager: CostManager):
        """Test budget remaining calculation."""
        initial = cost_manager.get_monthly_usage()
        assert initial["budget_remaining"] == 20.0
        assert initial["usage_percent"] == 0.0

        # Use ~$0.50 with small tokens
        for _ in range(10):
            cost_manager.track_usage(
                model="claude-3-5-haiku-20241022",
                input_tokens=62_500,  # 0.0625M * $0.80 = $0.05
                output_tokens=0,
            )

        updated = cost_manager.get_monthly_usage()
        assert abs(updated["cost_usd"] - 0.5) < 0.01
        assert abs(updated["budget_remaining"] - 19.5) < 0.01

    def test_budget_warning_threshold(self, db_session: Session):
        """Test that warnings are logged near budget limit."""
        cost_manager = CostManager(db=db_session, monthly_budget=0.1)

        # Use most of budget
        for _ in range(50):
            cost_manager.track_usage(
                model="claude-3-5-haiku-20241022",
                input_tokens=1000,
                output_tokens=1,
            )

        usage = cost_manager.get_monthly_usage()
        assert usage["budget_remaining"] < 0.1


class TestDailyUsage:
    """Test daily usage tracking."""

    def test_get_daily_usage_today(self, cost_manager: CostManager):
        """Test getting usage for today."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )

        today_usage = cost_manager.get_daily_usage(date.today())
        assert today_usage is not None
        assert today_usage["date"] == date.today()
        assert today_usage["input_tokens"] == 1000
        assert today_usage["requests"] == 1

    def test_get_daily_usage_no_data(self, cost_manager: CostManager):
        """Test getting usage for a day with no data."""
        yesterday = date.today() - timedelta(days=1)
        usage = cost_manager.get_daily_usage(yesterday)
        assert usage is None

    def test_get_daily_usage_aggregates(self, cost_manager: CostManager):
        """Test that daily usage aggregates multiple requests."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=500,
            output_tokens=100,
        )
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=500,
            output_tokens=100,
        )

        today_usage = cost_manager.get_daily_usage(date.today())
        assert today_usage["input_tokens"] == 1000
        assert today_usage["requests"] == 2


class TestUsageByModel:
    """Test usage breakdown by model."""

    def test_usage_by_model_single(self, cost_manager: CostManager):
        """Test usage breakdown for single model."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )

        by_model = cost_manager.get_usage_by_model()
        assert len(by_model) == 1
        assert "claude-3-5-haiku-20241022" in by_model
        assert by_model["claude-3-5-haiku-20241022"]["requests"] == 1

    def test_usage_by_model_multiple(self, cost_manager: CostManager):
        """Test usage breakdown for multiple models."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_manager.track_usage(
            model="claude-3-5-sonnet-20241022",
            input_tokens=2000,
            output_tokens=1000,
        )

        by_model = cost_manager.get_usage_by_model()
        assert len(by_model) == 2

        haiku_usage = by_model["claude-3-5-haiku-20241022"]
        sonnet_usage = by_model["claude-3-5-sonnet-20241022"]

        # Sonnet should have more cost (higher pricing)
        assert sonnet_usage["cost_usd"] > haiku_usage["cost_usd"]

    def test_usage_by_model_date_range(self, cost_manager: CostManager):
        """Test usage by model with date range."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Add usage for "yesterday" manually
        usage_yesterday = APIUsageORM(
            date=yesterday,
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.001,
            requests=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        cost_manager.db.add(usage_yesterday)
        cost_manager.db.commit()

        # Add today's usage
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=2000,
            output_tokens=1000,
        )

        # Query for all time
        all_time = cost_manager.get_usage_by_model(
            start_date=yesterday,
            end_date=today,
        )
        assert all_time["claude-3-5-haiku-20241022"]["input_tokens"] == 3000


class TestReporting:
    """Test usage reporting."""

    def test_generate_report(self, cost_manager: CostManager):
        """Test report generation."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )

        report = cost_manager.generate_report()
        assert "API Usage Report" in report
        assert "Monthly Summary" in report
        assert "Usage by Model" in report
        assert "$" in report  # Should contain currency


class TestDatabasePersistence:
    """Test that usage data is persisted to database."""

    def test_usage_persists_to_database(
        self, cost_manager: CostManager, db_session: Session
    ):
        """Test that usage is saved to database."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )

        # Query database directly
        records = db_session.query(APIUsageORM).all()
        assert len(records) == 1
        assert records[0].model == "claude-3-5-haiku-20241022"
        assert records[0].input_tokens == 1000

    def test_usage_updates_existing_record(
        self, cost_manager: CostManager, db_session: Session
    ):
        """Test that same-day usage updates existing record."""
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_manager.track_usage(
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
        )

        # Should have only 1 record (updated, not created twice)
        records = db_session.query(APIUsageORM).all()
        assert len(records) == 1
        assert records[0].requests == 2
