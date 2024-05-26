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
from middleware import pin_validation

app = FastAPI() # inisialisasi app

@app.middleware("http")
async def pin_validation_middleware(request: Request, call_next):
    return await pin_validation(request, call_next)

@app.post("/daftar")
def create_account(account: AccountRequest):
    logger.info(f"Request: {account}")
    result = account_controller.create_account(account)
    logger.info(f"Response: {result}")
    if result["remark"] == "failed":
        logger.error(f"Failed to create account {account.no_rekening}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

@app.post("/tabung")
def tabung(transaksi: TransaksiRequest):
    logger.info(f"Request: {transaksi}")
    result = transaksi_controller.tabung(transaksi)
    logger.info(f"Response: {result}")
    if result["remark"] == "failed":
        logger.error(f"Failed to deposit {transaksi.nominal} to account {transaksi.no_rekening}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

@app.post("/tarik")
def tarik(transaksi: TransaksiRequest):
    logger.info(f"Request: {transaksi}")
    result = transaksi_controller.tarik(transaksi)
    logger.info(f"Response: {result}")
    if result["remark"] == "failed":
        logger.error(f"Failed to withdraw {transaksi.nominal} from account {transaksi.no_rekening}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

# endpoint untuk cek saldo
@app.get("/saldo/{no_rekening}")
def get_saldo(no_rekening: str):
    logger.info(f"Request: {no_rekening}")
    result = account_controller.check_account_existence(no_rekening)
    logger.info(f"Response: {result}")
    if result["remark"] == "failed":
        logger.error(f"Account {no_rekening} does not exist")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

@app.post("/transfer")
def transfer(transfer: TransferRequest):
    logger.info(f"Request: {transfer}")
    result = transaksi_controller.transfer(transfer)
    logger.info(f"Response: {result}")
    if result["remark"] == "failed":
        logger.error(f"Failed to transfer {transfer.nominal} from account {transfer.no_rekening_pengirim} to account {transfer.no_rekening_penerima}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

# endpoint untuk mengecek mutasi
@app.get("/mutasi/{no_rekening}")
def get_mutasi(no_rekening: str):
    logger.info(f"Request: {no_rekening}")
    result = transaksi_controller.get_mutasi(no_rekening)
    logger.info(f"Response: {result}")
    if result["remark"] == "failed":
        logger.error(f"Account {no_rekening} does not exist")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=result)

if __name__ == "__main__":\
    # in production mode
    server = Server(
            Config(app="main:app", 
                host="0.0.0.0",
                log_level=LOG_LEVEL,
                reload=True
            )
    )
    server.run()

    # in development mode
    # setup_logging()
    # uvicorn.run(
    #     app="main:app",
    #     host="0.0.0.0",
    #     log_level=LOG_LEVEL,
    #     reload=True
    # )
