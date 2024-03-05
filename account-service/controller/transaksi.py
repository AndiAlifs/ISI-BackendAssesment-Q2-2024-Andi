import random
from fastapi import FastAPI, status, HTTPException
from fastapi.responses import JSONResponse
from database.model import Account
from database import crud
from database.model import get_session, close_session
from database.schemas import TransaksiRequest
import logging
from loguru import logger
import re
from hashing import Hasher
from controller.account import check_account_existence
from kafka_utils import publish_message
from datetime import datetime

def tabung(transaksi: TransaksiRequest):
    session = get_session()
    account_exist = check_account_existence(transaksi.no_rekening)
    if account_exist["remark"] == "failed":
        return account_exist

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

    account = crud.account_by_no_rekening(session, transaksi.no_rekening)
    return_msg = {
        "remark": "success",
        "data": {
            "saldo": account.saldo
        }
    }
    close_session(session)
    return return_msg