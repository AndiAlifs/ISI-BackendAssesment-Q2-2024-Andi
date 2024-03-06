from fastapi.testclient import TestClient
from main import app
from database import crud
from database.model import get_session, close_session
import random
import pytest

client = TestClient(app)

@pytest.fixture
def nomor_rekening():
    response = client.post(
        "/daftar",
        json={
            "nik": str(random.randint(1000000, 9999999)),
            "nama": "test_case",
            "no_hp": str(random.randint(1000000, 9999999)),
            "pin": "321123"
        },
    )
    return response.json()["data"]["no_rekening"]

@pytest.fixture
def nomor_rekening_2():
    response = client.post(
        "/daftar",
        json={
            "nik": str(random.randint(1000000, 9999999)),
            "nama": "test_case",
            "no_hp": str(random.randint(1000000, 9999999)),
            "pin": "321123"
        },
    )
    return response.json()["data"]["no_rekening"]

@pytest.fixture
def db_session():
    yield
    delete_test_data()

def test_create_rekening(db_session):
    nik = str(random.randint(1000000, 9999999))
    no_hp = str(random.randint(1000000, 9999999))

    response = client.post(
        "/daftar",
        json={
            "nik": nik,
            "nama": "test_case",
            "no_hp": no_hp,
            "pin": "321123"
        },
    )
    
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["remark"] == "success"

def test_create_rekening_failed_nik_sama(db_session):
    nik = str(random.randint(1000000, 9999999))
    no_hp = str(random.randint(1000000, 9999999))

    response = client.post(
        "/daftar",
        json={
            "nik": nik,
            "nama": "test_case",
            "no_hp": no_hp,
            "pin": "321123"
        },
    )
    
    response = client.post(
        "/daftar",
        json={
            "nik": nik,
            "nama": "test_case",
            "no_hp": no_hp,
            "pin": "321123"
        },
    )
    
    response_json = response.json()
    assert response.status_code == 400
    assert response_json["remark"] == "failed"

def test_create_rekening_failed_no_hp_sama(db_session):
    nik = str(random.randint(1000000, 9999999))
    no_hp = str(random.randint(1000000, 9999999))

    response = client.post(
        "/daftar",
        json={
            "nik": nik,
            "nama": "test_case",
            "no_hp": no_hp,
            "pin": "321123"
        },
    )
    
    response = client.post(
        "/daftar",
        json={
            "nik": str(random.randint(1000000, 9999999)),
            "nama": "test_case",
            "no_hp": no_hp,
            "pin": "321123"
        },
    )
    
    response_json = response.json()
    assert response.status_code == 400
    assert response_json["remark"] == "failed"

def test_tabung(db_session, nomor_rekening):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 100000,
        },
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    assert response_json["remark"] == "success"
    assert response_json["data"]["saldo"] == 100000
    
def test_tarik(db_session, nomor_rekening):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 100000,
        },
        headers={"pin": "321123"}
    )

    response = client.post(
        "/tarik",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 50000,
        },
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["remark"] == "success"
    assert response_json["data"]["saldo"] == 50000

def test_tarik_failed_saldo_kurang(db_session, nomor_rekening):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 100000,
        },
        headers={"pin": "321123"}
    )

    response = client.post(
        "/tarik",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 120000,
        },
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    assert response.status_code == 400
    assert response_json["remark"] == "failed"

def test_tarik_failed_no_rekening_tidak_ditemukan(db_session):
    nomor_rekening = "123456"

    response = client.post(
        "/tarik",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 120000,
        },
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    assert response.status_code == 400
    assert response_json["remark"] == "failed"

def test_saldo(db_session, nomor_rekening):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 23000,
        },
        headers = {"pin": "321123"}
    )
    response = client.get(
        "/saldo/" + nomor_rekening,
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["remark"] == "success"
    assert response_json["data"]["saldo"] == 23000

def test_mutasi_failed_no_rekening_tidak_ditemukan(db_session):
    nomor_rekening = "123456"
    response = client.get(
        "/mutasi/" + nomor_rekening,
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    assert response.status_code == 400
    assert response_json["remark"] == "failed"

def test_mutasi(db_session, nomor_rekening):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 100000,
        },
        headers={"pin": "321123"}
    )
    response = client.post(
        "/tarik",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 50000,
        },
        headers={"pin": "321123"}
    )
    response = client.get(
        "/mutasi/" + nomor_rekening,
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["remark"] == "success"
    assert len(response_json["data"]["mutasi"]) == 2

def test_transfer(db_session, nomor_rekening, nomor_rekening_2):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 120000,
        },
        headers={"pin": "321123"}
    )
    response = client.post(
        "/transfer",
        json={
            "no_rekening_asal": nomor_rekening,
            "no_rekening_tujuan": nomor_rekening_2,
            "nominal": 50000,
        },
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["remark"] == "success"
    assert response_json["data"]["saldo_pengirim"] == 70000
    assert response_json["data"]["saldo_penerima"] == 50000

def test_transfer_fail_saldo_kurang(db_session, nomor_rekening, nomor_rekening_2):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 120000,
        },
        headers={"pin": "321123"}
    )
    response = client.post(
        "/transfer",
        json={
            "no_rekening_asal": nomor_rekening,
            "no_rekening_tujuan": nomor_rekening_2,
            "nominal": 150000,
        },
        headers={"pin": "321123"}
    )
    
    response_json = response.json()
    
    assert response.status_code == 400
    assert response_json["remark"] == "failed"

def delete_test_data():
    session = get_session()
    all_test_account = crud.get_accounts_by_name(session, "test")
    for test_data in all_test_account:
        related_transaksi = crud.get_all_transaksi_by_no_rekening(session, test_data.no_rekening)
        for transaksi in related_transaksi:
            crud.delete_transaksi(session, transaksi)
        crud.delete_account(session, test_data)
    close_session(session)