# ETL Reksa Dana Indonesia (pasardana.id)

**Seleksi Tahap 2 Asisten Basis Data 2026 - ETL Project**
*Data Scraping, Database Modeling, and Data Storing*

**Author:** R. Athalla Ananda Putra
**NIM:** 18224060

---

## Daftar Isi

1. [Deskripsi Singkat](#1-deskripsi-singkat)
2. [Status Progres](#2-status-progres)
3. [Cara Menjalankan](#3-cara-menjalankan)
4. [Data Scraping: Cara Kerja dan Cara Pakai](#4-data-scraping-cara-kerja-dan-cara-pakai)
5. [Struktur File JSON Hasil Scraper](#5-struktur-file-json-hasil-scraper)
6. [Transform dan Load ke OLTP](#6-transform-dan-load-ke-oltp)
7. [ERD dan Diagram Relasional](#7-erd-dan-diagram-relasional)
8. [Screenshot](#8-screenshot)
9. [Bonus](#9-bonus)
10. [Keterbatasan yang Disadari](#10-keterbatasan-yang-disadari)
11. [Penggunaan AI](#11-penggunaan-ai)
12. [Referensi](#12-referensi)

Dokumen ini adalah README utama untuk submission. Untuk catatan anomali data portofolio lihat `docs/snapshot-anomali.md`.

---

## 1. Deskripsi Singkat

**Topik:** Data NAV historis, portofolio, dan ekosistem reksa dana Indonesia.
**Sumber data:** [pasardana.id](https://pasardana.id) (endpoint REST internal, diakses lewat sesi browser, bukan API publik berkunci).
**DBMS:** PostgreSQL 16, dijalankan lewat Podman/Docker Compose.

### Kenapa topik ini

Reksa dana Indonesia punya struktur data yang kaya relasi: Manajer Investasi (MI) mengelola banyak fund, tiap fund punya kustodian, portofolio bulanan, benchmark, dan jaringan APERD (agen penjual) sendiri. Topik ini belum diangkat di seleksi 2024, dan sumbernya (endpoint internal pasardana.id) berbeda dari portal reksa dana lain yang biasa dipakai. NAV harian dan AUM bulanan juga cocok untuk latihan membangun fact table di data warehouse.

### Ringkasan hasil

- 22 entitas tersimpan di OLTP, total sekitar 514.000 baris.
- Data mencakup sekitar 1.520 fund dari 100 Manajer Investasi, 23 bank kustodian, dan 90 APERD.
- Data warehouse (bonus) sudah dibangun dengan model fact constellation (3 fact table, 4 dimensi).
- Scheduling otomatis (bonus) berjalan lewat Apache Airflow dengan 3 DAG berjadwal berbeda sesuai frekuensi perubahan data di sumber.

---

## 2. Status Progres

| Tahap | Isi | Status |
|---|---|---|
| 0 | Setup lingkungan (venv, Podman, DDL awal) | Selesai |
| 1 | Extract: scraping seluruh endpoint (master, fund, snapshot, portofolio, kuartalan) | Selesai |
| 2 | Transform: preprocessing 21 entitas jadi JSON bersih | Selesai |
| 3 | Load: masuk ke OLTP PostgreSQL | Selesai |
| 4 | Bonus - Data Warehouse (OLAP): skema dan ETL OLTP -> DW | Skema dan load script selesai, data sudah ter-load |
| 5 | Bonus - Scheduling Airflow (3 DAG: harian, bulanan, master) | DAG dibuat dan sudah diuji jalan |
| 6 | Bonus - 3 query optimasi (index/materialized view) | Selesai |
| 7 | Dokumentasi & artefak visual (ERD, diagram relasional, screenshot, export .sql) | Selesai |
| 8 | Review akhir & submission | **[ISI: sudah/belum]** |

> Catatan: tabel ini perlu diperbarui manual sebelum submission final, terutama baris 6-8.

---

## 3. Cara Menjalankan

```bash
# 1. Setup environment Python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Jalankan database (Postgres + pgAdmin)
podman-compose up -d
# atau: docker compose up -d

# 3. Extract (butuh waktu lama, ada resume-check kalau terhenti)
cd "Data Scraping/src"
python main.py

# 4. Transform
python preprocessor.py

# 5. Load ke OLTP
cd "../../Data Storing/src"
python load_data.py
```

Kredensial database ada di `.env` (host, port, nama database, user, password - lihat `.env` yang sudah ada di root proyek, jangan di-commit ke git). Postgres jalan di container `reksadana_pg`, port 5432 di-expose ke host sehingga bisa diakses lewat `psql` langsung atau tool GUI seperti pgAdmin/DBeaver (pgAdmin tersedia di `http://localhost:5050`).

### Menjalankan bonus (Data Warehouse dan scheduling)

```bash
# Data Warehouse: DDL sudah otomatis dibuat oleh docker-compose (schema dw),
# untuk memuat/refresh data jalankan:
podman exec -i reksadana_pg psql -U postgres -d reksadana < "Data Storing/Data Warehouse/src/load_dw.sql"

# Scheduling: DAG Airflow ada di airflow/dags/. Jalankan Airflow standalone
# dari venv terpisah (lihat requirements-nya sendiri), lalu aktifkan
# DAG reksa_dana_daily_nav, reksa_dana_monthly, dan reksa_dana_master
# lewat Airflow UI atau CLI.
```

---

## 4. Data Scraping: Cara Kerja dan Cara Pakai

### Metode

Scraping memakai Playwright untuk membuka sesi browser asli (supaya dapat cookie sesi valid), lalu memanggil endpoint REST internal pasardana.id lewat `page.evaluate(fetch())` di dalam konteks browser tersebut. Tidak ada endpoint publik/API resmi yang dipakai; semua endpoint ditemukan lewat inspeksi DevTools (Network -> Fetch/XHR) dan diakses persis seperti browser normal mengaksesnya.

### Delapan fase scraping

Kode ada di `Data Scraping/src/main.py`, dijalankan berurutan lewat 8 fase:

| Fase | Isi | Kira-kira jumlah call |
|---|---|---|
| 1 | Master data (Manajer Investasi, bank kustodian, APERD) | 4 |
| 2 | Daftar seluruh fund (paginated) | ~10 |
| 3 | AUM bulanan per Manajer Investasi | ~100 |
| 4 | Fund class per Manajer Investasi (grup multi-kelas) | ~100 |
| 5 | Snapshot NAV, AUM, performance, ranking, benchmark per fund | ~1.000 |
| 6 | Portofolio historis per fund (1 call = 12 snapshot bulanan) | ~1.000 |
| 7 | Return kuartalan per fund (5 tahun terakhir) | ~5.000 |
| 8 | Junction fund <-> APERD (agen penjual) | ~10-20 |

### Cara pakai

```bash
cd "Data Scraping/src"

# Jalankan seluruh 8 fase (default)
python main.py

# Jalankan fase tertentu saja, paksa re-fetch walau cache sudah ada
python main.py --phases 5 --force
```

Hasil scraping mentah disimpan di `Data Scraping/raw/` (JSON per endpoint, tidak di-commit ke git karena ukurannya besar dan mudah direproduksi ulang). Ada mekanisme resume-check: kalau proses terhenti di tengah jalan, menjalankan ulang `python main.py` akan melewati fase/file yang sudah selesai, bukan mengulang dari awal.

Setelah scraping mentah selesai, jalankan `python preprocessor.py` untuk menghasilkan JSON bersih di `Data Scraping/data/` (lihat bagian 5 dan 6).

Detail lengkap tiap endpoint (parameter, contoh response) ada di kode `Data Scraping/src/endpoints.py`.

---

## 5. Struktur File JSON Hasil Scraper

Data hasil preprocessing dipisah per entitas (bukan digabung dalam satu file besar), tersimpan di `Data Scraping/data/`. Total 21 file berikut yang di-commit ke git:

| File | Jumlah baris | Field utama |
|---|---:|---|
| `investment_managers.json` | 100 | `manager_id, name, ojk_code, mi_permit_num, address, capital, paid_in_capital, is_active, data_last_update, ...` |
| `manager_personnel.json` | 456 | `manager_id, name, title` |
| `manager_shareholders.json` | 241 | `manager_id, shareholder_name, share_amount` |
| `manager_aum_records.json` | 949 | `manager_id, record_date, aum_value, total_units` |
| `custodian_banks.json` | 23 | `bank_id, name, ojk_code, address, ownership_status, activity_status, is_active, ...` |
| `sales_companies.json` | 90 | `company_id, name, aperd_id, npwp, address, contact_person, ...` |
| `fund_classes.json` | 182 | `class_group_id, base_name` |
| `funds.json` | 1.520 | `fund_id, manager_id, bank_id, class_group_id, name, isin_code, fund_type, currency, is_sharia, is_etf, is_index, ipo_date, official_benchmark, fee/policy fields, ...` |
| `nav_records.json` | 341.175 | `fund_id, record_date, nav_value, class_total_value` |
| `aum_records.json` | 15.462 | `fund_id, record_date, published_date, aum_value, total_units, class_total_value` |
| `asset_categories.json` | 17 | `category_id, name` |
| `securities.json` | 7.275 | `security_id, code, name, security_type, source_stock_id` |
| `portfolio_snapshots.json` | 9.625 | `fund_id, date_based, domestic_allocation_pct, foreign_allocation_pct` |
| `portfolio_allocations.json` | 23.189 | `snapshot_ref [fund_id, date_based], category_id, value_pct` |
| `portfolio_holdings.json` | 87.999 | `snapshot_ref [fund_id, date_based], security_id, value_pct` |
| `fund_performances.json` | 1.309 | `fund_id, period_code, as_of_date, return_pct, std_dev, beta, sharpe_ratio, treynor_ratio, sortino_ratio, cagr, ...` |
| `fund_rankings.json` | 6.071 | `fund_id, period_code, category_code, as_of_date, risk_rank, rating_rank, pasardana_rating, ...` |
| `fund_quarterly_returns.json` | 5.646 | `fund_id, quarter_start, return_pct` |
| `benchmarks.json` | 19 | `benchmark_id, name` |
| `benchmark_data_points.json` | 4.243 | `benchmark_id, record_date, value` |
| `fund_benchmarks.json` | 6.532 | `fund_id, benchmark_id, is_official` |
| `fund_sales_companies.json` | 3.023 | `fund_id, company_id, commission_fee` |

Beberapa catatan struktur:

- `snapshot_ref` pada `portfolio_allocations.json`/`portfolio_holdings.json` adalah pasangan `[fund_id, date_based]`, bukan foreign key langsung ke surrogate key `snapshot_id`. Nilai `snapshot_id` di-generate saat proses load ke database (lihat bagian 6), karena di level JSON belum ada database yang meng-assign surrogate key.
- Field yang bersifat turunan (`daily_return`, `conservative_label`) sengaja **tidak** ditulis di file JSON manapun; keduanya dihasilkan oleh database (view dan generated column, lihat bagian 7).
- Nama field sudah di-snake_case-kan dan tipe datanya sudah diparsing (string rupiah -> integer, persentase string -> float, tanggal -> format ISO `YYYY-MM-DD`), bukan lagi string mentah dari API.

Aturan parsing lengkap ada di kode `Data Scraping/src/preprocessor.py`.

---

## 6. Transform dan Load ke OLTP

### Transform (`Data Scraping/src/preprocessor.py`)

Raw JSON diolah jadi 21 file bersih. Beberapa hal penting yang ditangani di tahap ini:

- Parsing tipe dasar: string rupiah jadi integer, persentase jadi float, tanggal ke format ISO.
- Fund multi-kelas dikelompokkan lewat `FkClassFundId` dari API, bukan parsing nama produk (nama terlalu tidak konsisten formatnya).
- Saham dan obligasi disatukan jadi entitas `security` (supertype), karena keduanya berperan sama sebagai instrumen yang dipegang portofolio.
- Atribut turunan seperti `daily_return` dan `conservative_label` sengaja tidak dihitung di sini karena dijadikan view atau generated column di database.

### Load (`Data Storing/src/load_data.py`)

Loader membaca seluruh file JSON hasil Transform dan memasukkannya ke PostgreSQL, mengikuti urutan dependency FK (master dulu, baru tabel yang bergantung padanya, baru tabel time-series, baru junction yang butuh `snapshot_id`).

Semua tabel di-load pakai `INSERT ... ON CONFLICT` supaya proses ini aman diulang (idempotent). Tabel `manager_personnel` dan `manager_shareholder` yang tidak punya kolom unik alami ditangani beda: sebelum insert, baris lama untuk `manager_id` yang sama dihapus dulu, baru insert ulang.

Hasil akhir: 21 tabel data + tabel turunan terisi, total sekitar 514.000 baris. Sudah diverifikasi:
- Tidak ada foreign key yang menggantung.
- Kolom `conservative_label` ter-generate benar oleh database (contoh: fund ABF Indonesia Bond Index Fund yang punya `is_index=true` otomatis dapat label "Indeks", bukan "Pendapatan Tetap" walau `fund_type`-nya bond).
- Loader dijalankan dua kali berturut-turut dan jumlah baris di semua tabel tetap sama, membuktikan proses memang idempotent.

### Masalah data yang ditemukan dan cara menanganinya

Saat proses load, ditemukan beberapa nilai di data yang secara teknis tidak valid (melanggar batas kolom atau constraint di database). Semuanya berasal dari sumber data, bukan bug di scraper atau transformer.

1. **302 baris di `fund_ranking`** punya semua kolom rank dan rating bernilai 0 sekaligus. Ini sentinel dari API yang artinya "belum ada ranking untuk periode ini", bukan ranking asli. Baris ini dilewati saat load.
2. **Satu fund proteksi** (Batavia Proteksi Maxima 16) punya `min_next_subscription = -1`, kemungkinan sentinel "tidak berlaku". Nilai ini diubah jadi NULL.
3. **Satu fund** (MEGA ASSET MANTAP) punya `red_fee_max_pct = 200`, padahal fee lain di fund yang sama wajar (1-3%). Nilai ini di-null-kan.
4. **Dua pasang kelas fund** berbagi kode ISIN yang sama persis. Tidak bisa dipastikan kelas mana yang kodenya benar, jadi yang disimpan cuma kemunculan pertama, sisanya NULL.
5. **Tiga fund** punya kombinasi persentase kebijakan alokasi (bond/equity/pasar uang) yang totalnya tidak masuk akal, ada yang sampai negatif. Field yang bermasalah di-null-kan per fund.
6. **Tiga baris** di `fund_performance` punya `treynor_ratio` yang melonjak sampai puluhan ribu, jauh di luar rentang wajar. Ini terjadi karena beta mendekati nol sehingga rasio return-dibagi-beta meledak secara matematis. Nilai ini di-null-kan.
7. **Sebagian baris `portfolio_allocation` dan `portfolio_holding`** muncul dua kali untuk kombinasi snapshot dan kategori/instrumen yang sama, dengan nilai persentase berbeda. Setelah dicek, total semua baris di snapshot itu tetap pas 100%, jadi kedua baris memang dua bagian terpisah yang kebetulan dapat kode kategori sama dari sumbernya. Solusinya dijumlahkan, bukan salah satu dibuang.

Ada juga satu temuan menarik soal `asset_category`. Kode kategori 7 dan 9 sama-sama dilabeli "Pasar Uang" di hasil Transform, padahal keduanya muncul bersamaan di beberapa snapshot (jadi jelas dua kategori berbeda, bukan duplikat). Setelah dicek langsung ke raw JSON, kategori 9 di kebanyakan fund sumbernya berlabel "Real Estate", bukan "Pasar Uang". Kategori 9 diberi nama "Real Estate" di database supaya sesuai makna aslinya.

---

## 7. ERD dan Diagram Relasional

### Gambar ERD dan diagram relasional

![ERD](Data%20Storing/design/erd.png)
*Placeholder - taruh gambar ERD (format .png) di `Data Storing/design/erd.png`.*

![Diagram Relasional](Data%20Storing/design/relational_diagram.png)
*Placeholder - taruh gambar diagram relasional (format .png) di `Data Storing/design/relational_diagram.png`.*

Notasi ERD yang dipakai: `[ Entity ]` untuk strong entity, `[[ Entity ]]` untuk weak entity, `< Relasi >` untuk relationship biasa, `<< Relasi >>` untuk identifying relationship, `──` untuk partisipasi partial dan `══` untuk partisipasi total. Atribut kunci ditulis `(*attr*)`, atribut turunan `(~attr~)`.

Kardinalitas dan partisipasi tiap relasi mengikuti diagram ERD di atas, konsisten dengan constraint (`NOT NULL`, `UNIQUE`, `ON DELETE CASCADE`) yang ditegakkan di `Data Storing/src/ddl_oltp.sql`.

### Ringkasan struktur

- **Entitas master (strong):** `investment_manager`, `custodian_bank`, `sales_company`, `mutual_fund`, `fund_class`, `benchmark`, `asset_category`, `security`.
- **Entitas time-series (weak, existence-dependent ke parent):** `manager_personnel`, `manager_shareholder`, `manager_aum_record`, `nav_record`, `aum_record`, `portfolio_snapshot`, `fund_performance`, `fund_ranking`, `fund_quarterly_return`, `benchmark_data_point`.
- **Relasi M:N dengan atribut (junction table di level relasional):** `fund_benchmark` (`is_official`), `fund_sales_company` (`commission_fee`), `portfolio_allocation` (`value_pct`), `portfolio_holding` (`value_pct`).

### Penjelasan translasi ERD ke diagram relasional

Aturan translasi yang diikuti secara konsisten:

1. **Strong entity** menjadi tabel dengan primary key sendiri (`manager_id`, `fund_id`, `bank_id`, dst).
2. **Weak entity** menjadi tabel dengan foreign key `NOT NULL` ke tabel owner-nya (ditegakkan `ON DELETE CASCADE`), dan primary key komposit dari `(foreign_key_owner, partial_key)`, misalnya `nav_record (fund_id, record_date)`.
3. **Relationship 1:M** diwakili oleh foreign key di sisi tabel anak (sisi dengan partisipasi total), bukan tabel terpisah. Contoh: `mutual_fund.manager_id REFERENCES investment_manager`.
4. **Relationship M:N dengan atribut** diwujudkan sebagai tabel junction tersendiri, dengan primary key komposit dari kedua foreign key, dan kolom tambahan untuk atribut relasi itu sendiri. Contoh: `fund_sales_company (fund_id, company_id, commission_fee)`.
5. **Atribut turunan** (`daily_return`, `conservative_label`) tidak diterjemahkan menjadi kolom biasa, melainkan menjadi **VIEW** (`v_nav_return`, `v_benchmark_return`) untuk yang bergantung pada baris lain, atau **GENERATED column** untuk yang bergantung pada kolom lain di baris yang sama.
6. Skema hasil translasi diverifikasi memenuhi 1NF sampai BCNF: tidak ada repeating group, tidak ada partial dependency pada composite key, tidak ada transitive dependency (misal `mutual_fund` tidak menyimpan nama Manajer Investasi, hanya `manager_id`, nama diambil lewat JOIN).

DDL lengkap semua tabel, constraint, view, dan generated column ada di `Data Storing/src/ddl_oltp.sql`.

---

## 8. Screenshot

Screenshot bukti query `SELECT ... FROM ... WHERE` yang berhasil dijalankan terhadap database. Taruh file gambar (.png) di `Data Storing/screenshots/` lalu tampilkan di sini.

![Screenshot query 1](Data%20Storing/screenshots/query-1.png)

![Screenshot query 2](Data%20Storing/screenshots/query-2.png)

![Screenshot query 3](Data%20Storing/screenshots/query-3.png)

**[ISI: tambah caption singkat tiap query di atas kalau perlu, misal query apa yang dijalankan]**

---

## 9. Bonus

Bagian ini opsional sesuai spesifikasi. Isi status sebenarnya sebelum submission.

### 9.1 Data Warehouse

Model: **fact constellation**, 3 fact table berbagi dimensi konform.

```
dim_date, dim_fund (SCD2), dim_manager (SCD2), dim_category, dim_custodian (SCD2)
        |
        +-- fact_nav_daily          (grain: fund x hari)
        +-- fact_aum_monthly        (grain: fund x bulan)
        +-- fact_manager_aum_monthly (grain: manajer investasi x bulan)
```

- `dim_fund`, `dim_manager`, `dim_custodian` memakai **SCD Type 2** (atributnya bisa berubah seiring waktu, mis. fee atau alamat), `dim_date` dan `dim_category` memakai SCD Type 1 (nyaris tidak pernah berubah).
- `daily_return` yang di OLTP hanya berupa VIEW, sengaja **dimaterialisasi** sebagai kolom di `fact_nav_daily` karena DW dioptimalkan untuk agregasi, bukan untuk konsistensi menulis seperti OLTP.
- DDL: `Data Storing/Data Warehouse/src/ddl_dw.sql`. ETL OLTP -> DW: `Data Storing/Data Warehouse/src/load_dw.sql`.

Contoh query analitik yang bisa dijalankan terhadap skema ini. Catatan penting: agregasi atas nilai absolut (`SUM`/`AVG` pada `aum_value`) wajib dipartisi per `currency_code` karena ada fund yang memakai USD, sementara agregasi atas rasio (`daily_return`) aman lintas currency. Join ke `dim_fund`/`dim_manager`/`dim_custodian` wajib lewat `dim_*_key` (bukan natural key seperti `fund_id`), karena dimensi ini SCD Type 2 dan bisa punya banyak baris per entitas:

```sql
-- Volatilitas tahunan per kategori fund
SELECT dc.label,
       COUNT(DISTINCT f.fund_id)        AS n_fund,
       STDDEV(f.daily_return)*SQRT(252) AS ann_volatility,
       AVG(f.daily_return)*252          AS ann_return
FROM dw.fact_nav_daily f
JOIN dw.dim_category dc ON f.category_id = dc.category_id
JOIN dw.dim_date dd     ON f.date_id = dd.date_id
WHERE dd.year = 2026
GROUP BY dc.label
ORDER BY ann_volatility DESC;
```

**Skema (ERD/star schema):**

![ERD/star schema Data Warehouse](Data%20Storing/Data%20Warehouse/design/star_schema.png)

**Screenshot bukti query analitik terhadap Data Warehouse:**

![Screenshot query Data Warehouse](Data%20Storing/Data%20Warehouse/screenshots/query_1.png)

**[ISI: `Data Storing/Data Warehouse/export/dw_export.sql` masih belum ada - jalankan `pg_dump` sesuai instruksi di `Data Storing/Data Warehouse/export/README.md` sebelum submission]**

### 9.2 Automated Scheduling

Bonus: Apache Airflow, 3 DAG dengan jadwal berbeda sesuai frekuensi perubahan data aktual di sumber, dibuktikan lewat field timestamp di response API (contoh: NAV punya `LastUpdate` yang berubah tiap hari bursa, sementara data Manajer Investasi punya `DataLastUpdate` yang terakhir berubah bertahun-tahun lalu).

| DAG | Jadwal (cron) | Cakupan |
|---|---|---|
| `reksa_dana_daily_nav` | `0 20 * * 1-5` (tiap hari bursa, 20:00 WIB) | NAV, performance, ranking, benchmark |
| `reksa_dana_monthly` | `0 6 2 * *` (tanggal 2 tiap bulan) | AUM fund, AUM MI, portofolio, security baru, return kuartalan |
| `reksa_dana_master` | `0 3 * * 0` (Minggu dini hari) | Manajer Investasi, bank kustodian, APERD, detail fund, fund class |

Kode DAG ada di `airflow/dags/`. Setiap load memakai `ON CONFLICT ... DO NOTHING` untuk tabel time-series (`nav_record`, `aum_record`, `portfolio_snapshot`, dsb, karena baris lama tidak pernah berubah, cukup ditambah) dan `ON CONFLICT ... DO UPDATE` untuk tabel master (`investment_manager`, `mutual_fund`, `custodian_bank`, karena atributnya bisa berubah seperti fee atau alamat), supaya scheduling berkala tidak menghasilkan duplikasi data.

**Bukti scheduling** (perbedaan `scraped_at` antar batch, membuktikan data di-update berkala tanpa redundansi baris):

```sql
SELECT record_date,
       COUNT(*)        AS jumlah_fund,
       MIN(scraped_at) AS batch_mulai,
       MAX(scraped_at) AS batch_selesai
FROM nav_record
GROUP BY record_date
ORDER BY record_date DESC
LIMIT 10;
```

Hasil aktual dari database yang sedang berjalan (dua run DAG `reksa_dana_daily_nav` berbeda: `scheduled__2026-07-22T13:00:00+00:00` dan `manual__2026-07-23T08:54:41`, lihat `airflow/logs/dag_id=reksa_dana_daily_nav/`):

```
 record_date | jumlah_fund |          batch_mulai          |         batch_selesai
-------------+-------------+-------------------------------+-------------------------------
 2026-07-22  |        1475 | 2026-07-23 09:43:00.774153+00 | 2026-07-23 09:43:00.774153+00
 2026-07-21  |        1476 | 2026-07-23 09:43:00.774153+00 | 2026-07-23 09:43:00.774153+00
 2026-07-20  |        1476 | 2026-07-23 09:43:00.774153+00 | 2026-07-23 09:43:00.774153+00
 2026-07-17  |        1476 | 2026-07-23 08:06:30.684527+00 | 2026-07-23 09:43:00.774153+00
 2026-07-16  |        1478 | 2026-07-23 08:06:30.684527+00 | 2026-07-23 08:06:30.684527+00
 2026-07-15  |        1483 | 2026-07-23 08:06:30.684527+00 | 2026-07-23 08:06:30.684527+00
```

Cara baca hasil ini:
- Baris `2026-07-20` sampai `2026-07-22` cuma dibuat oleh batch kedua (`batch_mulai` = `batch_selesai` = `09:43:00`) - ini tanggal NAV baru yang belum ada saat batch pertama jalan, jadi murni ditambahkan, bukan ditimpa.
- Baris `2026-07-17` punya `batch_mulai` (`08:06:30`, dari batch pertama) berbeda dari `batch_selesai` (`09:43:00`, dari batch kedua) - artinya sebagian fund untuk tanggal itu memang sudah masuk di batch pertama, dan batch kedua cuma menambah fund yang sebelumnya belum tercatat (`ON CONFLICT (fund_id, record_date) DO NOTHING`), bukan menduplikasi baris yang sudah ada.
- `jumlah_fund` per tanggal tidak pernah melonjak dua kali lipat meski DAG sudah dijalankan lebih dari sekali, membuktikan tidak ada redundansi data.

**[ISI: kalau mau, tambahkan screenshot dari query bukti scheduling di atas]**

### 9.3 Query Optimasi (3 query)

Tiga query dioptimasi dengan `EXPLAIN ANALYZE` sebelum vs sesudah, output identik, waktu lebih cepat. Sesuai spesifikasi, seluruh query optimasi dikumpulkan dalam folder tersendiri di root repo bernama `Query Optimasi/`, bukan di dalam `Data Storing/`. Seluruh query ada dalam satu file `Query Optimasi/query_optimasi.sql`, dengan komentar SQL yang menjelaskan fungsi tiap query (index composite untuk NAV terbaru per fund, index untuk lookup instrumen di portofolio, dan materialized view untuk dashboard NAV+return).

**Bukti optimasi 1 - index NAV terbaru per fund:**

![Bukti optimasi 1](Query%20Optimasi/optimasi-1.png)

**Bukti optimasi 2 - index lookup instrumen di portofolio:**

![Bukti optimasi 2](Query%20Optimasi/optimasi-2.png)

Catatan: pada screenshot di atas, index `idx_phold_security` kebetulan sudah ada dari percobaan sebelumnya saat query "SEBELUM" dijalankan, sehingga kedua hasil di screenshot sama-sama memakai index (7.174 ms vs 6.976 ms) dan tidak menunjukkan kontras. Angka pembanding yang valid (index benar-benar di-drop dulu sebelum mengukur baseline) ada di tabel ringkasan di bawah.

**Bukti optimasi 3 - materialized view dashboard NAV+return:**

![Bukti optimasi 3](Query%20Optimasi/optimasi-3.png)

**Ringkasan hasil:**

| # | Optimasi | Sebelum | Sesudah | Perubahan plan |
|---|---|---:|---:|---|
| 1 | Index `idx_nav_fund_date` (fund_id, record_date DESC) | 176.9 ms | 64.8 ms (~2.7x) | `Incremental Sort` -> `Index Scan` langsung tanpa sort |
| 2 | Index `idx_phold_security` (security_id) | 9.1 ms | 4.5 ms (~2x) | `Index Scan` di kolom yang salah urutan (`snapshot_id, security_id`) -> `Bitmap Index Scan` langsung di `security_id` |
| 3 | Materialized view `mv_fund_latest_nav` | 420.5 ms | 0.344 ms (~1.200x) | `WindowAgg` (hitung ulang `LAG()` tiap query) -> `Index Scan` langsung baca hasil tersimpan |

Ketiganya output identik dengan query sebelum optimasi (jumlah baris dan isi sama, cuma jalur eksekusinya beda), diverifikasi lewat query `SELECT COUNT(*), MD5(...)` di akhir `query_optimasi.sql`.

---

## 10. Keterbatasan yang Disadari

Beberapa hal sengaja tidak ditutup karena scope tugas ini adalah pemodelan basis data, bukan sistem produksi:

- **Tidak ada penanganan revisi data sumber.** Kalau pasardana merevisi NAV historis setelah proses scrape, model ini tidak akan menangkap revisi itu di OLTP (di DW, riwayat perubahan atribut dimensi ditangkap lewat SCD Type 2).
- **Tidak ada pelacakan siklus hidup fund**, sehingga analisis yang hanya mengambil fund aktif berpotensi bias (survivorship bias: fund yang performanya jelek cenderung lebih dulu tutup atau merger).
- **Sebagian snapshot portofolio totalnya tidak persis 100%.** Ini murni masalah data dari sumbernya sendiri, bukan bug di pipeline. Detail lengkap ada di `docs/snapshot-anomali.md`.

Sebagian celah di atas ditutup lewat mekanisme lain: tabel `audit_log` (trigger di OLTP) mencatat perubahan pada data master, dan SCD Type 2 di Data Warehouse (bagian 9.1) menyimpan riwayat atribut dimensi dari waktu ke waktu.

---

## 11. Penggunaan AI

Spesifikasi mewajibkan penjelasan detail bila menggunakan AI dalam pengerjaan tugas ini. Berikut penjelasannya sesuai keempat poin yang diminta.

### 1. Bagian yang dibantu AI

- Penulisan **script kode** (Python untuk scraper, preprocessor, loader, DAG Airflow) dan **query/DDL SQL** (skema OLTP, skema Data Warehouse, query optimasi). AI dipakai untuk menerjemahkan rancangan yang sudah dibuat sendiri menjadi kode, mempercepat penulisan boilerplate, dan membantu debugging.
- Penyusunan dokumentasi, termasuk README ini dan catatan teknis di `docs/`.

### 2. Bagian yang tetap dikerjakan sendiri

- **Perancangan desain**: ERD, skema relasional, keputusan normalisasi, dan keputusan desain database lainnya.
- **Riset endpoint API**: pengecekan endpoint `pasardana.id` satu per satu secara manual lewat DevTools (Network tab), termasuk menentukan parameter, struktur response, dan endpoint mana yang perlu/tidak perlu dipakai.
- **Desain database** secara keseluruhan (pemodelan entitas, kardinalitas, partisipasi, pemilihan atribut turunan vs disimpan, dsb) - AI membantu menuliskan hasilnya ke kode/DDL, tapi keputusan desainnya sendiri.

### 3. Refleksi penggunaan AI

**[ISI: tulis refleksi personal, misalnya: bagian mana yang benar-benar menghemat waktu, apakah ada saran/kode dari AI yang ternyata salah atau perlu dikoreksi setelah dicek ke data asli, apa yang dipelajari dari proses membagi kerja desain (manual) vs implementasi (dibantu AI) seperti ini]**

### 4. Detail lain

- Tool AI yang dipakai: **[ISI: nama tool/model, misalnya Claude Code]**
- Perkiraan porsi pekerjaan yang melibatkan AI: **[ISI: mis. sebagian besar implementasi kode dan SQL, sementara seluruh proses desain/riset dikerjakan manual]**
- **[ISI: detail relevan lainnya bila ada]**

Catatan: bagian ini **wajib** ada isinya, bukan boleh dikosongkan. Peserta yang terindikasi memakai AI tanpa menuliskan bagian ini akan dikenakan sanksi pengurangan nilai.

---

## 12. Referensi

- Sumber data: [pasardana.id](https://pasardana.id)
- [Playwright](https://playwright.dev/python/) untuk browser automation dan session handling.
- [pandas](https://pandas.pydata.org/) untuk transformasi data.
- [psycopg2](https://www.psycopg.org/) untuk koneksi PostgreSQL.
- PostgreSQL 16, dijalankan lewat Podman/Docker Compose.
- Apache Airflow untuk automated scheduling (bonus).

**[ISI: tambah referensi lain yang benar-benar dipakai, misal artikel/dokumentasi yang dirujuk saat merancang ERD atau data warehouse]**
