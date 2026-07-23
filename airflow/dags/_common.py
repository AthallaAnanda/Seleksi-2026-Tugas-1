"""_common.py: konstanta bersama untuk 3 DAG reksa dana.

Bukan DAG (Airflow tidak akan memuatnya sebagai DAG karena tidak ada
objek DAG() di module-level), cuma modul konfigurasi yang di-import.
"""
from datetime import timedelta
from pathlib import Path

# Root proyek - 2 level di atas airflow/dags/
PROJECT = str(Path(__file__).resolve().parent.parent.parent)
PY = f'{PROJECT}/.venv/bin/python'  # venv UTAMA (bukan venv Airflow) - lihat KD Tahap 6

DEFAULT_ARGS = {
    "owner": "18224060",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

# Task yang identik di ketiga DAG: transform (preprocessor.py penuh),
# load_oltp (load_data.py penuh), refresh_dw (load_dw.sql penuh).
# Dipanggil penuh, bukan granular per-tabel - sudah terbukti idempoten &
# cepat (preprocessor ~2 detik, load_data.py ~7 detik, load_dw.sql <1 detik),
# jadi kesederhanaan menang atas optimasi prematur.
TRANSFORM_CMD = f'cd "{PROJECT}/Data Scraping/src" && {PY} preprocessor.py'
LOAD_OLTP_CMD = f'cd "{PROJECT}/Data Storing/src" && {PY} load_data.py'
REFRESH_DW_CMD = (
    f'podman exec -i reksadana_pg psql -U postgres -d reksadana '
    f'< "{PROJECT}/Data Storing/Data Warehouse/src/load_dw.sql"'
)
