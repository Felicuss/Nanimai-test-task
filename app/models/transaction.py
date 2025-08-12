from __future__ import annotations
from datetime import datetime
from sqlalchemy import BigInteger, String, CheckConstraint, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from . import Base
import enum

class TransactionStatus(enum.Enum):
    LOCKED = "locked"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"

class BalanceTransaction(Base):
    __tablename__ = "balance_transactions"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    service_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    external_tx_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.LOCKED, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    closed_at: Mapped[datetime] = mapped_column(nullable=True)
    
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
        Index("idx_user_service_external_unique", "user_id", "service_id", "external_tx_id", unique=True),
        Index("idx_user_status", "user_id", "status"),
        Index("idx_expires_status", "status", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<BalanceTransaction id={self.id} user_id={self.user_id} amount={self.amount} status={self.status}>"


