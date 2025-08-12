from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import BigInteger, String, CheckConstraint
from datetime import datetime
from . import Base

class UserBalance(Base):
    __tablename__ = "user_balances"
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    current: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    maximum: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    locked_total: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("current >= 0", name="check_current_nonnegative"),
        CheckConstraint("maximum >= 0", name="check_maximum_nonnegative"),
        CheckConstraint("locked_total >= 0", name="check_locked_nonnegative"),
        CheckConstraint("current <= maximum", name="check_current_le_maximum"),
        CheckConstraint("current + locked_total <= maximum", name="check_current_plus_locked_le_maximum"),
    )
    
    def __repr__(self) -> str:
        return f"<UserBalance user_id={self.user_id} current={self.current} max={self.maximum} locked={self.locked_total}>"
