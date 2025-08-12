import asyncio
from datetime import datetime
import grpc
from app.db import AsyncSessionLocal
from app.services.balance_service import BalanceService
from . import balance_pb2, balance_pb2_grpc


def dt_to_str(dt: datetime | None) -> str:
    return dt.isoformat() if dt else ""


class BalanceAPI(balance_pb2_grpc.BalanceAPIServicer):
    async def GetBalance(self, request, context):
        async with AsyncSessionLocal() as session:
            service = BalanceService(session)
            bal = await service.get_balance(request.user_id)
            return balance_pb2.BalanceResponse(user_id=bal.user_id, current=bal.current, maximum=bal.maximum, locked_total=bal.locked_total)

    async def AdjustLimits(self, request, context):
        async with AsyncSessionLocal() as session:
            service = BalanceService(session)
            bal = await service.adjust_limits(request.user_id, int(request.delta))
            await session.commit()
            return balance_pb2.BalanceResponse(user_id=bal.user_id, current=bal.current, maximum=bal.maximum, locked_total=bal.locked_total)

    async def AdjustCurrent(self, request, context):
        async with AsyncSessionLocal() as session:
            service = BalanceService(session)
            bal = await service.adjust_current(request.user_id, int(request.delta))
            await session.commit()
            return balance_pb2.BalanceResponse(user_id=bal.user_id, current=bal.current, maximum=bal.maximum, locked_total=bal.locked_total)

    async def OpenTransaction(self, request, context):
        async with AsyncSessionLocal() as session:
            service = BalanceService(session)
            tx = await service.open_transaction(user_id=request.user_id, service_id=request.service_id, external_tx_id=request.external_tx_id, amount=int(request.amount), timeout_seconds=int(request.timeout_seconds))
            await session.commit()
            return balance_pb2.TransactionResponse(id=tx.id, user_id=tx.user_id, service_id=tx.service_id, external_tx_id=tx.external_tx_id, amount=tx.amount, status=tx.status.value, created_at=dt_to_str(tx.created_at), expires_at=dt_to_str(tx.expires_at), closed_at=dt_to_str(tx.closed_at))

    async def ConfirmTransaction(self, request, context):
        async with AsyncSessionLocal() as session:
            service = BalanceService(session)
            tx = await service.confirm_transaction(user_id=request.user_id, service_id=request.service_id, external_tx_id=request.external_tx_id)
            await session.commit()
            return balance_pb2.TransactionResponse(id=tx.id, user_id=tx.user_id, service_id=tx.service_id, external_tx_id=tx.external_tx_id, amount=tx.amount, status=tx.status.value, created_at=dt_to_str(tx.created_at), expires_at=dt_to_str(tx.expires_at), closed_at=dt_to_str(tx.closed_at))

    async def CancelTransaction(self, request, context):
        async with AsyncSessionLocal() as session:
            service = BalanceService(session)
            tx = await service.cancel_transaction(user_id=request.user_id, service_id=request.service_id, external_tx_id=request.external_tx_id)
            await session.commit()
            return balance_pb2.TransactionResponse(id=tx.id, user_id=tx.user_id, service_id=tx.service_id, external_tx_id=tx.external_tx_id, amount=tx.amount, status=tx.status.value, created_at=dt_to_str(tx.created_at), expires_at=dt_to_str(tx.expires_at), closed_at=dt_to_str(tx.closed_at))


async def serve(bind_addr: str = "0.0.0.0:50051"):
    server = grpc.aio.server()
    balance_pb2_grpc.add_BalanceAPIServicer_to_server(BalanceAPI(), server)
    server.add_insecure_port(bind_addr)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
