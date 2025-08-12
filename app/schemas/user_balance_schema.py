from pydantic import BaseModel, Field

class BalanceRead(BaseModel):
    user_id: str
    current: int = Field(ge=0)
    maximum: int = Field(ge=0)
    locked_total: int = Field(ge=0)

class AdjustLimitsRequest(BaseModel):
    delta: int

class AdjustCurrentRequest(BaseModel):
    delta: int