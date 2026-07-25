from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    transaction_id: str = Field(..., description="Unique ID of the transaction")
    source_account: str = Field(..., description="Account initiating the transaction")
    destination_account: str = Field(..., description="Account receiving the transaction")
    amount: float = Field(..., description="Amount of the transaction")
    currency: str = Field(default="INR", description="Currency of the transaction")
    timestamp: datetime = Field(..., description="When the transaction occurred")
    channel: str = Field(..., description="Channel used (UPI, SWIFT, NEFT, RTGS, CARD)")
    location: Optional[str] = Field(None, description="Location of transaction if available")
    is_fraud: Optional[bool] = Field(None, description="Label for synthetic datasets only")
    fraud_pattern: Optional[str] = Field(None, description="Description of the planted fraud pattern")

class AccountData(BaseModel):
    account_id: str
    customer_id: str
    account_type: str # SAVINGS, CURRENT, CREDIT
    creation_date: datetime
