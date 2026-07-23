# Daftar Snapshot Anomali — Verifikasi Manual

Snapshot portofolio yang **nilai `Value`-nya bukan persen (0-100)** — anomali kualitas data sumber pasardana.id, bukan bug kode. Total **213 snapshot** pada **131 fund**.

**Cara cek manual:** buka `https://pasardana.id/fund/{fund_id}/portfolio` (atau cari nama fund di https://pasardana.id/fund/search → tab Portfolio), pilih bulan sesuai kolom tanggal.

**Kolom:**
- `alloc%` = SUM baris Type 0 (rekap kategori). Seharusnya ≈100%.
- `hold%` = SUM baris Type 1/2 (instrumen individual). Seharusnya parsial (<100%, ~50%).

Setelah Anda cek, beri tahu penanganan yang diinginkan (drop / simpan apa adanya / drop sebagian).

| fund_id | tanggal | alloc% | hold% | tipe fund | nama fund | link |
|---------|---------|--------|-------|-----------|-----------|------|
| 75 | 2025-10-31 | 100.0 | 105.1 | Pendapatan Tetap | Ashmore Dana Obligasi Nusantara Kelas A | [buka](https://pasardana.id/fund/75/portfolio) |
| 75 | 2025-11-28 | 100.0 | 106.6 | Pendapatan Tetap | Ashmore Dana Obligasi Nusantara Kelas A | [buka](https://pasardana.id/fund/75/portfolio) |
| 75 | 2026-01-30 | 100.0 | 101.0 | Pendapatan Tetap | Ashmore Dana Obligasi Nusantara Kelas A | [buka](https://pasardana.id/fund/75/portfolio) |
| 80 | 2025-09-30 | 100.0 | 100.2 | Pendapatan Tetap | Ashmore Dana USD Nusantara Kelas A | [buka](https://pasardana.id/fund/80/portfolio) |
| 80 | 2025-10-31 | 100.0 | 104.3 | Pendapatan Tetap | Ashmore Dana USD Nusantara Kelas A | [buka](https://pasardana.id/fund/80/portfolio) |
| 80 | 2025-11-28 | 100.0 | 103.7 | Pendapatan Tetap | Ashmore Dana USD Nusantara Kelas A | [buka](https://pasardana.id/fund/80/portfolio) |
| 80 | 2026-03-31 | 100.0 | 100.3 | Pendapatan Tetap | Ashmore Dana USD Nusantara Kelas A | [buka](https://pasardana.id/fund/80/portfolio) |
| 125 | 2026-06-30 | 100.0 | 508.9 | Saham | Bahana Primavera Plus | [buka](https://pasardana.id/fund/125/portfolio) |
| 148 | 2025-06-30 | 386.1 | 56.0 | Pasar Uang | Bahana Liquid USD | [buka](https://pasardana.id/fund/148/portfolio) |
| 380 | 2026-02-27 | 100.0 | 109.9 | Pasar Uang | BNI-AM Dana Lancar Syariah | [buka](https://pasardana.id/fund/380/portfolio) |
| 488 | 2025-06-30 | 100.0 | 101.3 | Campuran | BNP Paribas Equitra Campuran Harmoni | [buka](https://pasardana.id/fund/488/portfolio) |
| 488 | 2025-10-31 | 100.0 | 104.9 | Campuran | BNP Paribas Equitra Campuran Harmoni | [buka](https://pasardana.id/fund/488/portfolio) |
| 488 | 2026-02-27 | 100.0 | 100.4 | Campuran | BNP Paribas Equitra Campuran Harmoni | [buka](https://pasardana.id/fund/488/portfolio) |
| 505 | 2025-09-30 | 9235.7 | 47.2 | Saham | BNP Paribas Pesona | [buka](https://pasardana.id/fund/505/portfolio) |
| 512 | 2026-06-30 | 40.0 | 99.6 | Pasar Uang | BNP PARIBAS RUPIAH PLUS | [buka](https://pasardana.id/fund/512/portfolio) |
| 606 | 2025-08-29 | 100.0 | 106.7 | Pendapatan Tetap | CIPTA BOND | [buka](https://pasardana.id/fund/606/portfolio) |
| 647 | 2025-09-30 | 100.0 | 122.4 | Pendapatan Tetap | DANA OBLIGASI STABIL | [buka](https://pasardana.id/fund/647/portfolio) |
| 647 | 2026-03-31 | 100.0 | 100.1 | Pendapatan Tetap | DANA OBLIGASI STABIL | [buka](https://pasardana.id/fund/647/portfolio) |
| 793 | 2025-12-30 | 4935.1 | 59.0 | Campuran | BRI Syariah Berimbang | [buka](https://pasardana.id/fund/793/portfolio) |
| 874 | 2025-08-29 | 87.4 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 874 | 2025-09-30 | 87.6 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 874 | 2025-10-31 | 86.7 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 874 | 2025-11-28 | 88.2 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 874 | 2025-12-30 | 87.9 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 874 | 2026-01-30 | 80.2 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 874 | 2026-02-27 | 86.2 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 874 | 2026-04-30 | 87.6 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 874 | 2026-05-29 | 85.4 | 0.0 | Campuran | Garuda Satu | [buka](https://pasardana.id/fund/874/portfolio) |
| 898 | 2026-03-31 | 100.0 | 101.5 | Saham | HPAM SYARIAH EKUITAS | [buka](https://pasardana.id/fund/898/portfolio) |
| 919 | 2025-09-30 | 100.0 | 926.3 | Pasar Uang | Insight Money (I-Money) | [buka](https://pasardana.id/fund/919/portfolio) |
| 920 | 2025-09-30 | 100.0 | 104.0 | Pasar Uang | Insight Money Syariah (I-Money Syariah) | [buka](https://pasardana.id/fund/920/portfolio) |
| 934 | 2026-05-29 | 89.5 | 62.4 | Pendapatan Tetap | Investa Dana Dollar Mandiri Kelas A | [buka](https://pasardana.id/fund/934/portfolio) |
| 953 | 2025-08-29 | 174.0 | 70.1 | Pendapatan Tetap | LIF Bond Plus | [buka](https://pasardana.id/fund/953/portfolio) |
| 1033 | 2025-09-30 | 613.8 | 21.8 | Pendapatan Tetap | Makara Prima Kelas G | [buka](https://pasardana.id/fund/1033/portfolio) |
| 1080 | 2026-01-30 | 85.5 | 63.5 | Campuran | Mandiri Investa Aktif Kelas A | [buka](https://pasardana.id/fund/1080/portfolio) |
| 1082 | 2025-11-28 | 84.6 | 40.1 | Saham | Mandiri Investa Atraktif Syariah | [buka](https://pasardana.id/fund/1082/portfolio) |
| 1082 | 2025-12-30 | 116.0 | 55.7 | Saham | Mandiri Investa Atraktif Syariah | [buka](https://pasardana.id/fund/1082/portfolio) |
| 1082 | 2026-01-30 | 89.1 | 42.2 | Saham | Mandiri Investa Atraktif Syariah | [buka](https://pasardana.id/fund/1082/portfolio) |
| 1092 | 2025-09-30 | 26.4 | 54.5 | Pendapatan Tetap | Mandiri Investa Dana Syariah Kelas A | [buka](https://pasardana.id/fund/1092/portfolio) |
| 1098 | 2025-08-29 | 88.1 | 40.5 | Saham | MANDIRI INVESTA EKUITAS SYARIAH | [buka](https://pasardana.id/fund/1098/portfolio) |
| 1098 | 2025-11-28 | 82.6 | 39.6 | Saham | MANDIRI INVESTA EKUITAS SYARIAH | [buka](https://pasardana.id/fund/1098/portfolio) |
| 1098 | 2026-01-30 | 87.0 | 44.7 | Saham | MANDIRI INVESTA EKUITAS SYARIAH | [buka](https://pasardana.id/fund/1098/portfolio) |
| 1098 | 2026-05-29 | 86.3 | 46.7 | Saham | MANDIRI INVESTA EKUITAS SYARIAH | [buka](https://pasardana.id/fund/1098/portfolio) |
| 1098 | 2026-06-30 | 88.2 | 49.3 | Saham | MANDIRI INVESTA EKUITAS SYARIAH | [buka](https://pasardana.id/fund/1098/portfolio) |
| 1100 | 2026-01-30 | 85.9 | 37.5 | Saham | MANDIRI INVESTA EQUITY DYNAMO FACTOR | [buka](https://pasardana.id/fund/1100/portfolio) |
| 1106 | 2026-03-31 | 110.3 | 78.7 | Pasar Uang | Mandiri Investa Pasar Uang Kelas A | [buka](https://pasardana.id/fund/1106/portfolio) |
| 1117 | 2026-02-27 | 110.4 | 61.9 | Saham | Mandiri Investa Cerdas Bangsa Kelas A | [buka](https://pasardana.id/fund/1117/portfolio) |
| 1300 | 2025-11-28 | 44.5 | 55.5 | Pendapatan Tetap | MEGA DANA OBLIGASI DUA | [buka](https://pasardana.id/fund/1300/portfolio) |
| 1300 | 2025-12-30 | 45.8 | 54.2 | Pendapatan Tetap | MEGA DANA OBLIGASI DUA | [buka](https://pasardana.id/fund/1300/portfolio) |
| 1350 | 2025-10-31 | 151.1 | 121.0 | Pasar Uang | MNC DANA LANCAR | [buka](https://pasardana.id/fund/1350/portfolio) |
| 1399 | 2025-11-28 | 100.0 | 102.9 | Pendapatan Tetap | INAMI Indah Pendapatan Tetap Nusantara | [buka](https://pasardana.id/fund/1399/portfolio) |
| 1400 | 2025-06-30 | 100.0 | 117.7 | Campuran | Inami Balanced Fund | [buka](https://pasardana.id/fund/1400/portfolio) |
| 1400 | 2026-02-27 | 100.0 | 139.8 | Campuran | Inami Balanced Fund | [buka](https://pasardana.id/fund/1400/portfolio) |
| 1417 | 2025-07-31 | 100.0 | 105.9 | Pendapatan Tetap | INAMI Tracker Obligasi Nusantara | [buka](https://pasardana.id/fund/1417/portfolio) |
| 1630 | 2026-06-30 | 81.8 | 81.9 | Pendapatan Tetap | PNM Amanah Syariah Kelas A | [buka](https://pasardana.id/fund/1630/portfolio) |
| 1636 | 2026-06-30 | 81.0 | 49.5 | Saham | PNM Ekuitas Syariah | [buka](https://pasardana.id/fund/1636/portfolio) |
| 1639 | 2026-06-30 | 85.7 | 46.7 | Saham | PNM SAHAM AGRESIF | [buka](https://pasardana.id/fund/1639/portfolio) |
| 1924 | 2025-10-31 | 100.0 | 100.1 | Campuran | SAM SYARIAH BERIMBANG | [buka](https://pasardana.id/fund/1924/portfolio) |
| 1924 | 2025-12-30 | 100.0 | 100.1 | Campuran | SAM SYARIAH BERIMBANG | [buka](https://pasardana.id/fund/1924/portfolio) |
| 1924 | 2026-01-30 | 100.0 | 100.1 | Campuran | SAM SYARIAH BERIMBANG | [buka](https://pasardana.id/fund/1924/portfolio) |
| 1932 | 2026-03-31 | 88.3 | 33.2 | Saham | SCHRODER DANA ISTIMEWA | [buka](https://pasardana.id/fund/1932/portfolio) |
| 1932 | 2026-05-29 | 89.2 | 28.6 | Saham | SCHRODER DANA ISTIMEWA | [buka](https://pasardana.id/fund/1932/portfolio) |
| 1946 | 2026-02-27 | 263.4 | 37.7 | Campuran | SCHRODER DANA TERPADU II | [buka](https://pasardana.id/fund/1946/portfolio) |
| 2061 | 2026-06-30 | 100.0 | 103.1 | Campuran | Sucorinvest Premium Fund Kelas A | [buka](https://pasardana.id/fund/2061/portfolio) |
| 2098 | 2025-12-30 | 112.8 | 68.2 | Saham | Syailendra Equity Opportunity Fund Kelas A | [buka](https://pasardana.id/fund/2098/portfolio) |
| 2099 | 2025-06-30 | 100.0 | 102.2 | Pendapatan Tetap | Syailendra Fixed Income Fund Kelas A | [buka](https://pasardana.id/fund/2099/portfolio) |
| 2099 | 2026-03-31 | 100.0 | 103.0 | Pendapatan Tetap | Syailendra Fixed Income Fund Kelas A | [buka](https://pasardana.id/fund/2099/portfolio) |
| 2127 | 2025-12-30 | 100.0 | 1880.4 | Campuran | TRAM ALPHA | [buka](https://pasardana.id/fund/2127/portfolio) |
| 2183 | 2025-09-30 | 100.0 | 902.3 | Saham | Cipta GTWS Equity | [buka](https://pasardana.id/fund/2183/portfolio) |
| 2215 | 2026-03-31 | 100.0 | 351.2 | Pasar Uang | Capital Money Market Fund | [buka](https://pasardana.id/fund/2215/portfolio) |
| 2232 | 2026-04-30 | 111.9 | 95.7 | Pasar Uang | MNC Dana Syariah Barokah | [buka](https://pasardana.id/fund/2232/portfolio) |
| 2288 | 2026-06-30 | 80.8 | 59.0 | Saham | PNM SAHAM UNGGULAN | [buka](https://pasardana.id/fund/2288/portfolio) |
| 2309 | 2025-07-31 | 100.0 | 101.1 | Pendapatan Tetap | HPAM GOVERNMENT BOND | [buka](https://pasardana.id/fund/2309/portfolio) |
| 2309 | 2025-11-28 | 100.0 | 100.2 | Pendapatan Tetap | HPAM GOVERNMENT BOND | [buka](https://pasardana.id/fund/2309/portfolio) |
| 2328 | 2025-07-31 | 100.0 | 261.1 | Pendapatan Tetap | I AM BOND FUND | [buka](https://pasardana.id/fund/2328/portfolio) |
| 2457 | 2026-02-27 | 48.0 | 96.7 | Pasar Uang | TRIMEGAH DANA LIKUID | [buka](https://pasardana.id/fund/2457/portfolio) |
| 2488 | 2025-06-30 | 100.0 | 100.2 | Pasar Uang | ASHMORE DANA PASAR UANG NUSANTARA | [buka](https://pasardana.id/fund/2488/portfolio) |
| 2488 | 2025-07-31 | 100.0 | 100.3 | Pasar Uang | ASHMORE DANA PASAR UANG NUSANTARA | [buka](https://pasardana.id/fund/2488/portfolio) |
| 2488 | 2025-09-30 | 100.0 | 103.7 | Pasar Uang | ASHMORE DANA PASAR UANG NUSANTARA | [buka](https://pasardana.id/fund/2488/portfolio) |
| 2513 | 2025-06-30 | 131.7 | 65.6 | Pasar Uang | Sequis Liquid Prima | [buka](https://pasardana.id/fund/2513/portfolio) |
| 2576 | 2025-08-29 | 100.0 | 134.1 | Global/ETF | Eastspring Syariah Equity Islamic Asia Pacific USD | [buka](https://pasardana.id/fund/2576/portfolio) |
| 2620 | 2026-03-31 | 123.0 | 62.3 | Campuran | HPAM ULTIMA BALANCE | [buka](https://pasardana.id/fund/2620/portfolio) |
| 2751 | 2026-06-30 | 2885.9 | 66.8 | Campuran | VICTORIA CAMPURAN DINAMIS | [buka](https://pasardana.id/fund/2751/portfolio) |
| 2765 | 2026-05-29 | 100.0 | 129.8 | Campuran | AVRIST BALANCED AMAR SYARIAH | [buka](https://pasardana.id/fund/2765/portfolio) |
| 3075 | 2025-08-29 | 10.0 | 55.4 | Saham | Avrist Ada Saham Blue Safir Kelas A | [buka](https://pasardana.id/fund/3075/portfolio) |
| 3113 | 2025-08-29 | 100.0 | 100.2 | Pendapatan Tetap | Manulife Syariah Sukuk Indonesia | [buka](https://pasardana.id/fund/3113/portfolio) |
| 3113 | 2025-11-28 | 67.0 | 91.0 | Pendapatan Tetap | Manulife Syariah Sukuk Indonesia | [buka](https://pasardana.id/fund/3113/portfolio) |
| 3113 | 2025-12-30 | 100.0 | 100.5 | Pendapatan Tetap | Manulife Syariah Sukuk Indonesia | [buka](https://pasardana.id/fund/3113/portfolio) |
| 3113 | 2026-01-30 | 100.0 | 100.4 | Pendapatan Tetap | Manulife Syariah Sukuk Indonesia | [buka](https://pasardana.id/fund/3113/portfolio) |
| 3244 | 2025-10-31 | 100.0 | 100.2 | Saham | Victoria Equity Maxima | [buka](https://pasardana.id/fund/3244/portfolio) |
| 3244 | 2025-11-28 | 100.0 | 100.2 | Saham | Victoria Equity Maxima | [buka](https://pasardana.id/fund/3244/portfolio) |
| 3264 | 2026-03-31 | 3297.5 | 70.0 | Pasar Uang | Danapathi Money Market Fund | [buka](https://pasardana.id/fund/3264/portfolio) |
| 3374 | 2025-06-30 | 3195.0 | 96.7 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas A | [buka](https://pasardana.id/fund/3374/portfolio) |
| 3374 | 2025-11-28 | 112.4 | 107.0 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas A | [buka](https://pasardana.id/fund/3374/portfolio) |
| 3374 | 2026-01-30 | 120.2 | 114.8 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas A | [buka](https://pasardana.id/fund/3374/portfolio) |
| 3374 | 2026-02-27 | 130.2 | 124.1 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas A | [buka](https://pasardana.id/fund/3374/portfolio) |
| 3374 | 2026-03-31 | 118.2 | 113.8 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas A | [buka](https://pasardana.id/fund/3374/portfolio) |
| 3374 | 2026-04-30 | 112.4 | 109.5 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas A | [buka](https://pasardana.id/fund/3374/portfolio) |
| 3374 | 2026-05-29 | 113.7 | 113.3 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas A | [buka](https://pasardana.id/fund/3374/portfolio) |
| 3432 | 2025-08-29 | 100.0 | 101.1 | Pendapatan Tetap | Ashmore Dana Obligasi Unggulan Nusantara Kelas A | [buka](https://pasardana.id/fund/3432/portfolio) |
| 3432 | 2025-09-30 | 100.0 | 103.6 | Pendapatan Tetap | Ashmore Dana Obligasi Unggulan Nusantara Kelas A | [buka](https://pasardana.id/fund/3432/portfolio) |
| 3432 | 2025-10-31 | 100.0 | 102.9 | Pendapatan Tetap | Ashmore Dana Obligasi Unggulan Nusantara Kelas A | [buka](https://pasardana.id/fund/3432/portfolio) |
| 3432 | 2025-11-28 | 100.0 | 101.0 | Pendapatan Tetap | Ashmore Dana Obligasi Unggulan Nusantara Kelas A | [buka](https://pasardana.id/fund/3432/portfolio) |
| 3447 | 2025-11-28 | 100.0 | 100.0 | Pasar Uang | Reliance Pasar Uang | [buka](https://pasardana.id/fund/3447/portfolio) |
| 3456 | 2026-06-30 | 100.0 | 104.9 | Pasar Uang | Capital Sharia Money Market | [buka](https://pasardana.id/fund/3456/portfolio) |
| 3467 | 2025-09-30 | 114.1 | 63.5 | Pasar Uang | Nusadana Lancar | [buka](https://pasardana.id/fund/3467/portfolio) |
| 3493 | 2025-08-29 | 100.0 | 101.0 | Pendapatan Tetap | Victoria Obligasi Negara Syariah | [buka](https://pasardana.id/fund/3493/portfolio) |
| 3493 | 2026-05-29 | 100.0 | 101.5 | Pendapatan Tetap | Victoria Obligasi Negara Syariah | [buka](https://pasardana.id/fund/3493/portfolio) |
| 3519 | 2025-07-31 | 85.0 | 78.7 | Pasar Uang | Majoris Pasar Uang Syariah Indonesia | [buka](https://pasardana.id/fund/3519/portfolio) |
| 3545 | 2026-04-30 | 7783.4 | 35.2 | Campuran | Insight Bhinneka Balanced Fund | [buka](https://pasardana.id/fund/3545/portfolio) |
| 3597 | 2025-11-28 | 100.0 | 100.2 | Pasar Uang | SAM Dana Likuid Syariah | [buka](https://pasardana.id/fund/3597/portfolio) |
| 3597 | 2026-05-29 | 100.0 | 100.1 | Pasar Uang | SAM Dana Likuid Syariah | [buka](https://pasardana.id/fund/3597/portfolio) |
| 3597 | 2026-06-30 | 100.0 | 100.1 | Pasar Uang | SAM Dana Likuid Syariah | [buka](https://pasardana.id/fund/3597/portfolio) |
| 3631 | 2026-03-31 | 100.0 | 103.0 | Campuran | Pinnacle Balanced Growth Fund | [buka](https://pasardana.id/fund/3631/portfolio) |
| 3637 | 2025-06-30 | 100.0 | 132.8 | Pasar Uang | Insight Retail Cash Fund (I-Retail Cash) | [buka](https://pasardana.id/fund/3637/portfolio) |
| 3723 | 2025-10-31 | 100.0 | 100.5 | Saham | Syailendra MSCI Indonesia Value Index Fund Kelas A | [buka](https://pasardana.id/fund/3723/portfolio) |
| 3723 | 2026-01-30 | 100.0 | 100.6 | Saham | Syailendra MSCI Indonesia Value Index Fund Kelas A | [buka](https://pasardana.id/fund/3723/portfolio) |
| 3723 | 2026-02-27 | 100.0 | 100.5 | Saham | Syailendra MSCI Indonesia Value Index Fund Kelas A | [buka](https://pasardana.id/fund/3723/portfolio) |
| 3723 | 2026-05-29 | 100.0 | 100.7 | Saham | Syailendra MSCI Indonesia Value Index Fund Kelas A | [buka](https://pasardana.id/fund/3723/portfolio) |
| 3742 | 2025-07-31 | 100.0 | 100.1 | Pendapatan Tetap | SAM Dana Obligasi Prima | [buka](https://pasardana.id/fund/3742/portfolio) |
| 3742 | 2025-08-29 | 100.0 | 100.1 | Pendapatan Tetap | SAM Dana Obligasi Prima | [buka](https://pasardana.id/fund/3742/portfolio) |
| 3742 | 2026-02-27 | 100.0 | 100.1 | Pendapatan Tetap | SAM Dana Obligasi Prima | [buka](https://pasardana.id/fund/3742/portfolio) |
| 3742 | 2026-05-29 | 100.0 | 100.1 | Pendapatan Tetap | SAM Dana Obligasi Prima | [buka](https://pasardana.id/fund/3742/portfolio) |
| 3744 | 2025-10-31 | 111.4 | 43.3 | Campuran | SAM Cipta Sejahtera Campuran Kelas D | [buka](https://pasardana.id/fund/3744/portfolio) |
| 3830 | 2025-12-30 | 70.7 | 66.1 | Campuran | Jasa Capital Campuran Harmonis | [buka](https://pasardana.id/fund/3830/portfolio) |
| 3893 | 2026-04-30 | 30.0 | 81.5 | Campuran | Capital Balanced Growth | [buka](https://pasardana.id/fund/3893/portfolio) |
| 3977 | 2025-06-30 | 100.0 | 101.0 | Pasar Uang | PNM Arafah | [buka](https://pasardana.id/fund/3977/portfolio) |
| 4056 | 2025-06-30 | 106.3 | 106.0 | Pendapatan Tetap | Danapathi Fixed Income Fund | [buka](https://pasardana.id/fund/4056/portfolio) |
| 4116 | 2026-02-27 | 100.0 | 111.0 | Pasar Uang | PNM Falah | [buka](https://pasardana.id/fund/4116/portfolio) |
| 4116 | 2026-04-30 | 114.4 | 97.0 | Pasar Uang | PNM Falah | [buka](https://pasardana.id/fund/4116/portfolio) |
| 4144 | 2026-02-27 | 821.3 | 66.3 | Campuran | Jarvis Balanced Fund | [buka](https://pasardana.id/fund/4144/portfolio) |
| 4147 | 2026-02-27 | 8736.8 | 38.5 | Pendapatan Tetap | Trimegah Fixed Income Plan | [buka](https://pasardana.id/fund/4147/portfolio) |
| 4414 | 2026-04-30 | 100.0 | 105.9 | Saham | KIM Equity Fund | [buka](https://pasardana.id/fund/4414/portfolio) |
| 4504 | 2025-07-31 | 100.0 | 101.8 | Saham | Premier ETF MSCI Indonesia Large Cap | [buka](https://pasardana.id/fund/4504/portfolio) |
| 4557 | 2026-05-29 | 100.0 | 110.8 | Pasar Uang | Avrist Ada Liquid Syariah | [buka](https://pasardana.id/fund/4557/portfolio) |
| 4740 | 2025-06-30 | 100.0 | 106.0 | Pendapatan Tetap | PNM Surat Berharga Syariah Negara | [buka](https://pasardana.id/fund/4740/portfolio) |
| 4779 | 2025-06-30 | 173.8 | 48.4 | Pendapatan Tetap | UOBAM Dana Membangun Negeri Kelas G | [buka](https://pasardana.id/fund/4779/portfolio) |
| 4791 | 2025-09-30 | 100.0 | 106.2 | Pendapatan Tetap | Eastspring Syariah Fixed Income USD Kelas A | [buka](https://pasardana.id/fund/4791/portfolio) |
| 4802 | 2025-06-30 | 138.5 | 72.0 | Pasar Uang | BMI Indo Pasar Uang | [buka](https://pasardana.id/fund/4802/portfolio) |
| 4802 | 2025-09-30 | 135.1 | 69.2 | Pasar Uang | BMI Indo Pasar Uang | [buka](https://pasardana.id/fund/4802/portfolio) |
| 4802 | 2025-11-28 | 146.2 | 62.8 | Pasar Uang | BMI Indo Pasar Uang | [buka](https://pasardana.id/fund/4802/portfolio) |
| 4802 | 2025-12-30 | 145.1 | 57.8 | Pasar Uang | BMI Indo Pasar Uang | [buka](https://pasardana.id/fund/4802/portfolio) |
| 4802 | 2026-01-30 | 142.6 | 57.7 | Pasar Uang | BMI Indo Pasar Uang | [buka](https://pasardana.id/fund/4802/portfolio) |
| 4802 | 2026-02-27 | 147.7 | 54.6 | Pasar Uang | BMI Indo Pasar Uang | [buka](https://pasardana.id/fund/4802/portfolio) |
| 4802 | 2026-05-29 | 167.2 | 46.6 | Pasar Uang | BMI Indo Pasar Uang | [buka](https://pasardana.id/fund/4802/portfolio) |
| 4810 | 2025-09-30 | 100.0 | 834.9 | Pasar Uang | Trimegah Pundi Kas 11 | [buka](https://pasardana.id/fund/4810/portfolio) |
| 4928 | 2025-12-30 | 32.0 | 111.2 | Pendapatan Tetap | Anargya Supergrowth | [buka](https://pasardana.id/fund/4928/portfolio) |
| 5007 | 2026-02-27 | 103.2 | 103.2 | Pasar Uang | Mandiri Money Market USD | [buka](https://pasardana.id/fund/5007/portfolio) |
| 5007 | 2026-03-31 | 110.8 | 116.8 | Pasar Uang | Mandiri Money Market USD | [buka](https://pasardana.id/fund/5007/portfolio) |
| 5047 | 2026-04-30 | 100.0 | 100.2 | Pasar Uang | Ashmore Dana Pasar Uang Syariah | [buka](https://pasardana.id/fund/5047/portfolio) |
| 5047 | 2026-05-29 | 100.0 | 100.2 | Pasar Uang | Ashmore Dana Pasar Uang Syariah | [buka](https://pasardana.id/fund/5047/portfolio) |
| 5047 | 2026-06-30 | 100.0 | 100.2 | Pasar Uang | Ashmore Dana Pasar Uang Syariah | [buka](https://pasardana.id/fund/5047/portfolio) |
| 5054 | 2025-12-30 | 82.6 | 58.5 | Global/ETF | Mandiri Asia Sharia Equity Dollar Kelas B | [buka](https://pasardana.id/fund/5054/portfolio) |
| 5065 | 2026-01-30 | 100.0 | 109.8 | Pasar Uang | Valbury Liquid Fund | [buka](https://pasardana.id/fund/5065/portfolio) |
| 5080 | 2025-09-30 | 100.5 | 100.5 | Pendapatan Tetap | Victoria Fixed Income | [buka](https://pasardana.id/fund/5080/portfolio) |
| 5085 | 2026-06-30 | 306.9 | 65.2 | Pendapatan Tetap | Star Fixed Income 3 | [buka](https://pasardana.id/fund/5085/portfolio) |
| 5115 | 2026-04-30 | 117.0 | 94.5 | Pasar Uang | Simpan Cash Fund | [buka](https://pasardana.id/fund/5115/portfolio) |
| 5157 | 2025-10-31 | 93.0 | 129.9 | Pendapatan Tetap | KB Valbury Stable Growth Fund | [buka](https://pasardana.id/fund/5157/portfolio) |
| 5169 | 2026-01-30 | 100.0 | 166.0 | Pasar Uang | Anargya Supergama | [buka](https://pasardana.id/fund/5169/portfolio) |
| 5185 | 2025-09-30 | 100.0 | 2067.5 | Pasar Uang | Trimegah Pundi Kas Syariah 2 | [buka](https://pasardana.id/fund/5185/portfolio) |
| 5191 | 2025-09-30 | 100.0 | 100.1 | Saham | Sucorinvest Sharia Sustainability Equity Fund | [buka](https://pasardana.id/fund/5191/portfolio) |
| 5203 | 2026-02-27 | 110.4 | 61.9 | Saham | Mandiri Investa Cerdas Bangsa Kelas B | [buka](https://pasardana.id/fund/5203/portfolio) |
| 5248 | 2026-06-30 | 100.0 | 104.9 | Saham | Star Infobank 15 Kelas Utama | [buka](https://pasardana.id/fund/5248/portfolio) |
| 5254 | 2025-07-31 | 100.0 | 100.1 | Pendapatan Tetap | Trimegah Dana Tetap Syariah 2 | [buka](https://pasardana.id/fund/5254/portfolio) |
| 5273 | 2025-12-30 | 82.6 | 58.5 | Global/ETF | Mandiri Asia Sharia Equity Dollar Kelas A | [buka](https://pasardana.id/fund/5273/portfolio) |
| 5299 | 2026-04-30 | 100.0 | 108.6 | Pendapatan Tetap | Maybank Obligasi Syariah Negara | [buka](https://pasardana.id/fund/5299/portfolio) |
| 5299 | 2026-05-29 | 100.0 | 100.9 | Pendapatan Tetap | Maybank Obligasi Syariah Negara | [buka](https://pasardana.id/fund/5299/portfolio) |
| 5336 | 2025-09-30 | 100.0 | 122.3 | Saham | Batavia Index PEFINDO I GRADE | [buka](https://pasardana.id/fund/5336/portfolio) |
| 5353 | 2025-09-30 | 100.0 | 100.3 | Terproteksi | Sam Dana Obligasi Terproteksi 10 | [buka](https://pasardana.id/fund/5353/portfolio) |
| 5353 | 2025-10-31 | 100.0 | 102.9 | Terproteksi | Sam Dana Obligasi Terproteksi 10 | [buka](https://pasardana.id/fund/5353/portfolio) |
| 5353 | 2025-11-28 | 100.0 | 102.5 | Terproteksi | Sam Dana Obligasi Terproteksi 10 | [buka](https://pasardana.id/fund/5353/portfolio) |
| 5353 | 2025-12-30 | 100.0 | 103.5 | Terproteksi | Sam Dana Obligasi Terproteksi 10 | [buka](https://pasardana.id/fund/5353/portfolio) |
| 5353 | 2026-01-30 | 100.0 | 102.8 | Terproteksi | Sam Dana Obligasi Terproteksi 10 | [buka](https://pasardana.id/fund/5353/portfolio) |
| 5353 | 2026-02-27 | 100.0 | 102.8 | Terproteksi | Sam Dana Obligasi Terproteksi 10 | [buka](https://pasardana.id/fund/5353/portfolio) |
| 5353 | 2026-03-31 | 100.0 | 100.5 | Terproteksi | Sam Dana Obligasi Terproteksi 10 | [buka](https://pasardana.id/fund/5353/portfolio) |
| 5353 | 2026-05-29 | 100.0 | 100.1 | Terproteksi | Sam Dana Obligasi Terproteksi 10 | [buka](https://pasardana.id/fund/5353/portfolio) |
| 5357 | 2026-06-30 | 81.8 | 81.9 | Pendapatan Tetap | PNM Amanah Syariah Kelas D | [buka](https://pasardana.id/fund/5357/portfolio) |
| 5372 | 2025-06-30 | 173.8 | 48.4 | Pendapatan Tetap | UOBAM Dana Membangun Negeri Kelas D | [buka](https://pasardana.id/fund/5372/portfolio) |
| 5392 | 2026-01-30 | 100.0 | 100.0 | Saham | BNI AM IDX Pefindo Prime Bank Kelas R1 | [buka](https://pasardana.id/fund/5392/portfolio) |
| 5400 | 2025-08-29 | 10.0 | 55.4 | Saham | Avrist Ada Saham Blue Safir Kelas D | [buka](https://pasardana.id/fund/5400/portfolio) |
| 5405 | 2025-06-30 | 3195.0 | 96.7 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas C | [buka](https://pasardana.id/fund/5405/portfolio) |
| 5405 | 2025-11-28 | 112.4 | 107.0 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas C | [buka](https://pasardana.id/fund/5405/portfolio) |
| 5405 | 2026-01-30 | 120.2 | 114.8 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas C | [buka](https://pasardana.id/fund/5405/portfolio) |
| 5405 | 2026-02-27 | 130.2 | 124.1 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas C | [buka](https://pasardana.id/fund/5405/portfolio) |
| 5405 | 2026-03-31 | 118.2 | 113.8 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas C | [buka](https://pasardana.id/fund/5405/portfolio) |
| 5405 | 2026-04-30 | 112.4 | 109.5 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas C | [buka](https://pasardana.id/fund/5405/portfolio) |
| 5405 | 2026-05-29 | 113.7 | 113.3 | Pasar Uang | Mandiri Pasar Uang Syariah Kelas C | [buka](https://pasardana.id/fund/5405/portfolio) |
| 5413 | 2026-03-31 | 110.3 | 78.7 | Pasar Uang | Mandiri Investa Pasar Uang Kelas C | [buka](https://pasardana.id/fund/5413/portfolio) |
| 5428 | 2026-06-30 | 100.0 | 129.8 | Saham | Simpan Sustainable Equity Fund | [buka](https://pasardana.id/fund/5428/portfolio) |
| 5445 | 2026-03-31 | 110.3 | 78.7 | Pasar Uang | Mandiri Investa Pasar Uang Kelas B | [buka](https://pasardana.id/fund/5445/portfolio) |
| 5454 | 2025-07-31 | 100.0 | 104.3 | Terproteksi | Panin 37 | [buka](https://pasardana.id/fund/5454/portfolio) |
| 5465 | 2026-06-30 | 100.0 | 104.9 | Saham | Star Infobank 15 Kelas Profesional | [buka](https://pasardana.id/fund/5465/portfolio) |
| 5488 | 2026-05-29 | 100.0 | 106.9 | Pendapatan Tetap | Grow Obligasi Optima Dinamis Kelas O | [buka](https://pasardana.id/fund/5488/portfolio) |
| 5509 | 2025-07-31 | 116.0 | 79.0 | Saham | Trimegah Equity Focus 2 Kelas A | [buka](https://pasardana.id/fund/5509/portfolio) |
| 5512 | 2026-05-29 | 100.0 | 100.0 | Pasar Uang | Lif Money Market | [buka](https://pasardana.id/fund/5512/portfolio) |
| 5531 | 2025-09-30 | 26.4 | 54.5 | Pendapatan Tetap | Mandiri Investa Dana Syariah Kelas D | [buka](https://pasardana.id/fund/5531/portfolio) |
| 5544 | 2026-06-30 | 81.8 | 81.9 | Pendapatan Tetap | PNM Amanah Syariah Kelas B | [buka](https://pasardana.id/fund/5544/portfolio) |
| 5549 | 2026-06-30 | 100.0 | 104.9 | Saham | Star Infobank 15 Kelas Dana | [buka](https://pasardana.id/fund/5549/portfolio) |
| 5589 | 2025-12-30 | 100.0 | 1126.1 | Pendapatan Tetap | RDS SBSN Anargya Superoptima | [buka](https://pasardana.id/fund/5589/portfolio) |
| 5628 | 2025-11-28 | 100.0 | 100.5 | Saham | Batavia Index IDX Pefindo Prime Bank Kelas A | [buka](https://pasardana.id/fund/5628/portfolio) |
| 5628 | 2025-12-30 | 100.0 | 101.0 | Saham | Batavia Index IDX Pefindo Prime Bank Kelas A | [buka](https://pasardana.id/fund/5628/portfolio) |
| 5628 | 2026-01-30 | 100.0 | 100.5 | Saham | Batavia Index IDX Pefindo Prime Bank Kelas A | [buka](https://pasardana.id/fund/5628/portfolio) |
| 5628 | 2026-02-27 | 100.0 | 101.2 | Saham | Batavia Index IDX Pefindo Prime Bank Kelas A | [buka](https://pasardana.id/fund/5628/portfolio) |
| 5628 | 2026-05-29 | 100.0 | 100.2 | Saham | Batavia Index IDX Pefindo Prime Bank Kelas A | [buka](https://pasardana.id/fund/5628/portfolio) |
| 5634 | 2026-03-31 | 84.1 | 71.3 | Pendapatan Tetap | Sucorinvest Phei AAA Corporate Bond Fund | [buka](https://pasardana.id/fund/5634/portfolio) |
| 5665 | 2025-08-25 | 60.3 | 99.3 | Pasar Uang | BRI Seruni Likuid Dolar | [buka](https://pasardana.id/fund/5665/portfolio) |
| 5697 | 2025-08-29 | 996.0 | 847.8 | Pasar Uang | Recapital Money Market Liquid | [buka](https://pasardana.id/fund/5697/portfolio) |
| 5726 | 2025-08-29 | 103.4 | 103.4 | Pendapatan Tetap | Recapital Pendapatan Tetap Dana Gemilang | [buka](https://pasardana.id/fund/5726/portfolio) |
| 5726 | 2025-09-30 | 87.7 | 96.2 | Pendapatan Tetap | Recapital Pendapatan Tetap Dana Gemilang | [buka](https://pasardana.id/fund/5726/portfolio) |
| 5779 | 2026-04-30 | 100.0 | 109.1 | Pasar Uang | Batavia USD Money Market | [buka](https://pasardana.id/fund/5779/portfolio) |
| 5783 | 2026-05-29 | 100.0 | 108.8 | Global/ETF | IBESLN Syailendra Russel Idealratings Top 200 Isla | [buka](https://pasardana.id/fund/5783/portfolio) |
| 5917 | 2026-05-29 | 100.0 | 105.6 | Campuran | Grow Absolute Mixed Alpha Kelas O | [buka](https://pasardana.id/fund/5917/portfolio) |
| 5919 | 2026-05-29 | 100.0 | 105.6 | Campuran | Grow Absolute Mixed Alpha Kelas P | [buka](https://pasardana.id/fund/5919/portfolio) |