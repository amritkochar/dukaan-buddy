"""Alert agent - checks for low stock and other alerts."""

from core.state import StoreState


class AlertAgent:
    """Monitors stock levels and generates alerts."""

    def __init__(self, state: StoreState, threshold: float = 5.0):
        self.state = state
        self.threshold = threshold

    def check_alerts(self) -> dict:
        """
        Check for various alerts (currently just low stock).

        Returns:
            dict with alert information
        """
        low_stock_items = self.state.get_low_stock_items(self.threshold)

        return {
            "low_stock_items": low_stock_items,
            "threshold": self.threshold
        }
