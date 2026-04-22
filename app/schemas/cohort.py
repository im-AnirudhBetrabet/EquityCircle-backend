from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class CohortBase(BaseModel):
    month_year: str
    status    : str = "OPEN"

class CohortCreate(CohortBase):
    group_id: UUID

class CohortRead(CohortBase):
    id        : UUID
    group_id  : UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)