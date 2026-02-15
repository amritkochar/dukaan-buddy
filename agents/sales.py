"""Sales agent - records sales transactions."""

from loguru import logger
from core.state import StoreState
from core.schemas import SingleIntent


class SalesAgent:
    """Handles sales recording and tracking."""

    def __init__(self, state: StoreState):
        self.state = state

    def handle(self, intent: SingleIntent) -> dict:
        """
        Handle sale recording.

        Args:
            intent: SingleIntent with sale details

        Returns:
            dict with sale recording results
        """
        if not intent.item or intent.quantity is None or intent.quantity <= 0:
            return {
                "action": "sale_recorded",
                "error": "missing_data",
                "item": intent.item,
                "quantity": intent.quantity
            }

        # Calculate total if not provided
        total = intent.total_amount
        if total is None and intent.price_per_unit is not None:
            total = intent.quantity * intent.price_per_unit
        elif total is None:
            total = 0.0

        # Calculate price_per_unit if not provided
        price_per_unit = intent.price_per_unit
        if price_per_unit is None and total > 0 and intent.quantity > 0:
            price_per_unit = total / intent.quantity
        elif price_per_unit is None:
            price_per_unit = 0.0

        # Record the sale (this also removes stock automatically)
        record = self.state.record_sale(
            item_name=intent.item,
            quantity=intent.quantity,
            unit=intent.unit or "unit",
            price_per_unit=price_per_unit,
            total=total
        )

        # Get remaining stock
        current = self.state.get_stock(intent.item)
        remaining = current.quantity if current else 0

        return {
            "action": "sale_recorded",
            "item": intent.item,
            "quantity": intent.quantity,
            "unit": intent.unit or "unit",
            "price_per_unit": price_per_unit,
            "revenue": total,
            "remaining_stock": remaining,
            "remaining_unit": current.unit if current else "unit",
            "daily_sales_total": self.state.get_daily_sales_total()
        }
