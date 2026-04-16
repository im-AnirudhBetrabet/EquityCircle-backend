from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProfileBase(BaseModel):
    display_name: str
    role        : str = "member"

class ProfileRead(ProfileBase):
    id        : UUID
    group_id  : UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)