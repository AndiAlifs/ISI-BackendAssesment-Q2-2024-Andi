from fastapi.testclient import TestClient
from main import app, delete_test_data
import random
import pytest
from database.model import Session, Account, Transaksi, engine
import database.crud as crud

session = Session(bind=engine, expire_on_commit=False)

def test_get_all_account():
    accounts = crud.get_all_account(session)
    assert len(accounts) >= 0

def test_create_account():
    new_account = Account(
        nik=str(random.randint(1000000, 9999999)),
        nama="test_case",
        no_hp=str(random.randint(1000000, 9999999)),
        no_rekening=str(random.randint(100000, 999999)),
    )
    account = crud.create_account(session, new_account)
    assert account.no_rekening == new_account.no_rekening

def test_account_by_no_rekening():
    no_rekening = str(random.randint(100000, 999999)),
    new_account = Account(
        nik=str(random.randint(1000000, 9999999)),
        nama="test_case",
        no_hp=str(random.randint(1000000, 9999999)),
        no_rekening=no_rekening,
    )
    crud.create_account(session, new_account)
    account = crud.account_by_no_rekening(session, no_rekening)
    assert account.no_rekening == no_rekening

def test_account_by_no_rekening_failed_not_found():
    no_rekening = str(random.randint(100000, 999999)),
    account = crud.account_by_no_rekening(session, no_rekening)
    assert account == None  

def test_account_by_name():
    nama = "test_case"
    new_account = Account(
        nik=str(random.randint(1000000, 9999999)),
        nama=nama,
        no_hp=str(random.randint(1000000, 9999999)),
        no_rekening=str(random.randint(100000, 999999)),
    )
    crud.create_account(session, new_account)
    accounts = crud.get_accounts_by_name(session, nama)
    assert len(accounts) >= 1
    