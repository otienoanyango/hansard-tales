"""
Cost management and API usage tracking for Hansard Tales.

This module monitors and controls LLM API costs with budget enforcement,
caching, and Prometheus metrics integration.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from prometheus_client import Counter, Gauge
from sqlalchemy import func
from sqlalchemy.orm import Session

from hansard_tales.database.models import APIUsageORM

logger = logging.getLogger(__name__)


# Prometheus metrics for API usage
api_tokens_total = Counter(
    "api_tokens_total",
    "Total API tokens used",
    ["model", "token_type"],  # token_type: input or output
)

api_cost_total = Counter(
    "api_cost_usd_total",
    "Total API cost in USD",
    ["model"],
)

api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["model"],
)

budget_remaining_gauge = Gauge(
    "api_budget_remaining_usd",
    "Remaining API budget in USD",
)


@dataclass
class APIUsage:
    """Track API usage for a specific model."""

    date: date
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    requests: int


class BudgetExceededError(Exception):
    """Raised when API budget is exceeded."""

    pass


class CostManager:
    """
    Manage and monitor API costs.

    Tracks API usage, enforces budget constraints, and provides cost reporting.
    Supports Claude models with tiered pricing.
    """

    # Claude 3.5 Haiku pricing (per 1M tokens)
    CLAUDE_PRICING = {
        "claude-3-5-haiku-20241022": {
            "input": 0.80,  # $0.80 per 1M input tokens
            "output": 4.00,  # $4.00 per 1M output tokens
        },
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,  # $3.00 per 1M input tokens
            "output": 15.00,  # $15.00 per 1M output tokens
        },
        "claude-3-opus-20250219": {
            "input": 15.00,  # $15.00 per 1M input tokens
            "output": 75.00,  # $75.00 per 1M output tokens
        },
    }

    def __init__(
        self,
        db: Session,
        monthly_budget: float = 20.0,
        default_model: str = "claude-3-5-haiku-20241022",
    ):
        """
        Initialize CostManager.

        Args:
            db: SQLAlchemy session
            monthly_budget: Monthly budget in USD (default: $20)
            default_model: Default Claude model to use
        """
        self.db = db
        self.monthly_budget = monthly_budget
        self.default_model = default_model

    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Track API usage and update metrics.

        Args:
            model: Model name (e.g., "claude-3-5-haiku-20241022")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Raises:
            BudgetExceededError: If monthly budget would be exceeded
        """
        # Calculate cost
        pricing = self.CLAUDE_PRICING.get(model, self.CLAUDE_PRICING[self.default_model])
        cost_usd = (
            (input_tokens / 1_000_000) * pricing["input"]
            + (output_tokens / 1_000_000) * pricing["output"]
        )

        # Check budget before recording
        monthly_usage = self.get_monthly_usage()
        if monthly_usage["cost_usd"] + cost_usd > self.monthly_budget:
            logger.warning(
                f"Budget exceeded! Current: ${monthly_usage['cost_usd']:.2f}, "
                f"This request: ${cost_usd:.2f}, Budget: ${self.monthly_budget:.2f}"
            )
            raise BudgetExceededError(
                f"Monthly budget of ${self.monthly_budget:.2f} would be exceeded. "
                f"Current: ${monthly_usage['cost_usd']:.2f}, This request: ${cost_usd:.2f}"
            )

        # Check if we have a usage record for today
        today = date.today()
        existing = (
            self.db.query(APIUsageORM)
            .filter(APIUsageORM.date == today, APIUsageORM.model == model)
            .first()
        )

        if existing:
            # Update existing record
            existing.input_tokens += input_tokens
            existing.output_tokens += output_tokens
            existing.cost_usd += cost_usd
            existing.requests += 1
            existing.updated_at = datetime.now()
        else:
            # Create new record
            usage = APIUsageORM(
                date=today,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                requests=1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.db.add(usage)

        self.db.commit()

        # Update Prometheus metrics
        api_tokens_total.labels(model=model, token_type="input").inc(input_tokens)
        api_tokens_total.labels(model=model, token_type="output").inc(output_tokens)
        api_cost_total.labels(model=model).inc(cost_usd)
        api_requests_total.labels(model=model).inc()

        # Update budget gauge
        updated_usage = self.get_monthly_usage()
        budget_remaining_gauge.set(
            self.monthly_budget - updated_usage["cost_usd"]
        )

        logger.info(
            f"API usage tracked: model={model}, "
            f"input_tokens={input_tokens}, output_tokens={output_tokens}, "
            f"cost=${cost_usd:.4f}"
        )

    def get_monthly_usage(self) -> dict:
        """
        Get current month usage statistics.

        Returns:
            Dictionary with keys:
            - cost_usd: Total cost for current month
            - input_tokens: Total input tokens
            - output_tokens: Total output tokens
            - requests: Total number of requests
            - budget_remaining: Remaining budget
            - usage_percent: Percentage of budget used
        """
        # Get first day of current month
        today = date.today()
        first_day = today.replace(day=1)

        result = self.db.query(
            func.sum(APIUsageORM.cost_usd).label("cost"),
            func.sum(APIUsageORM.input_tokens).label("input_tokens"),
            func.sum(APIUsageORM.output_tokens).label("output_tokens"),
            func.sum(APIUsageORM.requests).label("requests"),
        ).filter(APIUsageORM.date >= first_day)

        row = result.first()

        cost = row.cost or 0.0
        input_tokens = row.input_tokens or 0
        output_tokens = row.output_tokens or 0
        requests = row.requests or 0

        return {
            "cost_usd": cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "requests": requests,
            "budget_remaining": self.monthly_budget - cost,
            "usage_percent": (cost / self.monthly_budget * 100) if self.monthly_budget > 0 else 0,
        }

    def get_daily_usage(self, target_date: Optional[date] = None) -> Optional[dict]:
        """
        Get usage for a specific day.

        Args:
            target_date: Date to get usage for (default: today)

        Returns:
            Dictionary with usage statistics or None if no usage for that day
        """
        if target_date is None:
            target_date = date.today()

        result = self.db.query(
            func.sum(APIUsageORM.cost_usd).label("cost"),
            func.sum(APIUsageORM.input_tokens).label("input_tokens"),
            func.sum(APIUsageORM.output_tokens).label("output_tokens"),
            func.sum(APIUsageORM.requests).label("requests"),
        ).filter(APIUsageORM.date == target_date)

        row = result.first()

        if not row.cost:
            return None

        return {
            "date": target_date,
            "cost_usd": row.cost or 0.0,
            "input_tokens": row.input_tokens or 0,
            "output_tokens": row.output_tokens or 0,
            "requests": row.requests or 0,
        }

    def get_usage_by_model(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> dict:
        """
        Get usage broken down by model.

        Args:
            start_date: Start date for range (default: first day of month)
            end_date: End date for range (default: today)

        Returns:
            Dictionary mapping model names to usage statistics
        """
        if start_date is None:
            today = date.today()
            start_date = today.replace(day=1)

        if end_date is None:
            end_date = date.today()

        results = (
            self.db.query(
                APIUsageORM.model,
                func.sum(APIUsageORM.cost_usd).label("cost"),
                func.sum(APIUsageORM.input_tokens).label("input_tokens"),
                func.sum(APIUsageORM.output_tokens).label("output_tokens"),
                func.sum(APIUsageORM.requests).label("requests"),
            )
            .filter(APIUsageORM.date >= start_date, APIUsageORM.date <= end_date)
            .group_by(APIUsageORM.model)
            .all()
        )

        usage_by_model = {}
        for model, cost, input_tokens, output_tokens, requests in results:
            usage_by_model[model] = {
                "cost_usd": cost or 0.0,
                "input_tokens": input_tokens or 0,
                "output_tokens": output_tokens or 0,
                "requests": requests or 0,
            }

        return usage_by_model

    def generate_report(self) -> str:
        """
        Generate a human-readable usage report.

        Returns:
            Formatted report string
        """
        monthly = self.get_monthly_usage()
        by_model = self.get_usage_by_model()

        report = f"""
=== API Usage Report ===
Period: {date.today().replace(day=1)} to {date.today()}

Monthly Summary:
  Total Cost: ${monthly['cost_usd']:.2f}
  Input Tokens: {monthly['input_tokens']:,}
  Output Tokens: {monthly['output_tokens']:,}
  Requests: {monthly['requests']}
  Budget Remaining: ${monthly['budget_remaining']:.2f}
  Usage: {monthly['usage_percent']:.1f}%

Usage by Model:
"""

        for model, usage in by_model.items():
            report += f"""
  {model}:
    Cost: ${usage['cost_usd']:.2f}
    Input Tokens: {usage['input_tokens']:,}
    Output Tokens: {usage['output_tokens']:,}
    Requests: {usage['requests']}
"""

        return report
