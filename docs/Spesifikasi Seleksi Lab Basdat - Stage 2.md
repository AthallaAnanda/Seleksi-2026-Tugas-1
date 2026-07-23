**Seleksi Tahap 2 Asisten Basis Data 2026**  
**ETL *Project***  
***Data Scraping, Database Modeling, and Data Storing***  
---

Pada tahap seleksi ini, peserta akan diminta untuk melakukan ETL dengan melakukan *data scraping* terkait sebuah topik yang dibebaskan pada peserta. Peserta diminta untuk merancang sebuah ERD dan model *database* relasional yang akan diimplementasikan untuk menyimpan pemrosesan *data scraping* sebelumnya.   
Tahap seleksi ini akan menguji kemampuan peserta dalam mengumpulkan data, merancang *database,* dan merealisasikan rancangan tersebut menjadi *database* relasional yang fungsional.

***Step 1: Data Scraping***

1. Pilih sebuah topik yang akan kalian jadikan sebagai tema pada seleksi data scraping Anda. Daftarkan topik tersebut ke dalam spreadsheet berikut: [Daftar Topik Seleksi Asisten Lab Basdat 2026](https://docs.google.com/spreadsheets/d/1cowSMPtWQApyALrypfMBJSOuqbXyGh2cCaDXKRs8fD4/edit?usp=sharing)  
1. Setiap peserta **WAJIB** melakukan *source* data dari sumber yang berbeda dan topik yang diangkat juga harus berbeda secara substansi (Tidak boleh mengangkat topik yang sama dari *source* yang berbeda e.g. tiket kereta api dari aplikasi KAI Access, Traveloka, Tiket.com merupakan topik yang sama dari *source* yang berbeda. Namun, masih diperbolehkan mengangkat tema yang berada dalam domain yang sama, selama topiknya berbeda secara substansi e.g. topik A: Jadwal keberangkatan dan kedatangan kereta dari KAI Access,  topik B: Harga tiket kereta berdasarkan kelas dari Tiket.com).   
2. Setiap peserta **TIDAK DIPERKENANKAN** mengambil *source* data dan topik yang sama dengan peserta Seleksi Asisten Basis Data tahun 2024\.   
3. *First come, first served*. Bila ada dua atau lebih peserta dengan topik yang sama, peserta dengan topik yang sudah terdaftar duluan (berada di atas) akan diprioritaskan.  
4. Akses edit ke spreadsheet topik data scraping akan ditutup pada tanggal tanggal **13 Juli 2026** pukul **22:40 WIB.**  
2. Lakukan *data scraping* dari sebuah *web page* untuk memperoleh data dan informasi sesuai dengan topik yang telah dipilih oleh masing-masing peserta.   
1. Data dan informasi yang diperoleh akan digunakan di *step* berikutnya sebagai data yang akan disimpan di dalam sebuah RDBMS.  
2. Peserta **DILARANG** menggunakan API untuk melakukan proses *data scraping*.  
3. Pada *folder* ***Data Scraping*****,** peserta harus mengumpulkan *file script* dan *file* JSON hasil *scraping* yang telah dilakukan.  
1. *Folder* **src** berisi *script*/*code* yang telah digunakan untuk *scraping*. Pastikan bahwa *script/code* yang kalian buat bersifat ***well documented*** dan ***clean**.*   
2. *Folder* **data** berisi semua data dan informasi yang berhasil kalian *scrape* dalam bentuk JSON. Sebaiknya, data tidak digabungkan ke dalam satu file JSON besar yang memuat berbagai jenis entitas. File JSON sebaiknya dipisahkan berdasarkan jenis data yang diambil, seperti movies.json, actors.json, review.json, dan sebagainya, jangan digabungkan dalam satu file besar.  
4. Sebagai referensi untuk mempelajari dan mengenal *data scraping*, asisten telah menyiapkan dokumen panduan singkat pada link berikut: [Panduan Singkat Data Scraping](https://docs.google.com/document/d/1vEyAK1HIkM792oIuwR4Li2xOodmAcCXxentCCivxxkw/edit?usp=sharing)  
1. Dokumen tersebut hanya merupakan panduan bagi peserta. Metodologi *data scraping* yang digunakan oleh peserta seleksi basdat dibebaskan (asal sesuai aturan).  
2. Perhatikan dan peragakan etika *data scraping* yang baik dalam pelaksanaan seleksi ini.  
5. Syarat data yang diperoleh dari proses *data scraping*: Data yang diperoleh **harus di-*preprocessing* terlebih dahulu.**  
   1. Beberapa contoh *preprocessing:*   
      1. *Cleaning,*  
      2. *Parsing,*  
      3. *Transformation,*   
      4. Dan lain-lain.  
   2. *Preprocessing* dilakukan untuk memastikan data yang diterima tidak sepenuh-penuhnya mentah dan tidak dapat dipahami dengan mudah.

# ***Step 2: Data Modeling \+ Data Storing***

1. Dari hasil proses *data scraping* yang telah dilakukan, lakukan perancangan *database* dalam bentuk **ERD**. Sertakan asumsi dan penjelasan di dalam desain ERD-nya bila diperlukan.  
2. Translasikan hasil desain ERD tersebut ke dalam bentuk diagram relasional. Peserta dipersilakan untuk menambahkan tabel lain yang sekiranya relevan atau berkaitan dengan tabel-tabel yang murni didapatkan dari proses *data scraping*.   
3. Implementasikan skema diagram relasional tersebut ke dalam RDBMS sesuai pilihan peserta (PostgreSQL, MariaDB, etc). Peserta **dilarang** untuk menggunakan DBMS No-SQL.  
   1. Jangan lupa untuk mengimplementasikan *constraints* ke dalam *database* (*primary key, foreign key, trigger, dll*).  
4. Setelah *database*\-nya telah diimplementasikan, masukkan data yang didapatkan dari proses *scraping* ke dalam RDBMS yang telah dibuat.  
   1. Tabel tambahan yang dibuat pada poin 2 tidak perlu diisi dengan data (baik data *dummy* maupun data asli). Cukup dibiarkan kosong.  
5. *Tools* yang digunakan dibebaskan kepada peserta.  
6. Pada *folder **Data Storing***, peserta harus mengumpulkan bukti penyimpanan data pada DBMS. *Folder **Data Storing*** terdiri dari *folder* design, src, export, dan screenshots.  
   1. *Folder* **design** berisi gambar ERD dan gambar diagram relasional dari *database* yang kalian rancang. Format file yang diterima adalah **.png.**  
   2. *Folder* **src** berisi *script*/*code* yang telah digunakan untuk *storing*. Pastikan bahwa *script/code* yang kalian bua bersifat ***well documented*** dan ***clean**.*   
   3. *Folder* **export** berisi file hasil export dari DBMS dengan format **.sql**  
   4. *Folder* **screenshots** berisi tangkapan layar bukti dari penyimpanan data ke dalam RDBMS (Query SELECT FROM WHERE pada RDBMS).

# ***Bonus:***

*Task-task* berikut merupakan *bonus* yang **TIDAK WAJIB** dilakukan oleh peserta seleksi. Penyelesaian satu atau lebih *task* *bonus* akan membawa nilai tambahan bagi peserta yang menyelesaikannya. Peserta dibolehkan untuk mengerjakan **sebagian** atau **seluruh** dari *task* bonus yang tersedia.

1. ***Data Warehouse***   
   Tidak seperti basis data operasional yang biasanya hanya mengambil data dari satu sumber (misalnya interaksi pengguna), *data warehouse* dapat mengintegrasikan data dari berbagai sumber, baik internal maupun eksternal. Hal ini memungkinkan pengguna untuk mendapatkan *insight* yang lebih luas dan mendalam. Selain itu, *database* konvensional umumnya hanya menyimpan data saat ini (*current data*), sedangkan *data warehouse* dirancang untuk menyimpan *historical data*, sehingga analisis tren jangka panjang menjadi mungkin dilakukan.

Secara arsitektur, *data warehouse* terdiri dari dua komponen utama, yaitu *fact table* dan *dimension table*. *Fact table* berisi data kuantitatif atau numerik yang dapat diukur, seperti jumlah penjualan atau total pendapatan, dan biasanya merupakan tabel dengan ukuran terbesar dalam *warehouse*. Sementara itu, *dimension table* menyimpan atribut atau konteks tambahan seperti nama produk, wilayah, atau tanggal, yang digunakan untuk memperkaya interpretasi data pada *fact table*. Hubungan antara *fact table* dan *dimension table* dapat dimodelkan ke dalam tiga jenis skema utama, yaitu: *star schema*, *snowflake schema*, dan *galaxy schema*. Pemilihan jenis skema ini bergantung pada kebutuhan analisis, kompleksitas data, serta tingkat normalisasi yang diinginkan.   
Buatlah **perancangan** dan **implementasi** ***data warehouse*** berdasarkan data yang diperoleh **dari** proses ***data storing***. Rancanglah skema yang diperlukan untuk *fact table* dan *dimension table* (misalnya menggunakan pendekatan *star schema* atau *snowflake schema*) untuk mendukung kebutuhan analitik. Sertakan struktur skema *data warehouse* yang digunakan beserta contoh *query* analitik yang bisa dijalankan terhadap data tersebut. Pada *folder* **Data Storing**, peserta harus mengumpulkan bukti penyimpanan data pada DBMS. *Folder* **Data Warehouse** terdiri dari *folder* design, src, export, dan screenshots.

1. *Folder* **design** berisi gambar ERD dan gambar diagram relasional dari *database* yang kalian rancang. Format file yang diterima adalah **.png**  
2. *Folder* **src** berisi *script*/*code* yang telah digunakan untuk melakukan loading data ke ***data warehouse**.* Pastikan bahwa *script/code* yang kalian bua bersifat ***well documented*** dan ***clean**.*   
3. *Folder* **export** berisi file hasil export dari Data Warehouse dengan format **.sql**  
4. *Folder* **screenshots** berisi tangkapan layar bukti dari penyimpanan data ke dalam RDBMS (Query SELECT FROM WHERE pada RDBMS).  
2. Lakukan ***automated scheduling*** untuk keseluruhan proses, sehingga data dapat di-*update* secara berkala. Pastikan tidak terdapat redundansi data pada DBMS. Jika mengerjakan bonus ini, jelaskan pada README dan cantumkan pada data waktu pelaksanaan *scheduling*, misalnya dengan menunjukkan perbedaan *timestamp* ekstraksi antara data pada *batch* pertama dan data pada *batch* kedua.  
3. Buat **3 *query* optimasi** untuk meningkatkan performa *query* berdasarkan *database* relasional yang telah dibuat dan sertakan bukti bahwa *query* tersebut berhasil menghasilkan *query* yang lebih optimal dengan *output* yang sama dari *query* yang telah dibuat sebelumnya.   
   Query optimasi dibuat di dalam *folder* dengan nama **Query Optimasi** dengan isi:  
1. *Query* optimasi yang digunakan dalam bentuk *format file* **.sql (1 *file* untuk seluruh *query* optimasi yang dibuat)**. Pastikan bahwa Anda menuliskan komentar berupa **penjelasan** terkait fungsi/apa yang dilakukan oleh *query* tersebut.  
2.  *Screenshot* bukti bahwa *query* lebih optimal.

***Penggunaan AI***  
Apabila menggunakan AI, silakan tuliskan **secara detail** pada README:

1. Bagian-bagian yang dibantu AI,  
2. Bagian-bagian yang tetap dikerjakan sendiri,  
3. Refleksi dari penggunaan AI,  
4. Dan detail-detail lainnya

Namun, asisten **tidak menyarankan** peserta untuk langsung melakukan *copy paste* dari hasil kerja AI. Jika peserta terindikasi menggunakan AI tanpa menuliskan bagian ini, peserta akan dikenakan sanksi pengurangan nilai.

# ***Pengumpulan***

1. Peserta diwajibkan untuk melakukan *fork* terhadap *project* GitHub berikut: [https://github.com/wargabasdat/Seleksi-2026-Tugas-1](https://github.com/wargabasdat/Seleksi-2026-Tugas-1). Peserta harus melakukan *pull request* dengan nama **TUGAS\_SELEKSI\_1\_\[NIM\]** sebelum tenggat waktu yang telah ditetapkan.  
2. Tambahkan .gitignore pada *file* atau *folder* yang tidak perlu di-*upload*. NB: Binary tidak perlu di-*upload*.  
3. Sertakan *file* README yang memuat:  
   1. *Author* (Nama dan NIM).  
   2. Deskripsi singkat mengenai data dan DBMS yang telah dibuat \+ mengapa kalian memilih topik tersebut.  
   3. Cara menggunakan *scraper* yang telah dibuat dan menggunakan hasil *output*\-nya.  
   4. Penjelasan struktur dari file JSON yang dihasilkan *scraper*.  
   5. Struktur ERD dan diagram relasional RDBMS.  
   6. Penjelasan mengenai proses translasi ERD menjadi diagram relasional.  
   7. Beberapa *screenshot* dari program yang dijalankan (*image* di-*upload* sesuai *folder-folder* yang tersedia, di README tinggal ditampilkan).  
   8. Referensi (library yang digunakan, halaman *web* yang di-*scrape*, etc).

# ***DEADLINE*** **PENGUMPULAN ADALAH TANGGAL 23 Juli 2026, PUKUL  22:40.**