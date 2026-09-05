# Kualitas Udara Desa Bundah, Kecamatan Sreseh, Kabupaten Sampang

Proyek ini memantau dua polutan udara — **NO2** dan **CO** — di **Desa Bundah,
Kecamatan Sreseh, Kabupaten Sampang, Pulau Madura, Jawa Timur**, menggunakan
data satelit Sentinel-5P (TROPOMI) dari Copernicus, karena tidak ada stasiun
pemantau udara darat (ISPU/OpenAQ) di wilayah ini.

Rentang data: **1 September 2025 – 31 Agustus 2026** (12 bulan terakhir).

```{note}
📌 Buku ini akan terus diperbarui dan ditambah kontennya setiap pertemuan
perkuliahan. Navigasi di sebelah kiri dikelompokkan per pertemuan supaya
mudah diikuti perkembangannya.
```

Isi laporan ini:

- [Profil Penulis](profil.md)
- [Analisis Kualitas Udara](analisis_kualitas_udara.md) — mengikuti alur singkat CRISP-DM:
  1. [Business Understanding](01_business_understanding.md) — tujuan & manfaat
  2. [Data Understanding](02_data_understanding.ipynb) — deskripsi fitur, sumber
     polutan, eksplorasi & anomali data
  3. [Data Collection & Time Series](03_data_collection_dan_visualisasi.ipynb) —
     crawling data dengan batas wilayah GeoJSON, penyimpanan CSV, dan grafik
     time series
- [Migrasi Cloud & Statistik KNIME](04_migrasi_dan_statistik_knime.md) —
  memindahkan data ke Aiven PostgreSQL dan menganalisis statistik deskriptif
  di KNIME