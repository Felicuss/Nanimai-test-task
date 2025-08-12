from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserBalance, BalanceTransaction, TransactionStatus
from app.repositories import BalanceRepository


class BalanceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BalanceRepository(session)

    async def get_balance(self, user_id: str) -> UserBalance:
        balance = await self.repo.get_balance(user_id)
        if balance is None:
            balance = await self.repo.create_balance(user_id)
        return balance

    async def _lock_balance(self, user_id: str) -> UserBalance:
        return await self.repo.lock_balance(user_id)

    async def adjust_limits(self, user_id: str, delta: int) -> UserBalance:
        balance = await self._lock_balance(user_id)
        return await self.repo.apply_limits_delta(balance, delta)

    async def adjust_current(self, user_id: str, delta: int) -> UserBalance:
        balance = await self._lock_balance(user_id)
        return await self.repo.apply_current_delta(balance, delta)

    async def open_transaction(self, user_id: str, service_id: str, external_tx_id: str, amount: int, timeout_seconds: int) -> BalanceTransaction:
        if amount <= 0:
            raise ValueError("Сумма транзакции должна быть положительной")
        
        balance = await self._lock_balance(user_id)
        expires_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
        
        existing_tx = await self.repo.get_transaction(user_id, service_id, external_tx_id)
        if existing_tx:
            if existing_tx.status == TransactionStatus.LOCKED:
                return existing_tx
            else:
                raise ValueError("Транзакция уже завершена")
        
        available = balance.current - balance.locked_total
        if available < amount or balance.current + balance.locked_total + amount > balance.maximum:
            raise ValueError(f"Недостаточно средств. Доступно: {available}, требуется: {amount}")

        transaction = await self.repo.create_transaction(
            user_id=user_id,
            service_id=service_id,
            external_tx_id=external_tx_id,
            amount=amount,
            status=TransactionStatus.LOCKED,
            expires_at=expires_at,
        )
        await self.repo.increment_locked_total(balance, amount)
        
        return transaction

    async def confirm_transaction(self, user_id: str, service_id: str, external_tx_id: str) -> BalanceTransaction:
        balance = await self._lock_balance(user_id)
        transaction = await self.repo.get_transaction(user_id, service_id, external_tx_id)
        
        if not transaction:
            raise ValueError("Транзакция не найдена")
        
        if transaction.status != TransactionStatus.LOCKED:
            return transaction
        
        if transaction.expires_at < datetime.utcnow():
            await self._cancel_transaction_internal(balance, transaction)
            raise ValueError("Транзакция истекла")
        
        balance.current -= transaction.amount
        await self.repo.decrement_locked_total(balance, transaction.amount)
        await self.repo.mark_transaction_confirmed(transaction)
        
        return transaction

    async def cancel_transaction(self, user_id: str, service_id: str, external_tx_id: str) -> BalanceTransaction:
        balance = await self._lock_balance(user_id)
        transaction = await self.repo.get_transaction(user_id, service_id, external_tx_id)
        
        if not transaction:
            raise ValueError("Транзакция не найдена")
        
        if transaction.status != TransactionStatus.LOCKED:
            return transaction
        
        await self._cancel_transaction_internal(balance, transaction)
        return transaction

    async def _cancel_transaction_internal(self, balance: UserBalance, transaction: BalanceTransaction):
        await self.repo.decrement_locked_total(balance, transaction.amount)
        await self.repo.mark_transaction_canceled(transaction)

    # Kept for compatibility if needed in future; currently replaced by repository

    async def repair_user_balance(self, user_id: str) -> UserBalance:
        balance = await self._lock_balance(user_id)
        
        actual_locked = await self.repo.sum_locked_transactions(user_id)
        
        balance.locked_total = actual_locked
        
        max_allowed = max(0, balance.maximum - balance.locked_total)
        if balance.current > max_allowed:
            balance.current = max_allowed
        if balance.current < 0:
            balance.current = 0
        
        return balance

    async def sweep_expired_transactions(self, batch_size: int = 100) -> int:
        now = datetime.utcnow()
        
        expired_transactions = await self.repo.list_expired_locked_transactions(
            now=now, limit=batch_size
        )
        
        canceled_count = 0
        for tx in expired_transactions:
            try:
                balance = await self._lock_balance(tx.user_id)
                if tx.status == TransactionStatus.LOCKED:
                    await self._cancel_transaction_internal(balance, tx)
                    canceled_count += 1
            except Exception:
                continue
        
        return canceled_count


