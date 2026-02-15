"""Inventory agent - handles stock in/out and stock queries."""

from loguru import logger
from core.state import StoreState
from core.schemas import SingleIntent, IntentType


class InventoryAgent:
    """Handles inventory operations: stock in, stock out, stock queries."""

    def __init__(self, state: StoreState):
        self.state = state

    def handle(self, intent: SingleIntent) -> dict:
        """
        Handle inventory-related intents.

        Args:
            intent: SingleIntent with inventory operation details

        Returns:
            dict with action results
        """
        if intent.intent == IntentType.INVENTORY_IN:
            return self._handle_stock_in(intent)
        elif intent.intent == IntentType.INVENTORY_OUT:
            return self._handle_stock_out(intent)
        elif intent.intent == IntentType.QUERY_STOCK:
            return self._handle_stock_query(intent)
        elif intent.intent == IntentType.CORRECTION:
            return self._handle_correction(intent)
        else:
            logger.warning(f"InventoryAgent received unexpected intent: {intent.intent}")
            return {"action": "unknown", "error": "unexpected_intent"}

    def _handle_stock_in(self, intent: SingleIntent) -> dict:
        """Handle stock addition."""
        if not intent.item or intent.quantity is None:
            return {"action": "stock_added", "error": "missing_data",
                    "item": intent.item, "quantity": intent.quantity}

        # Calculate price_per_unit if not provided
        price_per_unit = intent.price_per_unit
        if price_per_unit is None and intent.total_amount and intent.quantity:
            price_per_unit = intent.total_amount / intent.quantity
        elif price_per_unit is None:
            price_per_unit = 0.0

        # Calculate total value
        total = intent.total_amount
        if total is None and price_per_unit is not None:
            total = (intent.quantity or 0) * price_per_unit

        # Add to inventory
        item = self.state.add_stock(
            intent.item,
            intent.quantity or 0,
            intent.unit or "unit",
            price_per_unit
        )

        return {
            "action": "stock_added",
            "item": intent.item,
            "quantity": intent.quantity,
            "unit": intent.unit or "unit",
            "price_per_unit": price_per_unit,
            "total_value": total,
            "current_stock": item.quantity,
            "current_unit": item.unit
        }

    def _handle_stock_out(self, intent: SingleIntent) -> dict:
        """Handle stock removal (damaged/returned)."""
        if not intent.item or intent.quantity is None:
            return {"action": "stock_removed", "error": "missing_data"}

        item = self.state.remove_stock(intent.item, intent.quantity or 0)

        return {
            "action": "stock_removed",
            "item": intent.item,
            "quantity": intent.quantity,
            "current_stock": item.quantity if item else 0,
            "unit": item.unit if item else "unit"
        }

    def _handle_correction(self, intent: SingleIntent) -> dict:
        """Handle correction of a previous entry."""
        if not intent.item:
            return {"action": "correction", "error": "missing_item"}

        # Calculate price_per_unit if not provided
        price_per_unit = intent.price_per_unit
        if price_per_unit is None and intent.total_amount and intent.quantity:
            price_per_unit = intent.total_amount / intent.quantity

        item = self.state.update_stock(
            intent.item,
            quantity=intent.quantity,
            unit=intent.unit,
            cost_per_unit=price_per_unit
        )

        if item is None:
            return {"action": "correction", "error": "item_not_found", "item": intent.item}

        return {
            "action": "correction",
            "item": intent.item,
            "quantity": item.quantity,
            "unit": item.unit,
            "price_per_unit": item.avg_cost_per_unit,
            "note": "entry_corrected"
        }

    def _handle_stock_query(self, intent: SingleIntent) -> dict:
        """Handle stock information queries."""
        if intent.item:
            # Query for specific item
            item = self.state.get_stock(intent.item)
            if item:
                return {
                    "action": "stock_info",
                    "item": intent.item,
                    "quantity": item.quantity,
                    "unit": item.unit
                }
            else:
                return {
                    "action": "stock_info",
                    "item": intent.item,
                    "quantity": 0,
                    "unit": "unknown",
                    "note": "item_not_found"
                }
        else:
            # Query for all stock
            all_stock = self.state.get_stock()
            items = [
                {"item": k, "qty": v.quantity, "unit": v.unit}
                for k, v in all_stock.items()
            ]
            return {
                "action": "full_stock",
                "items": items,
                "total_items": len(items)
            }
