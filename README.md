# PSD — Kualitas Udara Desa Bundah, Kecamatan Sreseh, Kabupaten Sampang

Tugas mata kuliah Pengantar Sains Data: memantau kualitas udara (NO2 & CO) di
wilayah sendiri, disimpan sebagai time series CSV, dan dipublikasikan sebagai
web statis (Jupyter Book).

Wilayah studi: **Desa Bundah, Kecamatan Sreseh, Kabupaten Sampang, Madura,
Jawa Timur** (titik tengah kira-kira -7.1781, 113.0548).

## Kenapa data satelit, bukan sensor darat?

Tidak ada stasiun ISPU (KLHK) atau titik OpenAQ di Sreseh — daerah ini pedesaan
pesisir tanpa alat pemantau udara darat. Solusinya: pakai data satelit
**Sentinel-5P (TROPOMI)** dari Copernicus, yang meng-cover seluruh permukaan
bumi tiap hari. Ini juga persis yang dipakai di contoh notebook dosen
(`NO2Covid.ipynb`, pakai `openeo` + Copernicus Data Space Ecosystem/CDSE).

## Struktur folder

```
PSD/
├── README.md
├── requirements.txt
├── geojson/
│   └── bundah_sreseh_sampang.geojson   <- batas wilayah (perhalus di geojson.io)
├── data/
│   └── (CSV hasil crawling disimpan di sini)
└── materi/                              <- isi Jupyter Book
    ├── _config.yml
    ├── _toc.yml
    ├── intro.md
    ├── 01_business_understanding.md
    ├── 02_data_understanding.ipynb
    └── 03_data_collection_dan_visualisasi.ipynb
```

## Setup di lokal (Windows) — versi yang sudah dikoreksi

Alur yang kamu tulis sudah hampir benar, cuma `py install 3.12` bukan
perintah yang valid. Ini urutan yang benar:

1. **Install Python 3.12** dari https://www.python.org/downloads/ (centang
   "Add py.exe to PATH" saat instalasi). Ini pakai installer resmi, bukan
   command line.
2. Buka terminal di folder proyek:
   ```
   cd "C:\Users\HYPE AMD\Documents\kuliah\psd"
   ```
3. Buat virtual environment dengan Python 3.12:
   ```
   py -3.12 -m venv .venv
   ```
4. Aktifkan venv:
   ```
   .venv\Scripts\activate
   ```
5. Install semua dependency sekaligus (bukan cuma jupyter-book):
   ```
   pip install -r requirements.txt
   ```
6. Cek jupyter-book terpasang:
   ```
   jb --version
   ```
7. **Kalau folder `materi` belum ada isinya**, baru jalankan `jb create materi`
   (ini hanya dijalankan SEKALI untuk scaffolding awal). Kalau kamu pakai
   struktur dari zip ini, lewati langkah ini — filenya sudah disiapkan.
8. Jalankan notebook `02_data_understanding.ipynb` dan
   `03_data_collection_dan_visualisasi.ipynb` di Jupyter/VS Code sampai
   semua cell ada outputnya (grafik, tabel) — Jupyter Book hanya merender
   output yang sudah tersimpan, tidak menjalankan ulang notebook secara
   default (lihat `_config.yml`, `execute_notebooks: "off"`).
9. Build web statisnya:
   ```
   jb build materi
   ```
   Hasilnya ada di `materi/_build/html/`, buka `index.html` untuk preview.

## Push ke GitHub & deploy ke GitHub Pages

```
git init
git add .
git commit -m "Tugas PSD: kualitas udara Desa Bundah"
git branch -M main
git remote add origin https://github.com/<username-kamu>/PSD.git
git push -u origin main

pip install ghp-import
ghp-import -n -p -f materi/_build/html
```

Setelah itu aktifkan GitHub Pages dari branch `gh-pages` di Settings repo.
Hasil akhirnya akan tampil di:
`https://<username-kamu>.github.io/PSD/intro.html`
— sama persis pola contoh yang dikasih dosen.

## Sumber data & credential

Notebook `03_data_collection_dan_visualisasi.ipynb` butuh akun gratis di
https://dataspace.copernicus.eu/ (untuk openEO/CDSE) — proses login
memakai OAuth device flow lewat browser saat `connection.authenticate_oidc()`
dipanggil, jadi **harus dijalankan di komputer kamu sendiri**, bukan lewat
Claude, karena sandbox ini tidak punya akses internet ke server Copernicus.
