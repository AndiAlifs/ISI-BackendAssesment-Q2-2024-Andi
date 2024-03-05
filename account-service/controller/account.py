import random
from fastapi import FastAPI, status, HTTPException
from fastapi.responses import JSONResponse
from database.model import Account
from database import crud
from database.model import get_session, close_session
from database.schemas import AccountRequest
import logging
from loguru import logger
import re
from hashing import Hasher

def create_account(account: AccountRequest):
    session = get_session() # mendapatkan session
    all_account = crud.get_all_account(session)
    for acc in all_account:
        if acc.nik == account.nik:
            logger.error("NIK {} sudah terdaftar".format(account.nik))
            return_msg = {
                "remark": "failed",
                "data": {
                    "reason": "NIK {} sudah terdaftar".format(account.nik),
                }
            }
            return return_msg
        elif acc.no_hp == account.no_hp:
            logger.error("No HP {} sudah terdaftar".format(account.no_hp))
            return_msg = {
                "remark": "failed",
                "data": {
                    "reason": "No HP {} sudah terdaftar".format(account.no_hp),
                }
            }
            return return_msg

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

    logger.info("Akun {} berhasil didaftarkan".format(account.nik))
    return_msg = {
        "remark": "success",
        "data": {
            "no_rekening": new_account.no_rekening
        }
    }
    return return_msg