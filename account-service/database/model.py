# import sqlalchemy yang digunakan untuk menghubungkan aplikasi dengan database postgresql
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# mendapatkan url untuk koneksi ke database postgresql
uri = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
)

# membuat engine untuk koneksi ke database
engine = create_engine(uri)

# membuat session untuk melakukan query ke database
Session = sessionmaker(bind=engine)
session = Session()

# membuat tabel account dan transaksi
Base = declarative_base()

class Account(Base):
    __tablename__ = "account"
    nik = Column(String, primary_key=True)
    nama = Column(String)
    no_hp = Column(String)
    no_rekening = Column(String, nullable=True)
    saldo = Column(Integer, default=0)
    pin = Column(String)

class Transaksi(Base):
    __tablename__ = "transaksi"
    id = Column(Integer, primary_key=True)
    no_rekening = Column(String)
    nominal = Column(Integer)
    waktu = Column(DateTime)
    kode_transaksi = Column(String)

# inisiasi membuat tabel di database
Base.metadata.create_all(engine)
session.close()