import random
from fastapi import FastAPI, status, HTTPException
from fastapi.responses import JSONResponse
from database.model import Account, Transaksi
from database import crud
from database.model import get_session, close_session
from database.schemas import TransaksiRequest
import logging
from loguru import logger
import re
from hashing import Hasher
from controller.account import check_account_existence
from kafka_utils import produce_transaction_message
from datetime import datetime

def tabung(transaksi: TransaksiRequest):
    session = get_session()
    account_exist = check_account_existence(transaksi.no_rekening)
    if account_exist["remark"] == "failed":
        return account_exist

    crud.tambah_saldo(session, transaksi.no_rekening, transaksi.nominal)
    new_transaksi = Transaksi(
        no_rekening=transaksi.no_rekening,
        nominal=transaksi.nominal,
        waktu="now",
        kode_transaksi="c"
    )
    crud.create_transaksi(session, new_transaksi)

    transaksi_record = {
        "tanggal_transaksi": str(datetime.now()),
        "no_rekening_debit": "ATM",
        "no_rekening_kredit": transaksi.no_rekening,
        "nominal_debit": 0,
        "nominal_kredit": transaksi.nominal
    }
    produce_transaction_message(transaksi_record)

    account = crud.account_by_no_rekening(session, transaksi.no_rekening)
    return_msg = {
        "remark": "success",
        "data": {
            "saldo": account.saldo
        }
    }
    close_session(session)
    return return_msg

def tarik(transaksi: TransaksiRequest):
    session = get_session()
    account_exist = check_account_existence(transaksi.no_rekening)
    if account_exist["remark"] == "failed":
        return account_exist

    account = crud.account_by_no_rekening(session, transaksi.no_rekening)
    if account.saldo < transaksi.nominal:
        return_msg = {
            "remark": "failed",
            "data": {
                "reason": "Saldo saat ini {} tidak cukup untuk melakukan transaksi".format(account.saldo)
            }
        }
        return return_msg

    crud.tarik_saldo(session, transaksi.no_rekening, transaksi.nominal)
    new_transaksi = Transaksi(
        no_rekening=transaksi.no_rekening,
        nominal=transaksi.nominal,
        waktu="now",
        kode_transaksi="d"
    )
    crud.create_transaksi(session, new_transaksi)

    transaksi_record = {
        "tanggal_transaksi": str(datetime.now()),
        "no_rekening_debit": transaksi.no_rekening,
        "no_rekening_kredit": "ATM",
        "nominal_debit": transaksi.nominal,
        "nominal_kredit": 0
    }
    produce_transaction_message(transaksi_record)

    close_session(session)
    account = crud.account_by_no_rekening(session, transaksi.no_rekening)
    return_msg = {
        "remark": "success",
        "data": {
            "saldo": account.saldo
        }
    }
    return return_msg