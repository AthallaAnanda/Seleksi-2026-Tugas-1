"""reksa_dana_daily_nav - DAG harian: NAV, performance, ranking, benchmark.

Jadwal: 20:00 WIB, Senin-Jumat (hari bursa). NAV terbit tiap hari bursa
setelah pasar tutup; 20:00 memberi buffer setelah cut-off NAV pasardana.
Tidak jalan Sabtu/Minggu karena tidak ada perdagangan.

Scope: Phase 5 (`GetSnapshot`) saja - endpoint ini membundel NAV + AUM +
Performances + Rankings + Benchmarks dalam SATU call, jadi AUM ikut
ter-refresh sebagai efek samping tanpa perlu dipanggil terpisah.
"""
import pendulum
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

from _common import PROJECT, PY, DEFAULT_ARGS, TRANSFORM_CMD, LOAD_OLTP_CMD, REFRESH_DW_CMD

with DAG(
    "reksa_dana_daily_nav",
    schedule="0 20 * * 1-5",
    start_date=pendulum.datetime(2026, 7, 22, tz="Asia/Jakarta"),
    catchup=False,
    max_active_runs=1,  # scrape ~1520 fund makan waktu ~40 menit, jangan tumpang tindih
    default_args=DEFAULT_ARGS,
    tags=["reksa-dana", "daily"],
) as dag:

    scrape_daily_nav = BashOperator(
        task_id="scrape_daily_nav",
        bash_command=f'cd "{PROJECT}/Data Scraping/src" && {PY} main.py --phases 5 --force',
    )
    transform = BashOperator(task_id="transform", bash_command=TRANSFORM_CMD)
    load_oltp = BashOperator(task_id="load_oltp", bash_command=LOAD_OLTP_CMD)
    refresh_dw = BashOperator(task_id="refresh_dw", bash_command=REFRESH_DW_CMD)

    scrape_daily_nav >> transform >> load_oltp >> refresh_dw
