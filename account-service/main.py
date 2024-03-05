# import fastapi yang merupakan backend app
from fastapi import FastAPI, Response, status, Request
import time
from fastapi.responses import JSONResponse

# import database yang merupakan model dan akses database
from database.model import Base, engine, Session, Account, Transaksi, get_session, close_session

# import schemas yang merupakan request dan response
from database.schemas import AccountRequest, TransaksiRequest, TransferRequest

# import package yang digunakan dalam logic
from datetime import datetime
import random
import database.crud as crud

import os
import logging
import sys
from uvicorn import Config, Server
from loguru import logger

import bcrypt
import uvicorn
import re

from hashing import Hasher
from log_config import setup_logging, LOG_LEVEL
from kafka_utils import publish_message

from middleware import pin_validation

import controller.account as account_controller
import controller.transaksi as transaksi_controller


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
    session = get_session()
    account_pengirim = crud.account_by_no_rekening(session, transfer.no_rekening_asal)
    account_penerima = crud.account_by_no_rekening(session, transfer.no_rekening_tujuan)

    if account_pengirim is None:
        return_msg = {
            "remark": "failed - No Rekening Pengirim tidak ditemukan"
        }
        logger.error("No Rekening {} tidak ditemukan".format(transfer.no_rekening_asal))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)
    if account_penerima is None:
        return_msg = {
            "remark": "failed - No Rekening Penerima tidak ditemukan"
        }
        logger.error("No Rekening {} tidak ditemukan".format(transfer.no_rekening_tujuan))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)
    if account_pengirim.saldo < transfer.nominal:
        return_msg = {
            "remark": "failed - Saldo tidak cukup"
        }
        logger.error("Saldo {} sejumlah {} kurang dari {}".format(transfer.no_rekening_asal, account_pengirim.saldo, transfer.nominal))
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)

    crud.transfer_saldo(session, transfer.no_rekening_asal, transfer.no_rekening_tujuan, transfer.nominal)
    logger.info("Transfer {} ke {} sejumlah {}".format(transfer.no_rekening_asal, transfer.no_rekening_tujuan, transfer.nominal))

    new_transaksi_pengirim = Transaksi(
        no_rekening=transfer.no_rekening_asal,
        nominal=transfer.nominal,
        waktu="now",
        kode_transaksi="t"
    )
    new_transaksi_penerima = Transaksi(
        no_rekening=transfer.no_rekening_tujuan,
        nominal=transfer.nominal,
        waktu="now",
        kode_transaksi="t"
    )
    crud.create_transaksi(session, new_transaksi_pengirim)
    crud.create_transaksi(session, new_transaksi_penerima)
    close_session(session)

    return_msg = {
        "remark": "success",
        "data": {
            "saldo_pengirim": account_pengirim.saldo,
            "saldo_penerima": account_penerima.saldo
        }
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=return_msg)

# endpoint untuk mengecek mutasi
@app.get("/mutasi/{no_rekening}")
def get_mutasi(no_rekening: str):
    session = get_session()
    account = session.query(Account).filter(Account.no_rekening == no_rekening).first()

    if account is None:
        return_msg = {
            "remark": "failed - No Rekening tidak ditemukan"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)

    all_transaksi = session.query(Transaksi).filter(Transaksi.no_rekening == no_rekening).all()
    return_msg = {
        "remark": "success",
        "data": {
            "mutasi": []
        }
    }
    for transaksi in all_transaksi:
        return_msg["data"]["mutasi"].append({
            "waktu": datetime.strftime(transaksi.waktu, '%Y-%m-%d %H:%M:%S'),
            "nominal": transaksi.nominal,
            "kode_transaksi": transaksi.kode_transaksi
        })

    close_session(session)
    return JSONResponse(status_code=status.HTTP_200_OK, content=return_msg)

def delete_test_data():
    session = get_session()
    all_test_account = crud.get_accounts_by_name(session, "test")
    for test_data in all_test_account:
        related_transaksi = crud.get_all_transaksi_by_no_rekening(session, test_data.no_rekening)
        for transaksi in related_transaksi:
            crud.delete_transaksi(session, transaksi)
        crud.delete_account(session, test_data)
    close_session(session)

if __name__ == "__main__":
    server = Server(
            Config(app="main:app", 
                host="0.0.0.0",
                log_level=LOG_LEVEL
            )
    )
    setup_logging()
    server.run()
