from database.model import get_session, close_session, Transaksi, Account
from sqlalchemy import text

start_time = "2024-03-05 10:23:55.222"      # buat dalam format "YYYY-MM-DD HH:MM:SS"
end_time = "2024-03-07 10:23:55.222"        # buat dalam format "YYYY-MM-DD HH:MM:SS"

def find_total_transaction(start_time, end_time):
    session = get_session()
    result = session.query(Transaksi).filter(Transaksi.waktu >= start_time).filter(Transaksi.waktu <= end_time).count()
    close_session(session)
    return result

def find_sum_nominal_tarik(start_time, end_time):
    session = get_session()
    sql = "SELECT SUM(nominal) FROM transaksi WHERE waktu between '{}' and '{}' and kode_transaksi = 'd'".format(start_time, end_time)
    result = session.execute(text(sql)).fetchone()[0]
    close_session(session)
    return result

def find_sum_nominal_tabung(start_time, end_time):
    session = get_session()
    sql = "SELECT SUM(nominal) FROM transaksi WHERE waktu between '{}' and '{}' and kode_transaksi = 'c'".format(start_time, end_time)
    result = session.execute(text(sql)).fetchone()[0]
    close_session(session)
    return result

def find_sum_nominal_transfer(start_time, end_time):
    session = get_session()
    sql = "SELECT SUM(nominal) FROM transaksi WHERE waktu between '{}' and '{}' and kode_transaksi = 't'".format(start_time, end_time)
    result = session.execute(text(sql)).fetchone()[0]
    close_session(session)
    return result

if __name__ == "__main__":
    print("============ Recap Data ============")
    print("Start Time: ", start_time)
    print("End Time: ", end_time)
    print("====================================")
    print("Total Transaksi: ".format(find_total_transaction(start_time, end_time)))
    print("Total Penarikan: Rp. ".format(find_sum_nominal_tarik(start_time, end_time)))
    print("Total Penyetoran: Rp. ".format(find_sum_nominal_tabung(start_time, end_time)))
    print("Total Transfer: Rp. ".format(find_sum_nominal_transfer(start_time, end_time)))