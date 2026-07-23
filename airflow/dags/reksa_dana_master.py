"""reksa_dana_master - DAG mingguan: MI, bank kustodian, APERD, fund list, junction.

Jadwal: Minggu 03:00 WIB, saat beban server sumber paling rendah. Data ini
praktis statis (`DataLastUpdate` bank kustodian menunjukkan 2020) - mingguan
jauh lebih sering dari yang dibutuhkan, tapi biayanya murah (~120 call) dan
menjamin perubahan izin/merger/kanal penjualan tertangkap dalam <=7 hari.

Scope: Phase 1 (master MI/bank/APERD), 2 (fund list - fund baru), 8
(junction fund<->APERD).
"""
import pendulum
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

from _common import PROJECT, PY, DEFAULT_ARGS, TRANSFORM_CMD, LOAD_OLTP_CMD, REFRESH_DW_CMD

with DAG(
    "reksa_dana_master",
    schedule="0 3 * * 0",
    start_date=pendulum.datetime(2026, 7, 22, tz="Asia/Jakarta"),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["reksa-dana", "master"],
) as dag:

    scrape_master = BashOperator(
        task_id="scrape_master",
        bash_command=f'cd "{PROJECT}/Data Scraping/src" && {PY} main.py --phases 1,2,8 --force',
    )
    transform = BashOperator(task_id="transform", bash_command=TRANSFORM_CMD)
    load_oltp = BashOperator(task_id="load_oltp", bash_command=LOAD_OLTP_CMD)
    refresh_dw = BashOperator(task_id="refresh_dw", bash_command=REFRESH_DW_CMD)

    scrape_master >> transform >> load_oltp >> refresh_dw
