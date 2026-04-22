from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class TradeBase(BaseModel):
    # Shared properties
    ticker_symbol: str   = Field(..., description="The yfinance compatible ticker e.g. RELIANCE.NS")
    quantity     : float = Field(..., description="Number of share brought.")
    buy_price    : float = Field(..., description="Average price per share.")
    buy_date     : datetime
class TradeCreate(TradeBase):
    # Used when a new trade is executed
    cohort_id: UUID

class TradeUpdate(BaseModel):
    # Used when a trade is 'closed'
    status    : str = "CLOSED"
    sell_price: float = Field(..., gt=0)
    sell_date : datetime

class TradeRead(TradeBase):
    id        : UUID
    cohort_id : UUID
    buy_date  : datetime
    status    : str
    sell_price: Optional[float] = None
    sell_date : Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TradeAdjustment(BaseModel):
    other_pnl_amount: float
