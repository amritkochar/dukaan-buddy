"""Pydantic models for Dukaan Buddy."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class IntentType(str, Enum):
    INVENTORY_IN = "inventory_in"
    INVENTORY_OUT = "inventory_out"
    EXPENSE = "expense"
    SALE = "sale"
    QUERY_STOCK = "query_stock"
    QUERY_SUMMARY = "query_summary"
    QUERY_PROFIT = "query_profit"
    GREETING = "greeting"
    CLOSE_DAY = "close_day"
    CORRECTION = "correction"
    UNKNOWN = "unknown"


class SingleIntent(BaseModel):
    intent: IntentType
    item: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    total_amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class RouterOutput(BaseModel):
    intents: list[SingleIntent]


class InventoryItem(BaseModel):
    item_name: str
    quantity: float
    unit: str
    avg_cost_per_unit: float
    last_updated: datetime = Field(default_factory=datetime.now)


class ExpenseRecord(BaseModel):
    category: str
    amount: float
    description: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SaleRecord(BaseModel):
    item_name: str
    quantity: float
    unit: str
    price_per_unit: float
    total: float
    timestamp: datetime = Field(default_factory=datetime.now)


class DailySummary(BaseModel):
    date: str
    total_sales: float
    total_expenses: float
    profit: float
    items_sold: list[dict]
    expenses_list: list[dict]
    low_stock_items: list[str]
