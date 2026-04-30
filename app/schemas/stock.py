from pydantic import BaseModel
from typing import List
class StockInfo(BaseModel):
    date : str
    price: float
    pnl  : float

class StockInfoResponse(BaseModel):
    data: List[StockInfo]