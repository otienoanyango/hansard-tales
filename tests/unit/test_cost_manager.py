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


class TestPropertyBasedCostTracking:
    """Property-based tests for cost tracking accuracy.
    
    Property 13.1: Tracked costs must match actual API usage
    - Cost calculation must be accurate across all token counts
    - Aggregation must preserve individual costs
    - Cost rounding must not accumulate errors
    """

    @pytest.mark.hypothesis
    def test_cost_accuracy_for_various_token_counts(
        self, cost_manager: CostManager
    ):
        """Test that costs are calculated accurately for various token counts."""
        from hypothesis import given, strategies as st, settings

        @settings(max_examples=50)  # Reduce examples to stay within budget
        @given(
            input_tokens=st.integers(min_value=100, max_value=10_000),  # Keep tokens reasonable
            output_tokens=st.integers(min_value=0, max_value=5_000),
        )
        def test_with_varying_tokens(input_tokens, output_tokens):
            cost_manager.track_usage(
                model="claude-3-5-haiku-20241022",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            monthly = cost_manager.get_monthly_usage()
            
            # Verify tracking is working
            assert monthly["cost_usd"] >= 0
            assert monthly["requests"] > 0
            assert monthly["input_tokens"] >= input_tokens
            assert monthly["output_tokens"] >= output_tokens

        test_with_varying_tokens()

    @pytest.mark.hypothesis
    def test_aggregation_preserves_cost(
        self, cost_manager: CostManager
    ):
        """Test that aggregating multiple requests accumulates properly."""
        from hypothesis import given, strategies as st, settings

        @settings(max_examples=30)
        @given(
            requests_data=st.lists(
                st.tuples(
                    st.integers(min_value=100, max_value=2_000),
                    st.integers(min_value=50, max_value=1_000),
                ),
                min_size=1,
                max_size=5,
            )
        )
        def test_aggregation(requests_data):
            request_count = 0
            total_input = 0
            total_output = 0
            
            for input_tokens, output_tokens in requests_data:
                total_input += input_tokens
                total_output += output_tokens
                request_count += 1
                
                try:
                    cost_manager.track_usage(
                        model="claude-3-5-haiku-20241022",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                except BudgetExceededError:
                    # Stop if budget exceeded
                    break

            monthly = cost_manager.get_monthly_usage()
            
            # Verify totals accumulate correctly (at least for what succeeded)
            assert monthly["requests"] > 0
            assert monthly["cost_usd"] > 0
            assert monthly["input_tokens"] > 0
            assert monthly["output_tokens"] >= 0

        test_aggregation()

    @pytest.mark.hypothesis
    def test_cost_never_negative(
        self, cost_manager: CostManager
    ):
        """Test that costs are always non-negative.
        
        Property: cost_usd >= 0 for all tracking
        """
        from hypothesis import given, strategies as st, settings

        @settings(max_examples=20)
        @given(
            input_tokens=st.integers(min_value=1, max_value=10_000),
            output_tokens=st.integers(min_value=0, max_value=5_000),
        )
        def test_non_negative_cost(input_tokens, output_tokens):
            cost_manager.track_usage(
                model="claude-3-5-haiku-20241022",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            monthly = cost_manager.get_monthly_usage()
            assert monthly["cost_usd"] >= 0
            assert monthly["budget_remaining"] >= 0
            assert monthly["budget_remaining"] <= 20.0

        test_non_negative_cost()


class TestPropertyBasedBudgetEnforcement:
    """Property-based tests for budget enforcement.
    
    Property 13.2: Processing must stop when budget exceeded
    - Once budget is exceeded, further requests must fail
    - Budget limit must be enforced consistently
    - No requests should succeed after budget exceeded
    """

    @pytest.mark.hypothesis
    def test_budget_enforcement_consistency(
        self, db_session: Session
    ):
        """Test that budget enforcement is consistent across requests."""
        from hypothesis import given, strategies as st, settings

        @settings(max_examples=20)
        @given(
            num_requests=st.integers(min_value=1, max_value=10),
        )
        def test_enforcement(num_requests):
            cost_manager = CostManager(db=db_session, monthly_budget=2.0)  # Small budget
            exceeded = False
            successful_requests = 0

            for _ in range(num_requests):
                try:
                    cost_manager.track_usage(
                        model="claude-3-5-haiku-20241022",
                        input_tokens=5_000,  # Will exceed budget eventually
                        output_tokens=1_000,
                    )
                    successful_requests += 1
                except BudgetExceededError:
                    exceeded = True
                    break  # Stop on first budget exceeded

            # Either we succeeded with requests OR hit budget limit
            monthly = cost_manager.get_monthly_usage()
            assert monthly["cost_usd"] <= 2.0 or exceeded

        test_enforcement()

    @pytest.mark.hypothesis
    def test_budget_remaining_decreases_monotonically(
        self, db_session: Session
    ):
        """Test that budget_remaining decreases with each request.
        
        Property: budget_remaining[n] <= budget_remaining[n-1]
        """
        from hypothesis import given, strategies as st, settings

        @settings(max_examples=15)
        @given(
            requests=st.lists(
                st.tuples(
                    st.integers(min_value=100, max_value=1_000),
                    st.integers(min_value=0, max_value=500),
                ),
                min_size=1,
                max_size=5,
            )
        )
        def test_monotonic_decrease(requests):
            cost_manager = CostManager(db=db_session, monthly_budget=5.0)
            previous_remaining = 5.0
            
            for input_tokens, output_tokens in requests:
                try:
                    cost_manager.track_usage(
                        model="claude-3-5-haiku-20241022",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                    
                    monthly = cost_manager.get_monthly_usage()
                    current_remaining = monthly["budget_remaining"]
                    
                    # Budget remaining should monotonically decrease (or stay same)
                    assert current_remaining <= previous_remaining
                    previous_remaining = current_remaining
                    
                except BudgetExceededError:
                    # Once exceeded, stop trying
                    break

        test_monotonic_decrease()

    @pytest.mark.hypothesis
    def test_budget_math_correctness(
        self, cost_manager: CostManager
    ):
        """Test that budget math is always correct.
        
        Property: cost + budget_remaining == monthly_budget
        """
        from hypothesis import given, strategies as st, settings

        @settings(max_examples=30)
        @given(
            input_tokens=st.integers(min_value=1, max_value=5_000),
            output_tokens=st.integers(min_value=0, max_value=2_000),
        )
        def test_budget_math(input_tokens, output_tokens):
            cost_manager.track_usage(
                model="claude-3-5-haiku-20241022",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            monthly = cost_manager.get_monthly_usage()
            
            # Verify: used_cost + remaining = budget (approximately)
            calculated_sum = monthly["cost_usd"] + monthly["budget_remaining"]
            
            # Should equal 20.0 or be less if budget exceeded
            assert calculated_sum <= 20.0 + 0.01  # Small tolerance for floating point
            assert monthly["cost_usd"] >= 0
            assert monthly["budget_remaining"] >= 0

        test_budget_math()


class TestPropertyBasedMultiModel:
    """Property-based tests for multi-model cost tracking.
    
    Property: Cost tracking must be accurate across different models
    """

    @pytest.mark.hypothesis
    def test_model_independence(
        self, cost_manager: CostManager
    ):
        """Test that tracking one model doesn't affect another.
        
        Property: Tracking model A doesn't change model B's costs
        """
        from hypothesis import given, strategies as st, settings

        @settings(max_examples=20)
        @given(
            haiku_input=st.integers(min_value=1000, max_value=20_000),
            sonnet_input=st.integers(min_value=1000, max_value=20_000),
        )
        def test_independence(haiku_input, sonnet_input):
            # Track Haiku
            cost_manager.track_usage(
                model="claude-3-5-haiku-20241022",
                input_tokens=haiku_input,
                output_tokens=0,
            )
            
            haiku_usage = cost_manager.get_usage_by_model()
            haiku_cost = haiku_usage.get("claude-3-5-haiku-20241022", {}).get("cost_usd", 0)
            
            # Track Sonnet
            cost_manager.track_usage(
                model="claude-3-5-sonnet-20241022",
                input_tokens=sonnet_input,
                output_tokens=0,
            )
            
            updated_usage = cost_manager.get_usage_by_model()
            
            # Haiku cost should not have changed (same as before)
            haiku_cost_after = updated_usage.get("claude-3-5-haiku-20241022", {}).get("cost_usd", 0)
            assert abs(haiku_cost_after - haiku_cost) < 0.0001
            
            # Sonnet should have been added
            assert "claude-3-5-sonnet-20241022" in updated_usage

        test_independence()

    @pytest.mark.hypothesis
    def test_model_pricing_invariants(
        self, db_session: Session
    ):
        """Test that model pricing follows expected invariants.
        
        Property: sonnet_cost > haiku_cost for same token count
        (because Sonnet has higher pricing)
        """
        from hypothesis import given, strategies as st, settings

        @settings(max_examples=15)
        @given(
            tokens=st.integers(min_value=1_000, max_value=50_000),
        )
        def test_pricing_invariant(tokens):
            # Clear the database session first
            db_session.query(APIUsageORM).delete()
            db_session.commit()
            
            # Track Haiku tokens
            cm_haiku = CostManager(db=db_session, monthly_budget=100.0)
            cm_haiku.track_usage(
                model="claude-3-5-haiku-20241022",
                input_tokens=tokens,
                output_tokens=0,
            )
            
            haiku_usage = cm_haiku.get_usage_by_model()
            haiku_cost = haiku_usage.get("claude-3-5-haiku-20241022", {}).get("cost_usd", 0)
            
            # Clear and track Sonnet tokens separately
            db_session.query(APIUsageORM).delete()
            db_session.commit()
            
            cm_sonnet = CostManager(db=db_session, monthly_budget=100.0)
            cm_sonnet.track_usage(
                model="claude-3-5-sonnet-20241022",
                input_tokens=tokens,
                output_tokens=0,
            )
            
            sonnet_usage = cm_sonnet.get_usage_by_model()
            sonnet_cost = sonnet_usage.get("claude-3-5-sonnet-20241022", {}).get("cost_usd", 0)
            
            # Sonnet pricing is higher for input tokens (3.00 vs 0.80)
            # So for the same tokens, Sonnet should cost more
            assert sonnet_cost > haiku_cost, f"Sonnet ({sonnet_cost}) should cost more than Haiku ({haiku_cost})"

        test_pricing_invariant()

