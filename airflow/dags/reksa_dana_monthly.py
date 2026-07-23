"""reksa_dana_monthly - DAG bulanan: AUM MI, fund class, portofolio, kuartalan.

Jadwal: tanggal 2 tiap bulan, 06:00 WIB. AUM biasanya rilis akhir bulan;
tanggal 2 memberi jeda 1-2 hari supaya data bulan sebelumnya lengkap
terpublikasi.

Scope: Phase 3 (AUM level MI), 4 (fund class per MI), 6 (portofolio
historis), 7 (return kuartalan). TIDAK mengulang Phase 5 (snapshot) -
AUM level fund sudah ter-refresh sebagai efek samping DAG harian
(`reksa_dana_daily_nav`), jadi mengulanginya di sini cuma redundan.
"""
import pendulum
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

from _common import PROJECT, PY, DEFAULT_ARGS, TRANSFORM_CMD, LOAD_OLTP_CMD, REFRESH_DW_CMD

with DAG(
    "reksa_dana_monthly",
    schedule="0 6 2 * *",
    start_date=pendulum.datetime(2026, 7, 22, tz="Asia/Jakarta"),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["reksa-dana", "monthly"],
) as dag:

    scrape_monthly = BashOperator(
        task_id="scrape_monthly",
        bash_command=f'cd "{PROJECT}/Data Scraping/src" && {PY} main.py --phases 3,4,6,7 --force',
    )
    transform = BashOperator(task_id="transform", bash_command=TRANSFORM_CMD)
    load_oltp = BashOperator(task_id="load_oltp", bash_command=LOAD_OLTP_CMD)
    refresh_dw = BashOperator(task_id="refresh_dw", bash_command=REFRESH_DW_CMD)

    scrape_monthly >> transform >> load_oltp >> refresh_dw
