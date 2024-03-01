from fastapi.testclient import TestClient
from main import app, delete_test_data
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
        },
    )
    
    response = client.post(
        "/daftar",
        json={
            "nik": nik,
            "nama": "test_case",
            "no_hp": no_hp,
        },
    )
    
    response_json = response.json()
    assert response.status_code == 400
    assert response_json["remark"] == "failed - NIK sudah terdaftar"

def test_create_rekening_failed_no_hp_sama(db_session):
    nik = str(random.randint(1000000, 9999999))
    no_hp = str(random.randint(1000000, 9999999))

    response = client.post(
        "/daftar",
        json={
            "nik": nik,
            "nama": "test_case",
            "no_hp": no_hp,
        },
    )
    
    response = client.post(
        "/daftar",
        json={
            "nik": str(random.randint(1000000, 9999999)),
            "nama": "test_case",
            "no_hp": no_hp,
        },
    )
    
    response_json = response.json()
    assert response.status_code == 400
    assert response_json["remark"] == "failed - No HP sudah terdaftar"

def test_tabung(db_session, nomor_rekening):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 100000,
        },
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
    )

    response = client.post(
        "/tarik",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 50000,
        },
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
    )

    response = client.post(
        "/tarik",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 120000,
        },
    )
    
    response_json = response.json()
    assert response.status_code == 400
    assert response_json["remark"] == "failed - Saldo tidak cukup"

def test_tarik_failed_no_rekening_tidak_ditemukan(db_session):
    nomor_rekening = "123456"

    response = client.post(
        "/tarik",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 120000,
        },
    )
    
    response_json = response.json()
    assert response.status_code == 404
    assert response_json["remark"] == "failed - No Rekening tidak ditemukan"

def test_saldo(db_session, nomor_rekening):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 23000,
        },
    )
    response = client.get(
        "/saldo/" + nomor_rekening
    )
    
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["remark"] == "success"
    assert response_json["data"]["saldo"] == 23000

def test_mutasi_failed_no_rekening_tidak_ditemukan(db_session):
    nomor_rekening = "123456"
    response = client.get(
        "/mutasi/" + nomor_rekening
    )
    
    response_json = response.json()
    assert response.status_code == 404
    assert response_json["remark"] == "failed - No Rekening tidak ditemukan"

def test_mutasi(db_session, nomor_rekening):
    response = client.post(
        "/tabung",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 100000,
        },
    )
    response = client.post(
        "/tarik",
        json={
            "no_rekening": nomor_rekening,
            "nominal": 50000,
        },
    )
    response = client.get(
        "/mutasi/" + nomor_rekening
    )
    
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["remark"] == "success"
    assert len(response_json["data"]["mutasi"]) == 2
