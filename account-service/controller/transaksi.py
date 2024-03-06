import random
from fastapi import FastAPI, status, HTTPException
from fastapi.responses import JSONResponse
from database.model import Account, Transaksi
from database import crud
from database.model import get_session, close_session
from database.schemas import TransaksiRequest, TransferRequest
import logging
from loguru import logger
import re
from utils.hashing import Hasher
from controller.account import check_account_existence
from utils.kafka_utils import produce_transaction_message
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

def get_mutasi(no_rekening: str):
    session = get_session()
    account_exist = check_account_existence(no_rekening)
    if account_exist["remark"] == "failed":
        return account_exist

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
    return return_msg

def transfer(transfer: TransferRequest):
    session = get_session()
    account_pengirim = check_account_existence(transfer.no_rekening_asal)
    if account_pengirim["remark"] == "failed":
        return account_pengirim

    account_penerima = check_account_existence(transfer.no_rekening_tujuan)
    if account_penerima["remark"] == "failed":
        return account_penerima

    account_pengirim = crud.account_by_no_rekening(session, transfer.no_rekening_asal)
    account_penerima = crud.account_by_no_rekening(session, transfer.no_rekening_tujuan)
    if account_pengirim.saldo < transfer.nominal:
        logger.error("Saldo {} sejumlah {} kurang dari {}".format(transfer.no_rekening_asal, account_pengirim.saldo, transfer.nominal))
        return_msg = {
            "remark": "failed",

            "data": {
                "reason": "Saldo {} sejumlah {} kurang dari {}".format(transfer.no_rekening_asal, account_pengirim.saldo, transfer.nominal)
            }
        }
        return return_msg

    crud.transfer_saldo(session, transfer.no_rekening_asal, transfer.no_rekening_tujuan, transfer.nominal)
    logger.info("Transfer {} ke {} sejumlah {}".format(transfer.no_rekening_asal, transfer.no_rekening_tujuan, transfer.nominal))
    new_transaksi = Transaksi(
        no_rekening=transfer.no_rekening_asal,
        nominal=transfer.nominal,
        waktu="now",
        kode_transaksi="t"
    )
    crud.create_transaksi(session, new_transaksi)
    new_transaksi = Transaksi(
        no_rekening=transfer.no_rekening_tujuan,
        nominal=transfer.nominal,
        waktu="now",
        kode_transaksi="t"
    )
    crud.create_transaksi(session, new_transaksi)

    transaksi_record = {
        "tanggal_transaksi": str(datetime.now()),
        "no_rekening_debit": transfer.no_rekening_asal,
        "no_rekening_kredit": transfer.no_rekening_tujuan,
        "nominal_debit": transfer.nominal,
        "nominal_kredit": transfer.nominal,
    }
    produce_transaction_message(transaksi_record)
    
    account_pengirim = crud.account_by_no_rekening(session, transfer.no_rekening_asal)
    account_penerima = crud.account_by_no_rekening(session, transfer.no_rekening_tujuan)
    return_msg = {
        "remark": "success",
        "data": {
            "saldo_pengirim": account_pengirim.saldo,
            "saldo_penerima": account_penerima.saldo
        }
    }
    close_session(session)
    return return_msg
