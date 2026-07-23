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

---

## 1. Deskripsi Singkat

**Topik:** Data NAV historis, portofolio, dan ekosistem reksa dana Indonesia.
**Sumber data:** [pasardana.id](https://pasardana.id), diakses melalui endpoint REST internal lewat sesi browser, bukan melalui API publik berkunci.
**DBMS:** PostgreSQL 16, dijalankan melalui Podman/Docker Compose.

### Alasan pemilihan topik

Reksa dana Indonesia memiliki struktur data yang kaya akan relasi. Satu Manajer Investasi (MI) mengelola banyak fund, setiap fund memiliki bank kustodian, portofolio bulanan, benchmark, serta jaringan APERD (agen penjual efek reksa dana) tersendiri. Topik ini belum pernah diangkat pada seleksi 2024, dan sumber datanya, yaitu endpoint internal pasardana.id, berbeda dari portal reksa dana lain yang umum digunakan. Selain itu, ketersediaan NAV harian dan AUM bulanan menjadikan topik ini sesuai untuk membangun fact table pada data warehouse.

### Ringkasan

- 21 entitas tersimpan pada OLTP dengan total sekitar 514.000 baris.
- Data mencakup sekitar 1.520 fund dari 100 Manajer Investasi, 23 bank kustodian, dan 90 APERD.
- Data warehouse (bonus) dibangun dengan model fact constellation, terdiri atas 3 fact table dan 5 dimensi konform.
- Automated scheduling (bonus) berjalan melalui Apache Airflow dengan 3 DAG berjadwal berbeda, disesuaikan dengan frekuensi perubahan data pada sumber.

---

## 2. Status Progres

| Tahap | Isi | Status |
|---|---|---|
| 0 | Setup lingkungan (venv, Podman, DDL awal) | Selesai |
| 1 | Extract: scraping seluruh endpoint (master, fund, snapshot, portofolio, kuartalan) | Selesai |
| 2 | Transform: preprocessing 21 entitas menjadi JSON bersih | Selesai |
| 3 | Load: pemuatan data ke OLTP PostgreSQL | Selesai |
| 4 | Bonus - Data Warehouse (OLAP): skema dan ETL OLTP ke DW | Selesai |
| 5 | Bonus - Automated scheduling Airflow (3 DAG: harian, bulanan, master) | Selesai |
| 6 | Bonus - 3 query optimasi (index dan materialized view) | Selesai |
| 7 | Dokumentasi dan artefak visual (ERD, diagram relasional, screenshot, export .sql) | Selesai |
| 8 | Review akhir dan submission | Selesai |

---

## 3. Cara Menjalankan

```bash
# 1. Menyiapkan environment Python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Menjalankan database (Postgres dan pgAdmin)
podman-compose up -d
# atau: docker compose up -d

# 3. Extract (memerlukan waktu cukup lama, tersedia resume-check apabila terhenti)
cd "Data Scraping/src"
python main.py

# 4. Transform
python preprocessor.py

# 5. Load ke OLTP
cd "../../Data Storing/src"
python load_data.py
```

Kredensial database tersimpan pada berkas `.env` di root proyek (host, port, nama database, user, password) dan tidak di-commit ke git. PostgreSQL berjalan pada container `reksadana_pg` dengan port 5432 yang di-expose ke host, sehingga dapat diakses melalui `psql` maupun tool GUI seperti pgAdmin atau DBeaver. pgAdmin tersedia pada `http://localhost:5050`.

### Menjalankan bonus (Data Warehouse dan scheduling)

```bash
# Data Warehouse: DDL schema dw dibuat otomatis oleh docker-compose.
# Untuk memuat atau me-refresh data, jalankan:
podman exec -i reksadana_pg psql -U postgres -d reksadana < "Data Storing/Data Warehouse/src/load_dw.sql"

# Scheduling: DAG Airflow tersedia pada airflow/dags/. Jalankan Airflow standalone
# dari venv terpisah, kemudian aktifkan DAG reksa_dana_daily_nav,
# reksa_dana_monthly, dan reksa_dana_master melalui Airflow UI atau CLI.
```

---

## 4. Data Scraping
### Metode

Scraping dilakukan menggunakan Playwright untuk membuka sesi browser asli sehingga memperoleh cookie sesi yang valid, kemudian memanggil endpoint REST internal pasardana.id melalui `page.evaluate(fetch())` di dalam konteks browser tersebut. Tidak ada API resmi berkunci yang digunakan. Seluruh endpoint ditemukan melalui inspeksi DevTools (tab Network, Fetch/XHR) dan diakses sebagaimana browser normal mengaksesnya.

### Delapan fase scraping

Kode utama tersedia pada `Data Scraping/src/main.py` dan dijalankan berurutan melalui delapan fase berikut.

| Fase | Isi | Perkiraan jumlah call |
|---|---|---|
| 1 | Master data (Manajer Investasi, bank kustodian, APERD) | 4 |
| 2 | Daftar seluruh fund (paginated) | ~10 |
| 3 | AUM bulanan per Manajer Investasi | ~100 |
| 4 | Fund class per Manajer Investasi (grup multi-kelas) | ~100 |
| 5 | Snapshot NAV, AUM, performance, ranking, benchmark per fund | ~1.000 |
| 6 | Portofolio historis per fund (satu call memuat 12 snapshot bulanan) | ~1.000 |
| 7 | Return kuartalan per fund (lima tahun terakhir) | ~5.000 |
| 8 | Junction fund dengan APERD (agen penjual) | ~10-20 |

### Cara pakai

```bash
cd "Data Scraping/src"

# Menjalankan seluruh delapan fase (perilaku default)
python main.py

# Menjalankan fase tertentu saja, dengan pemaksaan re-fetch meskipun cache tersedia
python main.py --phases 5 --force
```

Hasil scraping mentah tersimpan pada `Data Scraping/raw/` dalam bentuk JSON per endpoint, dan tidak di-commit ke git karena berukuran besar serta mudah direproduksi ulang. Tersedia mekanisme resume-check: apabila proses terhenti di tengah jalan, menjalankan ulang `python main.py` akan melewati fase atau berkas yang telah selesai, bukan mengulang dari awal.

Setelah scraping mentah selesai, jalankan `python preprocessor.py` untuk menghasilkan JSON bersih pada `Data Scraping/data/` (lihat bagian 5 dan 6). Detail tiap endpoint, termasuk parameter dan struktur response, tersedia pada kode `Data Scraping/src/endpoints.py`.

---

## 5. Struktur File JSON Hasil Scraper

Data hasil preprocessing dipisah per entitas, tidak digabung dalam satu berkas besar, dan tersimpan pada `Data Scraping/data/`. Terdapat 21 berkas berikut yang di-commit ke git.

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

Beberapa catatan penting mengenai struktur berkas di atas.

- Field `snapshot_ref` pada `portfolio_allocations.json` dan `portfolio_holdings.json` berupa pasangan `[fund_id, date_based]`, bukan foreign key langsung ke surrogate key `snapshot_id`. Nilai `snapshot_id` dihasilkan saat proses load ke database (lihat bagian 6), karena pada tingkat JSON belum ada database yang memberikan surrogate key.
- Atribut turunan (`daily_return` dan `conservative_label`) sengaja tidak ditulis pada berkas JSON manapun, karena keduanya dihasilkan oleh database melalui view dan generated column (lihat bagian 7).
- Nama field telah dinormalkan menjadi snake_case dan tipe datanya telah diparsing (string rupiah menjadi integer, persentase menjadi float, tanggal menjadi format ISO `YYYY-MM-DD`), tidak lagi berupa string mentah dari API.

Aturan parsing selengkapnya tersedia pada kode `Data Scraping/src/preprocessor.py`.

---

## 6. Transform dan Load ke OLTP

### Transform (`Data Scraping/src/preprocessor.py`)

Raw JSON diolah menjadi 21 berkas bersih. Beberapa hal penting yang ditangani pada tahap ini antara lain:

- Parsing tipe dasar, yaitu string rupiah menjadi integer, persentase menjadi float, dan tanggal menjadi format ISO.
- Pengelompokan fund multi-kelas melalui `FkClassFundId` dari API, bukan melalui parsing nama produk, karena format nama tidak konsisten.
- Penyatuan saham dan obligasi menjadi entitas `security` sebagai supertype, karena keduanya berperan sama sebagai instrumen yang dipegang portofolio.
- Atribut turunan seperti `daily_return` dan `conservative_label` tidak dihitung pada tahap ini, karena akan direalisasikan sebagai view atau generated column pada database.

### Load (`Data Storing/src/load_data.py`)

Loader membaca seluruh berkas JSON hasil Transform dan memasukkannya ke PostgreSQL sesuai urutan dependensi foreign key, yaitu tabel master terlebih dahulu, kemudian tabel yang bergantung padanya, dilanjutkan tabel time-series, dan terakhir tabel junction yang membutuhkan `snapshot_id`.

Seluruh tabel dimuat menggunakan `INSERT ... ON CONFLICT` agar proses aman diulang (idempotent). Tabel `manager_personnel` dan `manager_shareholder` yang tidak memiliki kolom unik alami ditangani secara berbeda: sebelum insert, baris lama untuk `manager_id` yang sama dihapus terlebih dahulu, kemudian dimasukkan ulang.

Hasil akhirnya adalah 21 tabel data beserta tabel turunan yang terisi dengan total sekitar 514.000 baris. Proses ini telah diverifikasi sebagai berikut:

- Tidak terdapat foreign key yang menggantung.
- Kolom `conservative_label` dihasilkan dengan benar oleh database. Sebagai contoh, fund ABF Indonesia Bond Index Fund yang memiliki `is_index=true` secara otomatis memperoleh label "Indeks", bukan "Pendapatan Tetap", meskipun `fund_type`-nya adalah bond.
- Loader dijalankan dua kali berturut-turut dan jumlah baris pada seluruh tabel tetap sama, yang membuktikan bahwa proses memang idempotent.

### Masalah data yang ditemukan dan penanganannya

Selama proses load ditemukan sejumlah nilai yang secara teknis tidak valid karena melanggar batas kolom atau constraint pada database. Seluruhnya berasal dari sumber data, bukan akibat kesalahan pada scraper maupun transformer.

1. **302 baris pada `fund_ranking`** memiliki seluruh kolom rank dan rating bernilai 0 secara bersamaan. Nilai ini merupakan sentinel dari API yang berarti "belum ada ranking untuk periode tersebut", bukan ranking sesungguhnya, sehingga baris ini dilewati saat load.
2. **Satu fund proteksi** (Batavia Proteksi Maxima 16) memiliki `min_next_subscription = -1`, yang kemungkinan besar merupakan sentinel "tidak berlaku". Nilai ini diubah menjadi NULL.
3. **Satu fund** (MEGA ASSET MANTAP) memiliki `red_fee_max_pct = 200`, sementara fee lain pada fund yang sama berada pada kisaran wajar (1-3%). Nilai ini di-null-kan.
4. **Dua pasang kelas fund** berbagi kode ISIN yang sama persis. Karena tidak dapat dipastikan kelas mana yang kodenya benar, hanya kemunculan pertama yang disimpan, sedangkan sisanya di-null-kan.
5. **Tiga fund** memiliki kombinasi persentase kebijakan alokasi (bond, equity, pasar uang) yang totalnya tidak wajar, bahkan sebagian bernilai negatif. Field yang bermasalah di-null-kan per fund.
6. **Tiga baris** pada `fund_performance` memiliki `treynor_ratio` yang melonjak hingga puluhan ribu, jauh di luar rentang wajar. Hal ini terjadi karena nilai beta mendekati nol sehingga rasio return dibagi beta membesar secara matematis. Nilai ini di-null-kan.
7. **Sebagian baris `portfolio_allocation` dan `portfolio_holding`** muncul dua kali untuk kombinasi snapshot dan kategori atau instrumen yang sama, tetapi dengan nilai persentase berbeda. Setelah diperiksa, total seluruh baris pada snapshot tersebut tetap tepat 100%, sehingga kedua baris memang merupakan dua bagian terpisah yang kebetulan memperoleh kode kategori sama dari sumbernya. Penanganannya adalah menjumlahkan keduanya, bukan membuang salah satu.

Terdapat pula satu temuan menarik terkait `asset_category`. Kode kategori 7 dan 9 sama-sama berlabel "Pasar Uang" pada hasil Transform, padahal keduanya muncul bersamaan pada beberapa snapshot sehingga jelas merupakan dua kategori berbeda, bukan duplikat. Setelah diperiksa langsung ke raw JSON, kategori 9 pada sebagian besar fund sumbernya justru berlabel "Real Estate". Oleh karena itu, kategori 9 diberi nama "Real Estate" pada database agar sesuai dengan makna aslinya.

---

## 7. ERD dan Diagram Relasional

### Gambar ERD dan diagram relasional

![ERD](Data%20Storing/design/erd.png)

![Diagram Relasional](Data%20Storing/design/relational_diagram.png)

Kardinalitas dan partisipasi tiap relasi mengikuti diagram ERD di atas dan konsisten dengan constraint (`NOT NULL`, `UNIQUE`, `ON DELETE CASCADE`) yang ditegakkan pada `Data Storing/src/ddl_oltp.sql`.

### Ringkasan struktur

- **Entitas master (strong):** `investment_manager`, `custodian_bank`, `sales_company`, `mutual_fund`, `fund_class`, `benchmark`, `asset_category`, `security`.
- **Entitas time-series (weak, bergantung keberadaan pada parent):** `manager_aum_record`, `nav_record`, `aum_record`, `portfolio_snapshot`, `fund_performance`, `fund_ranking`, `fund_quarterly_return`, `benchmark_data_point`. Seluruhnya memiliki partial key yang andal (misalnya `record_date`) untuk membedakan baris di dalam satu owner.
- **Entitas dengan surrogate ID (bukan weak entity):** `manager_personnel` dan `manager_shareholder`. Keduanya bergantung pada `investment_manager`, tetapi atribut alaminya (`name`, `title`, `shareholder_name`) tidak cukup unik untuk membentuk partial key yang andal, sehingga tidak dimodelkan sebagai weak entity. Sebagai gantinya, keduanya diberi surrogate ID sendiri sebagai primary key pada ERD.
- **Relasi M:N dengan atribut (tabel junction pada tingkat relasional):** `fund_benchmark` (`is_official`), `fund_sales_company` (`commission_fee`), `portfolio_allocation` (`value_pct`), `portfolio_holding` (`value_pct`).

### Penjelasan translasi ERD menjadi diagram relasional

Translasi dilakukan mengikuti aturan berikut secara konsisten.

1. **Strong entity** menjadi tabel dengan primary key tersendiri (`manager_id`, `fund_id`, `bank_id`, dan seterusnya).
2. **Weak entity** menjadi tabel dengan foreign key `NOT NULL` ke tabel owner-nya (ditegakkan melalui `ON DELETE CASCADE`) dan primary key komposit berbentuk `(foreign_key_owner, partial_key)`, misalnya `nav_record (fund_id, record_date)`.
3. **Relasi 1:M** diwakili oleh foreign key pada sisi tabel anak (sisi dengan partisipasi total), bukan tabel terpisah. Sebagai contoh, `mutual_fund.manager_id REFERENCES investment_manager`.
4. **Relasi M:N dengan atribut** direalisasikan sebagai tabel junction tersendiri dengan primary key komposit dari kedua foreign key, ditambah kolom untuk atribut relasi itu sendiri. Sebagai contoh, `fund_sales_company (fund_id, company_id, commission_fee)`.
5. **Atribut turunan** (`daily_return`, `conservative_label`) tidak diterjemahkan menjadi kolom biasa, melainkan menjadi **VIEW** (`v_nav_return`, `v_benchmark_return`) untuk nilai yang bergantung pada baris lain, atau **GENERATED column** untuk nilai yang bergantung pada kolom lain di baris yang sama.
6. Skema hasil translasi diverifikasi memenuhi 1NF hingga BCNF, yaitu tanpa repeating group, tanpa partial dependency pada composite key, dan tanpa transitive dependency. Sebagai contoh, `mutual_fund` tidak menyimpan nama Manajer Investasi, melainkan hanya `manager_id`, sedangkan namanya diperoleh melalui JOIN.

### Penggunaan surrogate key

Sebagian besar entitas memakai natural key yang berasal langsung dari sumber (`fund_id`, `manager_id`, `bank_id`, dan sebagainya). Surrogate key diperkenalkan hanya pada tempat yang memerlukannya, yaitu ketika natural key tidak praktis untuk dijadikan referensi atau tidak cukup unik untuk membentuk primary key.

- **`portfolio_snapshot.snapshot_id`.** Natural key snapshot adalah pasangan komposit `(fund_id, date_based)`, dan pasangan ini menjadi target foreign key bagi dua tabel anak sekaligus, yaitu `portfolio_allocation` dan `portfolio_holding`. Menggunakan surrogate key satu kolom (`snapshot_id`) menyederhanakan kedua foreign key tersebut sehingga tidak perlu membawa dua kolom sekaligus. Pasangan `(fund_id, date_based)` tetap dipertahankan sebagai constraint `UNIQUE` agar tidak muncul snapshot ganda.
- **`security.security_id`.** Instrumen memiliki natural key alami berupa `code` (misalnya kode saham `BBCA`), tetapi surrogate `security_id` dipakai sebagai primary key agar referensi dari `portfolio_holding` bersifat ringkas dan stabil, sementara `code` tetap dijaga `UNIQUE`.
- **`manager_personnel` dan `manager_shareholder`.** Kedua entitas ini bergantung pada `investment_manager`, tetapi atribut alaminya tidak cukup unik untuk membentuk partial key yang unique jika dikombinasikan dengan manager_id. Nama direksi beserta jabatannya, maupun nama pemegang saham, dapat berulang atau tidak konsisten sehingga tidak dapat menjamin keunikan baris di dalam satu Manajer Investasi. Oleh karena itu, keduanya tidak dimodelkan sebagai weak entity, melainkan diberi surrogate ID sendiri sebagai primary key, dengan `manager_id` tetap disimpan sebagai foreign key ke owner-nya.

Prinsip yang dipegang adalah surrogate key diperkenalkan hanya jika memberikan manfaat konkret, baik untuk menyederhanakan relasi maupun untuk menjamin keunikan baris, bukan diterapkan secara seragam ke seluruh tabel.

DDL lengkap seluruh tabel, constraint, view, dan generated column tersedia pada `Data Storing/src/ddl_oltp.sql`.

---

## 8. Screenshot

Berikut adalah bukti query `SELECT ... FROM ... WHERE` yang berhasil dijalankan terhadap database. Berkas gambar tersimpan pada `Data Storing/screenshots/`.

![Screenshot query 1](Data%20Storing/screenshots/query-1.png)

![Screenshot query 2](Data%20Storing/screenshots/query-2.png)

![Screenshot query 3](Data%20Storing/screenshots/query-3.png)

---

## 9. Bonus

### 9.1 Data Warehouse

Data warehouse dirancang dengan model **fact constellation**, yaitu tiga fact table yang berbagi dimensi konform.

```
dim_date, dim_fund (SCD2), dim_manager (SCD2), dim_category, dim_custodian (SCD2)
        |
        +-- fact_nav_daily           (grain: fund x hari)
        +-- fact_aum_monthly         (grain: fund x bulan)
        +-- fact_manager_aum_monthly (grain: Manajer Investasi x bulan)
```

Setiap fact table memiliki grain berbeda dan tidak digabungkan, karena NAV harian, AUM fund bulanan, dan AUM Manajer Investasi bulanan merupakan tiga tingkat pengamatan yang berbeda. Dimensi `dim_date` dan `dim_manager` bersifat konform sehingga memungkinkan analisis drill-across antar fact.

Berkas DDL tersedia pada `Data Storing/Data Warehouse/src/ddl_dw.sql`, sedangkan ETL dari OLTP ke DW tersedia pada `Data Storing/Data Warehouse/src/load_dw.sql`.

#### Konsep penyimpanan: OLTP (upsert) & OLAP (SCD Type 2)

OLTP dan data warehouse menyimpan riwayat data dengan pendekatan yang sengaja dibuat berbeda, karena keduanya menjawab kebutuhan yang berbeda pula.

Pada **OLTP**, tabel master (`investment_manager`, `custodian_bank`, `sales_company`, `mutual_fund`, `security`, `fund_class`) dimuat menggunakan **upsert** (`ON CONFLICT ... DO UPDATE`). Artinya, ketika sebuah atribut berubah, misalnya fee atau alamat, nilai lama ditimpa oleh nilai baru dan yang tersimpan hanyalah keadaan terkini. Pendekatan ini setara dengan SCD Type 1 dan sesuai dengan peran OLTP sebagai *system of record*, yaitu sumber kebenaran atas kondisi data saat ini yang tetap ternormalisasi dan konsisten. Agar perubahan tetap dapat ditelusuri, OLTP dilengkapi tabel `audit_log` yang diisi melalui trigger `AFTER UPDATE`. Tabel ini menjawab pertanyaan "apa yang berubah dan kapan", yang berbeda kebutuhannya dari analisis historis.

Pada **data warehouse (OLAP)**, tujuan utamanya adalah analisis tren jangka panjang, sehingga riwayat atribut justru harus dipertahankan. Untuk itu, dimensi yang atributnya nyata berubah, yaitu `dim_fund`, `dim_manager`, dan `dim_custodian`, memakai **SCD Type 2**. Pada pendekatan ini, setiap versi historis disimpan sebagai baris tersendiri dengan penanda `valid_from`, `valid_to`, dan `is_current`. Dengan demikian, fact table dapat menjawab "berapa fee fund tersebut pada waktu itu", bukan sekadar "berapa fee-nya sekarang".

Ringkasnya, upsert pada OLTP menjaga integritas kondisi terkini, sedangkan SCD Type 2 pada DW menjaga jejak historis. Keduanya saling melengkapi, dan DW selalu dapat dibangun ulang dari OLTP apabila diperlukan.

#### Keputusan SCD dan surrogate key pada dimensi

- **SCD Type 2 untuk `dim_fund`, `dim_manager`, `dim_custodian`.** Ketiganya memiliki atribut yang benar-benar berubah seiring waktu (fee, alamat, status izin). Apabila dimensi ini dibiarkan sebagai SCD Type 1, riwayat atributnya akan hilang setiap kali ETL menimpa baris, dan analitik historis menjadi tidak akurat.
- **SCD Type 1 untuk `dim_date` dan `dim_category`.** Keduanya bersifat statis atau nyaris tidak pernah berubah. `dim_date` adalah kalender, sedangkan `dim_category` menyimpan `conservative_label` dan `fund_type` yang praktis tetap untuk fund yang sama. Menerapkan SCD Type 2 pada keduanya hanya menambah kompleksitas tanpa manfaat berarti.
- **Surrogate key sebagai konsekuensi SCD Type 2.** Karena dimensi SCD Type 2 dapat memiliki banyak baris untuk satu entitas yang sama (satu baris per versi historis), natural key seperti `fund_id` tidak lagi dapat menjadi primary key. Oleh karena itu, tiap dimensi tersebut memakai surrogate key (`dim_fund_key`, `dim_manager_key`, `dim_custodian_key`) sebagai primary key, sementara `fund_id` dan sejenisnya tetap disimpan sebagai natural key biasa yang boleh berulang antar versi.
- **Grain fact table tetap natural.** Fact table mempertahankan grain natural, misalnya `(date_id, fund_id)`, dan menambahkan kolom `dim_*_key` di sampingnya sebagai penunjuk versi dimensi yang berlaku saat fact tersebut dimasukkan. Grain tidak berubah, dan kolom surrogate hanya berperan sebagai penghubung ke versi dimensi yang tepat.

Sebagai konsekuensi desain SCD Type 2 ini, terdapat dua aturan penting saat menjalankan query analitik.

- Join ke dimensi SCD Type 2 harus melalui `dim_*_key` (bukan natural key seperti `fund_id`), karena join melalui natural key akan menggandakan hasil (fan-out) ketika satu entitas memiliki banyak versi historis.
- Agregasi atas nilai absolut seperti `SUM`/`AVG` pada `aum_value` harus dipartisi per `currency_code`, karena terdapat fund yang menggunakan USD. Sebaliknya, agregasi atas rasio seperti `daily_return` aman dilakukan lintas mata uang.

Contoh query analitik yang dapat dijalankan terhadap skema ini:

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

**Skema (ERD atau star schema):**

![ERD/star schema Data Warehouse](Data%20Storing/Data%20Warehouse/design/star_schema.png)

**Bukti query analitik terhadap Data Warehouse:**

![Screenshot query Data Warehouse](Data%20Storing/Data%20Warehouse/screenshots/query_1.png)

### 9.2 Automated Scheduling

Automated scheduling diimplementasikan menggunakan Apache Airflow dengan tiga DAG berjadwal berbeda. Jadwal masing-masing disesuaikan dengan frekuensi perubahan data aktual pada sumber, yang dapat dibuktikan melalui field timestamp pada response API. Sebagai contoh, NAV memiliki field `LastUpdate` yang berubah setiap hari bursa, sedangkan data Manajer Investasi memiliki `DataLastUpdate` yang terakhir berubah beberapa tahun lalu.

| DAG | Jadwal (cron) | Cakupan |
|---|---|---|
| `reksa_dana_daily_nav` | `0 20 * * 1-5` (tiap hari bursa, 20:00 WIB) | NAV, performance, ranking, benchmark |
| `reksa_dana_monthly` | `0 6 2 * *` (tanggal 2 tiap bulan) | AUM fund, AUM MI, portofolio, security baru, return kuartalan |
| `reksa_dana_master` | `0 3 * * 0` (Minggu dini hari) | Manajer Investasi, bank kustodian, APERD, detail fund, fund class |

Kode DAG tersedia pada `airflow/dags/`. Setiap load memakai `ON CONFLICT ... DO NOTHING` untuk tabel time-series (`nav_record`, `aum_record`, `portfolio_snapshot`, dan sejenisnya), karena baris lama tidak pernah berubah dan cukup ditambahkan. Untuk tabel master (`investment_manager`, `mutual_fund`, `custodian_bank`), digunakan `ON CONFLICT ... DO UPDATE` karena atributnya dapat berubah, misalnya fee atau alamat. Dengan demikian, scheduling berkala tidak menghasilkan duplikasi data.

**Bukti scheduling.** Perbedaan nilai `scraped_at` antar batch membuktikan bahwa data diperbarui secara berkala tanpa redundansi baris.

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

Hasil aktual dari database yang berjalan (dua run DAG `reksa_dana_daily_nav` berbeda, yaitu `scheduled__2026-07-22T13:00:00+00:00` dan `manual__2026-07-23T08:54:41`, lihat `airflow/logs/dag_id=reksa_dana_daily_nav/`):

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

Cara membaca hasil di atas:

- Baris `2026-07-20` hingga `2026-07-22` hanya dibuat oleh batch kedua (`batch_mulai` sama dengan `batch_selesai`, yaitu `09:43:00`). Ini merupakan tanggal NAV baru yang belum ada saat batch pertama berjalan, sehingga murni ditambahkan, bukan ditimpa.
- Baris `2026-07-17` memiliki `batch_mulai` (`08:06:30`, dari batch pertama) yang berbeda dari `batch_selesai` (`09:43:00`, dari batch kedua). Artinya, sebagian fund untuk tanggal tersebut telah masuk pada batch pertama, dan batch kedua hanya menambahkan fund yang sebelumnya belum tercatat, tanpa menduplikasi baris yang sudah ada.
- Nilai `jumlah_fund` per tanggal tidak pernah melonjak berlipat meskipun DAG telah dijalankan lebih dari sekali, yang membuktikan tidak adanya redundansi data.

### 9.3 Query Optimasi

Tiga query dioptimasi dengan pengukuran `EXPLAIN ANALYZE` sebelum dan sesudah optimasi, dengan output identik namun waktu eksekusi lebih cepat. Sesuai spesifikasi, seluruh query optimasi dikumpulkan dalam folder tersendiri di root repo bernama `Query Optimasi/`. Seluruh query berada dalam satu berkas `Query Optimasi/query_optimasi.sql`, disertai komentar SQL yang menjelaskan fungsi tiap query, yaitu index composite untuk NAV terbaru per fund, index untuk lookup instrumen pada portofolio, serta materialized view untuk dashboard NAV dan return.

**Bukti optimasi 1, index NAV terbaru per fund:**

![Bukti optimasi 1](Query%20Optimasi/optimasi-1.png)

**Bukti optimasi 2, index lookup instrumen pada portofolio:**

![Bukti optimasi 2](Query%20Optimasi/optimasi-2.png)

Pada screenshot optimasi 2, index `idx_phold_security` kebetulan sudah terpasang dari percobaan sebelumnya ketika query "sebelum" dijalankan, sehingga kedua hasil sama-sama memakai index (7.174 ms berbanding 6.976 ms) dan tidak menunjukkan kontras. Angka pembanding yang valid, yaitu setelah index benar-benar di-drop terlebih dahulu sebelum mengukur baseline, tercantum pada tabel ringkasan di bawah.

**Bukti optimasi 3, materialized view dashboard NAV dan return:**

![Bukti optimasi 3](Query%20Optimasi/optimasi-3.png)

**Ringkasan Hasil Optimasi:**

| # | Optimasi | Sebelum | Sesudah | Perubahan plan |
|---|---|---:|---:|---|
| 1 | Index `idx_nav_fund_date` (fund_id, record_date DESC) | 176.9 ms | 64.8 ms (~2.7x) | `Incremental Sort` menjadi `Index Scan` langsung tanpa sort |
| 2 | Index `idx_phold_security` (security_id) | 9.1 ms | 4.5 ms (~2x) | `Index Scan` pada kolom yang urutannya kurang tepat (`snapshot_id, security_id`) menjadi `Bitmap Index Scan` langsung pada `security_id` |
| 3 | Materialized view `mv_fund_latest_nav` | 420.5 ms | 0.344 ms (~1.200x) | `WindowAgg` (menghitung ulang `LAG()` tiap query) menjadi `Index Scan` langsung membaca hasil tersimpan |

Ketiga optimasi menghasilkan output yang identik dengan query sebelum optimasi (jumlah baris dan isi sama, hanya jalur eksekusinya yang berbeda). Hal ini diverifikasi melalui query `SELECT COUNT(*), MD5(...)` pada akhir `query_optimasi.sql`.

---

## 10. Keterbatasan yang Disadari

Beberapa hal sengaja tidak ditutup karena cakupan tugas ini adalah pemodelan basis data, bukan sistem produksi.

- **Tidak ada penanganan revisi data sumber.** Apabila pasardana merevisi NAV historis setelah proses scrape, model ini tidak akan menangkap revisi tersebut pada OLTP. Pada data warehouse, riwayat perubahan atribut dimensi tetap tertangkap melalui SCD Type 2.
- **Tidak ada pelacakan siklus hidup fund**, sehingga analisis yang hanya mengambil fund aktif berpotensi mengalami survivorship bias, yaitu bias akibat fund berkinerja buruk cenderung lebih dulu tutup atau merger.
- **Sebagian snapshot portofolio totalnya tidak persis 100%.** Hal ini murni merupakan masalah data dari sumbernya, bukan kesalahan pada pipeline.

Sebagian celah di atas ditutup melalui mekanisme lain. Tabel `audit_log` (melalui trigger pada OLTP) mencatat perubahan data master, sedangkan SCD Type 2 pada Data Warehouse (bagian 9.1) menyimpan riwayat atribut dimensi dari waktu ke waktu.

---

## 11. Penggunaan AI

Sesuai ketentuan spesifikasi, berikut penjelasan penggunaan AI dalam pengerjaan tugas ini.

### 1. Bagian yang dibantu AI

- Penulisan **script kode** (Python untuk scraper, preprocessor, loader, dan DAG Airflow) serta **query dan DDL SQL** (skema OLTP, skema Data Warehouse, dan query optimasi). AI digunakan untuk menerjemahkan rancangan yang telah disusun sendiri menjadi kode, mempercepat penulisan boilerplate, dan membantu proses debugging.
- Penyusunan dokumentasi, termasuk README ini dan catatan teknis pada `docs/`.

### 2. Bagian yang dikerjakan sendiri

- **Perancangan desain**, meliputi ERD, skema relasional, keputusan normalisasi, dan keputusan desain database lainnya.
- **Riset endpoint API**, yaitu pemeriksaan endpoint pasardana.id satu per satu secara manual melalui DevTools (tab Network), termasuk penentuan parameter, struktur response, serta endpoint mana yang perlu dan tidak perlu digunakan.
- **Desain database secara keseluruhan**, meliputi pemodelan entitas, kardinalitas, partisipasi, serta pemilihan atribut yang disimpan dibanding atribut turunan. AI hanya membantu menuliskan hasilnya menjadi kode dan DDL, sedangkan keputusan desainnya dilakukan sendiri.

### 3. Refleksi penggunaan AI

AI banyak membantu mempercepat bagian implementasi, yaitu penulisan boilerplate script Python, DDL, dan penyusunan dokumentasi, sehingga waktu dapat lebih difokuskan pada riset endpoint dan pengambilan keputusan desain database. Meskipun demikian, hasil dari AI tetap perlu diverifikasi ke data dan sistem yang sebenarnya, tidak diterima begitu saja. Sebagai contoh konkret, salah satu bukti query optimasi (optimasi 2) yang sempat dianggap selesai ternyata tidak valid setelah diperiksa ulang, karena index pembandingnya telah terpasang lebih dulu dari percobaan sebelumnya sehingga baseline "sebelum" dan "sesudah" sama-sama cepat dan tidak menunjukkan kontras. Hal ini baru diketahui setelah diperiksa langsung ke database, bukan sekadar mengandalkan screenshot yang telah ada. Pelajaran yang diperoleh adalah AI mempercepat proses penulisan dan pendokumentasian, tetapi verifikasi terhadap hasil nyata tetap harus dilakukan sendiri sebelum sesuatu dianggap benar.

### 4. Detail lain

- Tool AI yang digunakan: **Claude Code**.
- Pekerjaan yang melibatkan AI: sebagian besar penulisan script kode (Python) dan SQL (DDL), sedangkan seluruh proses desain (ERD dan skema database) serta riset endpoint API dikerjakan secara manual.

---

## 12. Referensi

- Sumber data: [pasardana.id](https://pasardana.id)
- [Playwright](https://playwright.dev/python/) untuk browser automation dan penanganan sesi.
- [pandas](https://pandas.pydata.org/) untuk transformasi data.
- [psycopg2](https://www.psycopg.org/) untuk koneksi PostgreSQL.
- PostgreSQL 16, dijalankan melalui Podman/Docker Compose.
- Apache Airflow untuk automated scheduling (bonus).
