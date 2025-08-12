from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserBalance, BalanceTransaction, TransactionStatus


class BalanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_balance(self, user_id: str) -> Optional[UserBalance]:
        result = await self.session.execute(select(UserBalance).where(UserBalance.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_balance(self, user_id: str) -> UserBalance:
        balance = UserBalance(user_id=user_id, current=0, maximum=0, locked_total=0)
        self.session.add(balance)
        await self.session.flush()
        return balance

    async def lock_balance(self, user_id: str) -> UserBalance:
        result = await self.session.execute(select(UserBalance).where(UserBalance.user_id == user_id).with_for_update())
        balance = result.scalar_one_or_none()
        if balance is None:
            balance = await self.create_balance(user_id)
        return balance

    async def apply_limits_delta(self, balance: UserBalance, delta: int) -> UserBalance:
        new_maximum = balance.maximum + delta
        if new_maximum < 0:
            raise ValueError("Максимальный баланс не может быть отрицательным")
        if new_maximum < balance.current + balance.locked_total:
            raise ValueError("Новый максимум меньше текущего баланса + заблокированных средств")
        balance.maximum = new_maximum
        return balance

    async def apply_current_delta(self, balance: UserBalance, delta: int) -> UserBalance:
        new_current = balance.current + delta
        if new_current < 0:
            raise ValueError("Текущий баланс не может быть отрицательным")
        if new_current + balance.locked_total > balance.maximum:
            raise ValueError("Текущий баланс + заблокированные средства превышают максимум")
        balance.current = new_current
        return balance

    async def increment_locked_total(self, balance: UserBalance, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if balance.locked_total + amount > balance.maximum - balance.current:
            raise ValueError("Недостаточно доступного лимита для блокировки средств")
        balance.locked_total += amount

    async def decrement_locked_total(self, balance: UserBalance, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if balance.locked_total - amount < 0:
            raise ValueError("Заблокированные средства не могут быть отрицательными")
        balance.locked_total -= amount

    async def get_transaction(self, user_id: str, service_id: str, external_tx_id: str) -> Optional[BalanceTransaction]:
        result = await self.session.execute(select(BalanceTransaction).where(and_(BalanceTransaction.user_id == user_id, BalanceTransaction.service_id == service_id, BalanceTransaction.external_tx_id == external_tx_id)))
        return result.scalar_one_or_none()

    async def create_transaction(self, user_id: str, service_id: str, external_tx_id: str, amount: int, status: TransactionStatus, expires_at: datetime) -> BalanceTransaction:
        transaction = BalanceTransaction(user_id=user_id, service_id=service_id, external_tx_id=external_tx_id, amount=amount, status=status, expires_at=expires_at)
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def sum_locked_transactions(self, user_id: str) -> int:
        result = await self.session.execute(select(func.coalesce(func.sum(BalanceTransaction.amount), 0)).where(and_(BalanceTransaction.user_id == user_id, BalanceTransaction.status == TransactionStatus.LOCKED)))
        return int(result.scalar_one())

    async def list_expired_locked_transactions(self, now: datetime, limit: int) -> List[BalanceTransaction]:
        result = await self.session.execute(select(BalanceTransaction).where(and_(BalanceTransaction.status == TransactionStatus.LOCKED, BalanceTransaction.expires_at < now)).limit(limit))
        return list(result.scalars().all())

    async def mark_transaction_confirmed(self, transaction: BalanceTransaction) -> None:
        transaction.status = TransactionStatus.CONFIRMED
        transaction.closed_at = datetime.utcnow()

    async def mark_transaction_canceled(self, transaction: BalanceTransaction) -> None:
        transaction.status = TransactionStatus.CANCELED
        transaction.closed_at = datetime.utcnow()


