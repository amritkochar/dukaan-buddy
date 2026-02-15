"""Expense agent - records and categorizes expenses."""

from loguru import logger
from core.state import StoreState
from core.schemas import SingleIntent


class ExpenseAgent:
    """Handles expense recording and tracking."""

    def __init__(self, state: StoreState):
        self.state = state

    def handle(self, intent: SingleIntent) -> dict:
        """
        Handle expense recording.

        Args:
            intent: SingleIntent with expense details

        Returns:
            dict with expense recording results
        """
        if intent.total_amount is None or intent.total_amount <= 0:
            return {
                "action": "expense_recorded",
                "error": "missing_amount",
                "category": intent.category or "other"
            }

        # Record the expense
        record = self.state.record_expense(
            category=intent.category or "other",
            amount=intent.total_amount,
            description=intent.description or ""
        )

        return {
            "action": "expense_recorded",
            "category": record.category,
            "amount": record.amount,
            "description": record.description,
            "daily_expense_total": self.state.get_daily_expense_total()
        }
