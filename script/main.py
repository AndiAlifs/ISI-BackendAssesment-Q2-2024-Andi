from database.model import get_session, close_session, Transaksi, Account
from sqlalchemy import text

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

def print_recap(start_time, end_time):
    print(" Recap Data ".center(42, "="))
    print("Start Time: {:>30}".format(start_time))
    print("End Time: {:>32}".format(end_time))
    print("==========================================")
    print("Total Transaksi: {:>25}".format(find_total_transaction(start_time, end_time)))
    print("Total Penarikan: {:>25}".format(str("Rp. " + str(find_sum_nominal_tarik(start_time, end_time)))))
    print("Total Penyetoran: {:>24}".format(str("Rp. " + str(find_sum_nominal_tabung(start_time, end_time)))))
    print("Total Transfer: {:>26}".format(str("Rp. " + str(find_sum_nominal_transfer(start_time, end_time)))))

if __name__ == "__main__":
    start_time = "2024-03-01 10:23:55.222"      # buat dalam format "YYYY-MM-DD HH:MM:SS"
    end_time = "2024-03-07 10:23:55.222"        # buat dalam format "YYYY-MM-DD HH:MM:SS"
    print_recap(start_time, end_time)