from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CreateTransactionRequest(BaseModel):
    service_id: str
    external_tx_id: str
    amount: int = Field(gt=0)
    timeout_seconds: int = Field(gt=0, le=3600)

class TransactionResponse(BaseModel):
    id: int
    user_id: str
    service_id: str
    external_tx_id: str
    amount: int
    status: str
    created_at: datetime
    expires_at: datetime
    closed_at: Optional[datetime] = None


class ServiceIdRequest(BaseModel):
    service_id: str
