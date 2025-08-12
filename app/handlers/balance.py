from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.user_balance_schema import BalanceRead, AdjustLimitsRequest, AdjustCurrentRequest
from app.schemas.transactions import (
    CreateTransactionRequest,
    TransactionResponse,
    ServiceIdRequest,
)
from app.services.balance_service import BalanceService

router = APIRouter(prefix='/balance', tags=['balance'])

@router.get("/{user_id}", response_model=BalanceRead)
async def get_balance(user_id: str, session: AsyncSession = Depends(get_db)):
    service = BalanceService(session)
    balance = await service.get_balance(user_id)
    await session.commit()  # Коммитим транзакцию
    return BalanceRead(
        user_id=balance.user_id,
        current=balance.current,
        maximum=balance.maximum,
        locked_total=balance.locked_total
    )

@router.post("/{user_id}/limits", response_model=BalanceRead)
async def adjust_limits(
    user_id: str,
    request: AdjustLimitsRequest,
    session: AsyncSession = Depends(get_db),
):
    service = BalanceService(session)
    try:
        balance = await service.adjust_limits(user_id, request.delta)
        await session.commit()
        return BalanceRead(
            user_id=balance.user_id,
            current=balance.current,
            maximum=balance.maximum,
            locked_total=balance.locked_total
        )
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{user_id}/current", response_model=BalanceRead)
async def adjust_current(
    user_id: str,
    request: AdjustCurrentRequest,
    session: AsyncSession = Depends(get_db),
):
    service = BalanceService(session)
    try:
        balance = await service.adjust_current(user_id, request.delta)
        await session.commit()
        return BalanceRead(
            user_id=balance.user_id,
            current=balance.current,
            maximum=balance.maximum,
            locked_total=balance.locked_total
        )
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{user_id}/transactions", response_model=TransactionResponse)
async def open_transaction(
    user_id: str,
    request: CreateTransactionRequest,
    session: AsyncSession = Depends(get_db),
):
    service = BalanceService(session)
    try:
        transaction = await service.open_transaction(
            user_id=user_id,
            service_id=request.service_id,
            external_tx_id=request.external_tx_id,
            amount=request.amount,
            timeout_seconds=request.timeout_seconds,
        )
        await session.commit()
        return TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            service_id=transaction.service_id,
            external_tx_id=transaction.external_tx_id,
            amount=transaction.amount,
            status=transaction.status.value,
            created_at=transaction.created_at,
            expires_at=transaction.expires_at,
            closed_at=transaction.closed_at
        )
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{user_id}/transactions/{external_tx_id}/confirm", response_model=TransactionResponse)
async def confirm_transaction(
    user_id: str,
    external_tx_id: str,
    request: ServiceIdRequest,
    session: AsyncSession = Depends(get_db),
):
    service = BalanceService(session)
    try:
        transaction = await service.confirm_transaction(user_id, request.service_id, external_tx_id)
        await session.commit()
        return TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            service_id=transaction.service_id,
            external_tx_id=transaction.external_tx_id,
            amount=transaction.amount,
            status=transaction.status.value,
            created_at=transaction.created_at,
            expires_at=transaction.expires_at,
            closed_at=transaction.closed_at
        )
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{user_id}/transactions/{external_tx_id}/cancel", response_model=TransactionResponse)
async def cancel_transaction(
    user_id: str,
    external_tx_id: str,
    request: ServiceIdRequest,
    session: AsyncSession = Depends(get_db),
):
    service = BalanceService(session)
    try:
        transaction = await service.cancel_transaction(user_id, request.service_id, external_tx_id)
        await session.commit()
        return TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            service_id=transaction.service_id,
            external_tx_id=transaction.external_tx_id,
            amount=transaction.amount,
            status=transaction.status.value,
            created_at=transaction.created_at,
            expires_at=transaction.expires_at,
            closed_at=transaction.closed_at
        )
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{user_id}/repair", response_model=BalanceRead)
async def repair_balance(user_id: str, session: AsyncSession = Depends(get_db)):
    service = BalanceService(session)
    balance = await service.repair_user_balance(user_id)
    await session.commit()
    return BalanceRead(
        user_id=balance.user_id,
        current=balance.current,
        maximum=balance.maximum,
        locked_total=balance.locked_total
    )
