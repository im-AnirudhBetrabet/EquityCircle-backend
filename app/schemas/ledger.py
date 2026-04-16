from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from datetime import datetime
from uuid import UUID

class LedgerBase(BaseModel):
    transaction_type: Literal['DEPOSIT', 'WITHDRAWAL', 'ROLL_FORWARD', 'INTEREST']
    amount          : float = Field(..., description="The transaction amount. Can be negative for withdrawals")

class LedgerCreate(LedgerBase):
    group_id : UUID
    cohort_id: UUID
    user_id  : UUID

class LedgerRead(LedgerBase):
    id              : UUID
    group_id        : UUID
    cohort_id       : UUID
    user_id         : UUID
    transaction_date: datetime

    model_config = ConfigDict(from_attributes=True)