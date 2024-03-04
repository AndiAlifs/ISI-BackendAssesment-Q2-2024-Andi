# import fastapi yang merupakan backend app
from fastapi import FastAPI, Response, status, Request
import time
from fastapi.responses import JSONResponse

# import database yang merupakan model dan akses database
from database.model import Base, engine, Session, Account, Transaksi

# import schemas yang merupakan request dan response
from database.schemas import AccountRequest, TransaksiRequest

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


app = FastAPI() # inisialisasi app


LOG_LEVEL = logging.getLevelName(os.environ.get("LOG_LEVEL", "DEBUG"))
JSON_LOGS = True if os.environ.get("JSON_LOGS", "0") == "1" else False


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LOG_LEVEL)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # configure loguru
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": JSON_LOGS}])

# function untuk mendapatkan session
def get_session():
    session = Session(bind=engine, expire_on_commit=False)
    return session
    
# function untuk menutup session
def close_session(session):
    session.commit()
    session.close()

SKIP_MIDDLEWARE_PATHS = ["/daftar"]

@app.middleware("http")
async def pin_validation(request: Request, call_next):
    if request.url.path not in SKIP_MIDDLEWARE_PATHS:
        pin = request.headers.get("pin")
        if pin is None:
            logger.error("PIN tidak ditemukan")
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"remark": "failed - PIN Tidak Ditemukan"})
        session = get_session()
        account = crud.account_by_no_rekening(session, nomor_rekening)
        if account is None:
            logger.error("No Rekening tidak ditemukan")
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"remark": "failed - No Rekening tidak ditemukan"})
        if not bcrypt.checkpw(pin.encode('utf-8'), account.pin):
            logger.error("PIN salah")
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"remark": "failed - PIN Salah"})
    else:
        response = await call_next(request)
        return response


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

    hashed_pin = bcrypt.hashpw(account.pin.encode('utf-8'), bcrypt.gensalt())
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

    new_transaksi = Transaksi(
        no_rekening=transaksi.no_rekening,
        nominal=transaksi.nominal,
        waktu="now",
        kode_transaksi="c"
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
