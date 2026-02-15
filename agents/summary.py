"""Summary agent - generates daily summaries and reports."""

from loguru import logger
from core.state import StoreState
from core.schemas import SingleIntent, IntentType


class SummaryAgent:
    """Handles summary and reporting requests."""

    def __init__(self, state: StoreState):
        self.state = state

    def handle(self, intent: SingleIntent) -> dict:
        """
        Handle summary requests (daily summary, profit queries, day closing).

        Args:
            intent: SingleIntent with summary request type

        Returns:
            dict with summary data
        """
        # Get the daily summary
        summary = self.state.get_daily_summary()

        # Check if this is a day closing request
        is_closing = intent.intent == IntentType.CLOSE_DAY

        return {
            "action": "closing_summary" if is_closing else "summary",
            "total_sales": summary.total_sales,
            "total_expenses": summary.total_expenses,
            "profit": summary.profit,
            "items_sold": summary.items_sold[:5],  # Top 5 items
            "expenses_list": summary.expenses_list[:5],  # Top 5 expenses
            "low_stock_items": summary.low_stock_items,
            "is_closing": is_closing
        }
