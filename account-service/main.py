import time
import database.crud as crud
import logging
import uvicorn
import controller.account as account_controller
import controller.transaksi as transaksi_controller
from fastapi import FastAPI, Response, status, Request
from fastapi.responses import JSONResponse
from database.schemas import AccountRequest, TransaksiRequest, TransferRequest
from datetime import datetime
from uvicorn import Config, Server
from loguru import logger
from utils.hashing import Hasher
from utils.log_config import setup_logging, LOG_LEVEL
from utils.kafka_utils import publish_message
from middleware import pin_validation

app = FastAPI() # inisialisasi app

@app.middleware("http")
async def pin_validation_middleware(request: Request, call_next):
    return await pin_validation(request, call_next)

@app.post("/daftar")
def create_account(account: AccountRequest):
    logger.info(f"Request: {account}")
    result = account_controller.create_account(account)
    if result["remark"] == "failed":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

@app.post("/tabung")
def tabung(transaksi: TransaksiRequest):
    logger.info(f"Request: {transaksi}")
    result = transaksi_controller.tabung(transaksi)
    if result["remark"] == "failed":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

@app.post("/tarik")
def tarik(transaksi: TransaksiRequest):
    logger.info(f"Request: {transaksi}")
    result = transaksi_controller.tarik(transaksi)
    if result["remark"] == "failed":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

# endpoint untuk cek saldo
@app.get("/saldo/{no_rekening}")
def get_saldo(no_rekening: str):
    logger.info(f"Request: {no_rekening}")
    result = account_controller.check_account_existence(no_rekening)
    if result["remark"] == "failed":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

@app.post("/transfer")
def transfer(transfer: TransferRequest):
    logger.info(f"Request: {transfer}")
    result = transaksi_controller.transfer(transfer)
    if result["remark"] == "failed":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

# endpoint untuk mengecek mutasi
@app.get("/mutasi/{no_rekening}")
def get_mutasi(no_rekening: str):
    logger.info(f"Request: {no_rekening}")
    result = transaksi_controller.get_mutasi(no_rekening)
    if result["remark"] == "failed":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

if __name__ == "__main__":
    server = Server(
            Config(app="main:app", 
                host="0.0.0.0",
                log_level=LOG_LEVEL
            )
    )
    setup_logging()
    server.run()
