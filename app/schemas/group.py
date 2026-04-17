from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class GroupCreate(BaseModel):
    name: str

class GroupRead(BaseModel):
    id        : UUID
    name      : str
    created_at: datetime

    model_config =  ConfigDict(from_attributes=True)

class RequestUpdate(BaseModel):
    status: str

class GroupRequestRead(BaseModel):
    created_at: datetime
    user_id   : UUID
    group_id  : UUID
    status    : str
    id        : UUID

    model_config = ConfigDict(from_attributes=True)