import random
import logging
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from database.model import Base, engine, Session, Account, Transaksi
from database.schemas import AccountRequest, TransaksiRequest
from datetime import datetime
from loguru import logger

def get_all_account(session):
    logger.info("Fetching all account data")
    all_account = session.query(Account).all()
    return all_account

def account_by_no_rekening(session, no_rekening):
    logger.info(f"Fetching account with no_rekening: {no_rekening}")
    account = session.query(Account).filter(Account.no_rekening == no_rekening).first()
    return account

def get_accounts_by_name(session, nama):
    logger.info(f"Fetching account with name: {nama}")
    accounts = session.query(Account).filter(Account.nama.like(f'%{nama}%')).all()
    return accounts

def create_account(session, NewAccount: Account):
    logger.info(f"Creating new account with data: {NewAccount.to_dict()}")
    session.add(NewAccount)
    return NewAccount

def delete_account(session, delete_account: Account):
    logger.info(f"Deleting account with data: {delete_account.to_dict()}")
    session.delete(delete_account)
    return delete_account

def tambah_saldo(session, no_rekening, jumlah):
    logger.info(f"Adding {jumlah} to account {no_rekening}")
    account = session.query(Account).filter(Account.no_rekening == no_rekening).first()
    account.saldo += jumlah
    return account

def tarik_saldo(session, no_rekening, jumlah):
    logger.info(f"Withdrawing {jumlah} from account {no_rekening}")
    account = session.query(Account).filter(Account.no_rekening == no_rekening).first()
    account.saldo -= jumlah
    return account

def transfer_saldo(session, no_rekening_pengirim, no_rekening_penerima, jumlah):
    logger.info(f"Transferring {jumlah} from account {no_rekening_pengirim} to account {no_rekening_penerima}")
    account_pengirim = session.query(Account).filter(Account.no_rekening == no_rekening_pengirim).first()
    account_penerima = session.query(Account).filter(Account.no_rekening == no_rekening_penerima).first()
    account_pengirim.saldo -= jumlah
    account_penerima.saldo += jumlah
    return account_pengirim, account_penerima

def create_transaksi(session, new_transaksi: Transaksi):
    logger.info(f"Creating new transaction with data: {new_transaksi.to_dict()}")
    session.add(new_transaksi)
    return new_transaksi

def get_all_transaksi_by_no_rekening(session, no_rekening):
    logger.info(f"Fetching all transaction for account {no_rekening}")
    all_transaksi = session.query(Transaksi).filter(Transaksi.no_rekening == no_rekening).all()
    logger.info(f"All transaction for account {no_rekening} fetched with count: {len(all_transaksi)}")
    return all_transaksi

def delete_transaksi(session, delete_transaksi: Transaksi):
    session.delete(delete_transaksi)
    return delete_transaksi
