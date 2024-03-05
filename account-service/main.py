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


app = FastAPI() # inisialisasi app

@app.middleware("http")
async def pin_validation_middleware(request: Request, call_next):
    return await pin_validation(request, call_next)

# endpoint untuk daftar akun
@app.post("/daftar")
def create_account(account: AccountRequest):
    logger.info(f"Request: {account}")
    session = get_session() # mendapatkan session
    all_account = crud.get_all_account(session)
    for acc in all_account:
        if acc.nik == account.nik:
            logger.error("NIK sudah terdaftar")
            return_msg = {
                "remark": "failed - NIK sudah terdaftar"
            }
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)
        elif acc.no_hp == account.no_hp:
            logger.error("No HP sudah terdaftar")
            return_msg = {
                "remark": "failed - No HP sudah terdaftar"
            }
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)

    hashed_pin = Hasher.get_password_hash(account.pin)
    new_account = Account(
        nik=account.nik,
        nama=account.nama,
        no_hp=account.no_hp,
        no_rekening=str(random.randint(100000, 999999)),
        saldo=0,
        pin=hashed_pin
    )
    crud.create_account(session, new_account)
    close_session(session)

    return_msg = {
        "remark": "success",
        "data": {
            "no_rekening": new_account.no_rekening,
        }
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=return_msg)

# endpoint untuk tabung - menambah saldo
@app.post("/tabung")
def tabung(transaksi: TransaksiRequest):
    session = get_session()
    account = crud.account_by_no_rekening(session, transaksi.no_rekening)
    if account is None:
        return_msg = {
            "remark": "failed - No Rekening tidak ditemukan"
        }
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=return_msg)
    crud.tambah_saldo(session, transaksi.no_rekening, transaksi.nominal)

    transaksi_record = {
        "tanggal_transaksi": str(datetime.now()),
        "no_rekening_debit": transaksi.no_rekening,
        "no_rekening_kredit": "0",
        "nominal_debit": transaksi.nominal,
        "nominal_kredit": 0
    }
    send_msg = str(transaksi_record)
    send_msg = send_msg.replace("\'", "\"")
    logger.info(f"Publishing message: {send_msg}")
    publish_message(send_msg)

    return_msg = {
        "remark": "success",
        "data": {
            "saldo": account.saldo
        }
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=return_msg)

# endpoint untuk tarik - mengurangi saldo
@app.post("/tarik")
def tarik(transaksi: TransaksiRequest):
    session = get_session()
    account = crud.account_by_no_rekening(session, transaksi.no_rekening)
    if account is None:
        return_msg = {
            "remark": "failed - No Rekening tidak ditemukan"
        }
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=return_msg)
    if account.saldo < transaksi.nominal:
        return_msg = {
            "remark": "failed - Saldo tidak cukup"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=return_msg)
    crud.tarik_saldo(session, transaksi.no_rekening, transaksi.nominal)

    new_transaksi = Transaksi(
        no_rekening=transaksi.no_rekening,
        nominal=transaksi.nominal,
        waktu="now",
        kode_transaksi="d"
    )
    crud.create_transaksi(session, new_transaksi)
    close_session(session)

    return_msg = {
        "remark": "success",
        "data": {
            "saldo": account.saldo
        }
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=return_msg)

# endpoint untuk cek saldo
@app.get("/saldo/{no_rekening}")
def get_saldo(no_rekening: str):
    session = get_session()
    account = crud.account_by_no_rekening(session, no_rekening)
    if account is None:
        return_msg = {
            "remark": "failed - No Rekening tidak ditemukan"
        }
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=return_msg)
    close_session(session)

    return_msg = {
        "remark": "success",
        "data": {
            "saldo": account.saldo
        }
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=return_msg)

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
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=return_msg)

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
