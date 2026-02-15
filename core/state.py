"""
In-memory store state backed by PostgreSQL (sync version).
"""

import os
import psycopg2
from datetime import datetime, date
from loguru import logger
from typing import Optional, Union
from core.schemas import InventoryItem, ExpenseRecord, SaleRecord, DailySummary
from core.normalizer import normalize_item, normalize_category


class StoreState:
    """
    In-memory store state with PostgreSQL persistence.
    Manages inventory, expenses, and sales for a single store.
    """

    def __init__(
        self,
        shopkeeper_name: str = "भैया",
        shopkeeper_honorific: str = "",
        low_stock_threshold: float = 5.0
    ):
        self.shopkeeper_name = shopkeeper_name
        self.shopkeeper_honorific = shopkeeper_honorific
        self.low_stock_threshold = low_stock_threshold

        self.inventory: dict[str, InventoryItem] = {}
        self.expenses: list[ExpenseRecord] = []
        self.sales: list[SaleRecord] = []

        self._saved_sales_count = 0
        self._saved_expenses_count = 0

        self._init_tables()

    def _get_conn(self):
        return psycopg2.connect(os.getenv("DATABASE_URL"))

    def _init_tables(self):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    item_name TEXT PRIMARY KEY,
                    quantity DOUBLE PRECISION,
                    unit TEXT,
                    avg_cost DOUBLE PRECISION,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    category TEXT,
                    amount DOUBLE PRECISION,
                    description TEXT,
                    created_at TEXT,
                    day TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id SERIAL PRIMARY KEY,
                    item_name TEXT,
                    quantity DOUBLE PRECISION,
                    unit TEXT,
                    price DOUBLE PRECISION,
                    total DOUBLE PRECISION,
                    created_at TEXT,
                    day TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _normalize_item_name(self, item_name: str) -> str:
        """
        Normalize item names using the normalizer module.
        Handles Hindi→English translation, typos, plurals, case.
        """
        return normalize_item(item_name)

    def _get_today_str(self) -> str:
        """Get today's date as YYYY-MM-DD string."""
        return date.today().isoformat()

    def add_stock(
        self,
        item_name: str,
        quantity: float,
        unit: str,
        cost_per_unit: float
    ) -> InventoryItem:
        """
        Add stock to inventory.
        If item exists: add quantity, recalculate weighted avg cost.
        If new: create entry.
        """
        item_name = self._normalize_item_name(item_name)

        if item_name in self.inventory:
            existing = self.inventory[item_name]
            total_existing_value = existing.quantity * existing.avg_cost_per_unit
            total_new_value = quantity * cost_per_unit
            new_total_qty = existing.quantity + quantity

            if new_total_qty > 0:
                new_avg_cost = (total_existing_value + total_new_value) / new_total_qty
            else:
                new_avg_cost = existing.avg_cost_per_unit

            existing.quantity = new_total_qty
            existing.avg_cost_per_unit = new_avg_cost
            existing.unit = unit
            existing.last_updated = datetime.now()

            logger.info(f"Updated stock: {item_name} → {new_total_qty} {unit}")
            return existing
        else:
            new_item = InventoryItem(
                item_name=item_name,
                quantity=quantity,
                unit=unit,
                avg_cost_per_unit=cost_per_unit,
                last_updated=datetime.now()
            )
            self.inventory[item_name] = new_item

            logger.info(f"Added new stock: {item_name} → {quantity} {unit}")
            return new_item

    def update_stock(
        self,
        item_name: str,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        cost_per_unit: Optional[float] = None
    ) -> Optional[InventoryItem]:
        """
        Replace (not add to) an existing item's quantity and/or cost.
        Used for corrections.
        """
        item_name = self._normalize_item_name(item_name)

        if item_name not in self.inventory:
            logger.warning(f"Correction for unknown item: {item_name}")
            return None

        item = self.inventory[item_name]
        if quantity is not None:
            item.quantity = quantity
        if unit is not None:
            item.unit = unit
        if cost_per_unit is not None:
            item.avg_cost_per_unit = cost_per_unit
        item.last_updated = datetime.now()

        logger.info(f"Corrected stock: {item_name} → qty={item.quantity}, cost={item.avg_cost_per_unit}")
        return item

    def remove_stock(self, item_name: str, quantity: float) -> Optional[InventoryItem]:
        """
        Remove stock from inventory.
        Allow negative (means sold more than tracked).
        """
        item_name = self._normalize_item_name(item_name)

        if item_name in self.inventory:
            item = self.inventory[item_name]
            item.quantity -= quantity
            item.last_updated = datetime.now()

            logger.info(f"Removed stock: {item_name} → {quantity} (remaining: {item.quantity})")
            return item
        else:
            logger.warning(f"Removing stock for unknown item: {item_name}")
            new_item = InventoryItem(
                item_name=item_name,
                quantity=-quantity,
                unit="unit",
                avg_cost_per_unit=0.0,
                last_updated=datetime.now()
            )
            self.inventory[item_name] = new_item
            return new_item

    def record_expense(
        self,
        category: str,
        amount: float,
        description: str = ""
    ) -> ExpenseRecord:
        """Record an expense."""
        normalized_category = normalize_category(category)

        record = ExpenseRecord(
            category=normalized_category,
            amount=amount,
            description=description,
            timestamp=datetime.now()
        )
        self.expenses.append(record)

        logger.info(f"Recorded expense: {normalized_category} → ₹{amount}")
        return record

    def record_sale(
        self,
        item_name: str,
        quantity: float,
        unit: str,
        price_per_unit: float,
        total: float = None
    ) -> SaleRecord:
        """
        Record a sale.
        Also removes stock from inventory.
        """
        if total is None:
            total = quantity * price_per_unit

        record = SaleRecord(
            item_name=self._normalize_item_name(item_name),
            quantity=quantity,
            unit=unit,
            price_per_unit=price_per_unit,
            total=total,
            timestamp=datetime.now()
        )
        self.sales.append(record)

        self.remove_stock(item_name, quantity)

        logger.info(f"Recorded sale: {item_name} → {quantity} {unit} @ ₹{price_per_unit} = ₹{total}")
        return record

    def get_stock(self, item_name: Optional[str] = None) -> Union[Optional[InventoryItem], dict[str, InventoryItem]]:
        """
        Get inventory.
        If item_name provided: return single item or None.
        If no item_name: return full inventory dict.
        """
        if item_name:
            item_name = self._normalize_item_name(item_name)
            return self.inventory.get(item_name)
        else:
            return self.inventory.copy()

    def get_daily_sales_total(self) -> float:
        """Get total sales revenue for today."""
        return sum(sale.total for sale in self.sales)

    def get_daily_expense_total(self) -> float:
        """Get total expenses for today."""
        return sum(expense.amount for expense in self.expenses)

    def get_daily_cogs(self) -> float:
        """Get cost of goods sold today (only items actually sold)."""
        cogs = 0.0
        for sale in self.sales:
            item_name = self._normalize_item_name(sale.item_name)
            if item_name in self.inventory:
                avg_cost = self.inventory[item_name].avg_cost_per_unit
                cogs += sale.quantity * avg_cost
        return cogs

    def get_daily_profit(self) -> float:
        """
        Calculate daily profit.
        Profit = Sales Revenue - Cost of Goods Sold (only sold items) - Operational Expenses
        Note: Inventory purchased but not sold is NOT a loss — it's still in stock.
        """
        sales_revenue = self.get_daily_sales_total()
        cogs = self.get_daily_cogs()
        expenses = self.get_daily_expense_total()
        return sales_revenue - cogs - expenses

    def get_total_inventory_value(self) -> float:
        """Get total value of current inventory."""
        return sum(item.quantity * item.avg_cost_per_unit for item in self.inventory.values() if item.quantity > 0)

    def get_low_stock_items(self, threshold: float = None) -> list[str]:
        """Get list of items below stock threshold."""
        if threshold is None:
            threshold = self.low_stock_threshold

        low_stock = []
        for item_name, item in self.inventory.items():
            if 0 < item.quantity <= threshold:
                low_stock.append(f"{item_name} ({item.quantity} {item.unit})")
        return low_stock

    def get_daily_summary(self) -> DailySummary:
        """Get complete daily summary."""
        items_sold = [
            {
                "item": sale.item_name,
                "quantity": sale.quantity,
                "unit": sale.unit,
                "revenue": sale.total
            }
            for sale in self.sales
        ]

        expenses_list = [
            {
                "category": exp.category,
                "amount": exp.amount,
                "description": exp.description
            }
            for exp in self.expenses
        ]

        return DailySummary(
            date=self._get_today_str(),
            total_sales=self.get_daily_sales_total(),
            total_expenses=self.get_daily_expense_total(),
            profit=self.get_daily_profit(),
            items_sold=items_sold,
            expenses_list=expenses_list,
            low_stock_items=self.get_low_stock_items(),
            cogs=self.get_daily_cogs(),
            inventory_value=self.get_total_inventory_value()
        )

    def save_to_db(self):
        """Persist current state to PostgreSQL."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            for item_name, item in self.inventory.items():
                cursor.execute("""
                    INSERT INTO inventory (item_name, quantity, unit, avg_cost, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (item_name) DO UPDATE SET
                        quantity = EXCLUDED.quantity,
                        unit = EXCLUDED.unit,
                        avg_cost = EXCLUDED.avg_cost,
                        updated_at = EXCLUDED.updated_at
                """, (item_name, item.quantity, item.unit, item.avg_cost_per_unit, item.last_updated.isoformat()))

            today = self._get_today_str()
            new_expenses = self.expenses[self._saved_expenses_count:]
            for exp in new_expenses:
                cursor.execute("""
                    INSERT INTO expenses (category, amount, description, created_at, day)
                    VALUES (%s, %s, %s, %s, %s)
                """, (exp.category, exp.amount, exp.description, exp.timestamp.isoformat(), today))
            self._saved_expenses_count = len(self.expenses)

            new_sales = self.sales[self._saved_sales_count:]
            for sale in new_sales:
                cursor.execute("""
                    INSERT INTO sales (item_name, quantity, unit, price, total, created_at, day)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (sale.item_name, sale.quantity, sale.unit, sale.price_per_unit, sale.total, sale.timestamp.isoformat(), today))
            self._saved_sales_count = len(self.sales)

            conn.commit()
            logger.info("✅ State saved to database")
        finally:
            conn.close()

    def load_from_db(self):
        """Restore state from PostgreSQL on startup."""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT item_name, quantity, unit, avg_cost, updated_at FROM inventory")
                for row in cursor.fetchall():
                    item_name, quantity, unit, avg_cost, updated_at = row
                    self.inventory[item_name] = InventoryItem(
                        item_name=item_name,
                        quantity=quantity,
                        unit=unit,
                        avg_cost_per_unit=avg_cost,
                        last_updated=datetime.fromisoformat(updated_at)
                    )
            except Exception:
                pass

            today = self._get_today_str()
            try:
                cursor.execute(
                    "SELECT category, amount, description, created_at FROM expenses WHERE day = %s",
                    (today,)
                )
                for row in cursor.fetchall():
                    category, amount, description, created_at = row
                    self.expenses.append(ExpenseRecord(
                        category=category,
                        amount=amount,
                        description=description,
                        timestamp=datetime.fromisoformat(created_at)
                    ))
                self._saved_expenses_count = len(self.expenses)
            except Exception:
                pass

            try:
                cursor.execute(
                    "SELECT item_name, quantity, unit, price, total, created_at FROM sales WHERE day = %s",
                    (today,)
                )
                for row in cursor.fetchall():
                    item_name, quantity, unit, price, total, created_at = row
                    self.sales.append(SaleRecord(
                        item_name=item_name,
                        quantity=quantity,
                        unit=unit,
                        price_per_unit=price,
                        total=total,
                        timestamp=datetime.fromisoformat(created_at)
                    ))
                self._saved_sales_count = len(self.sales)
            except Exception:
                pass

            logger.info(f"✅ State loaded: {len(self.inventory)} items, {len(self.sales)} sales, {len(self.expenses)} expenses")
        finally:
            conn.close()
