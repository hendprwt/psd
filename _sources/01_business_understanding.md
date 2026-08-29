# 1. Business Understanding

## 1.1 Latar Belakang & Konteks Wilayah

**Desa Bundah** adalah salah satu dari 12 desa di **Kecamatan Sreseh,
Kabupaten Sampang**, Pulau Madura, Provinsi Jawa Timur. Kecamatan ini
terletak sekitar 43 km dari pusat Kabupaten Sampang, dengan karakteristik
wilayah pedesaan-pesisir: mata pencaharian dominan nelayan dan petani,
akses jalan kabupaten yang relatif sepi dibanding kota besar, serta belum
adanya infrastruktur pemantauan lingkungan modern.

Beberapa fakta konteks yang relevan untuk proyek ini:

- **Tidak ada stasiun pemantau udara resmi** di wilayah ini — baik ISPU
  (Indeks Standar Pencemar Udara) dari KLHK maupun titik komunitas seperti
  OpenAQ. Pemantauan semacam ini umumnya hanya tersedia di kota-kota besar
  seperti Surabaya atau Malang.
- **Sumber emisi lokal tetap ada** meski wilayahnya pedesaan: kendaraan
  bermotor di jalur Sreseh–Blega, mesin diesel kapal nelayan di pesisir,
  pembakaran lahan/jerami sisa panen (terutama menjelang musim kemarau),
  dan dapur rumah tangga berbahan bakar kayu.
- **Karakteristik iklim tropis muson**: musim hujan (± November–April) dan
  musim kemarau (± Mei–Oktober) yang memengaruhi baik pola emisi
  (pembakaran lahan lebih sering di musim kemarau) maupun kualitas data
  satelit (tutupan awan lebih tinggi di musim hujan).
- **Ketiadaan data historis** membuat wilayah ini belum pernah punya
  gambaran kuantitatif tentang kualitas udaranya sendiri — proyek ini jadi
  upaya pertama untuk mengisi kekosongan tersebut, memanfaatkan data
  penginderaan jauh (satelit Sentinel-5P) sebagai pengganti sensor darat
  yang tidak tersedia.

## 1.2 Tujuan Proyek

### Tujuan Bisnis (Business Objectives)

1. Mengetahui gambaran kualitas udara di Desa Bundah, Kecamatan Sreseh,
   Kabupaten Sampang, yang selama ini tidak pernah terpantau.
2. Mengidentifikasi apakah ada pola musiman atau kejadian tertentu (mis.
   pembakaran lahan) yang memengaruhi kualitas udara desa.
3. Menyediakan bahan/basis data awal yang bisa dipakai pemerintah desa,
   kecamatan, atau warga sebagai referensi jika suatu saat diperlukan
   diskusi terkait lingkungan.

### Tujuan Teknis (Technical/Data Science Objectives)

1. Membangun pipeline crawling data konsentrasi **NO2** dan **CO** dari
   citra satelit Sentinel-5P, dibatasi secara spasial menggunakan polygon
   GeoJSON wilayah Desa Bundah.
2. Mengumpulkan data time series selama minimal **1 tahun**, dari
   **1 September 2025 sampai 31 Agustus 2026**.
3. Menyimpan hasil crawling dalam format **CSV** terstruktur (kolom
   tanggal, NO2, CO) agar mudah diproses ulang.
4. Melakukan eksplorasi data (statistik deskriptif, distribusi, deteksi
   nilai kosong/outlier) untuk memahami kualitas dan keterbatasan data.
5. Memvisualisasikan hasil sebagai **grafik time series** yang mudah
   dibaca.
6. Mempublikasikan seluruh proses dan hasil sebagai laporan web statis
   (Jupyter Book) yang bisa diakses publik lewat GitHub Pages.

## 1.3 Manfaat

- **Bagi warga & pemerintah desa/kecamatan**: baseline data kualitas udara
  pertama untuk wilayah ini, sebagai titik awal pemantauan berkelanjutan
  dan bahan diskusi kebijakan (mis. terkait pembakaran lahan terbuka).
- **Bagi edukasi masyarakat**: data yang divisualisasikan dalam grafik
  jauh lebih mudah dipahami dibanding angka mentah, dan bisa jadi materi
  sosialisasi dampak pembakaran biomassa/emisi kendaraan terhadap kualitas
  udara.
- **Bagi pengembangan lanjutan**: pipeline yang dibangun (geojson → openEO
  → CSV → visualisasi → Jupyter Book) bersifat generik, sehingga mudah
  dipakai ulang untuk desa lain, polutan lain (SO2, O3, CH4, aerosol
  index), atau rentang waktu lain.
- **Bagi pembelajaran teknis (pribadi)**: melatih alur kerja data science
  end-to-end sesuai kerangka CRISP-DM — mulai dari pemahaman masalah,
  pengambilan data dari API/satelit, pembatasan wilayah spasial,
  penyimpanan data terstruktur, eksplorasi data, sampai visualisasi dan
  publikasi laporan.

## 1.4 Rencana Proyek

Proyek ini mengikuti alur singkat berbasis CRISP-DM:

| Tahap | Kegiatan | Output |
|---|---|---|
| 1. Business Understanding | Menentukan tujuan, manfaat, dan batasan proyek | Dokumen ini |
| 2. Data Understanding | Mendeskripsikan fitur (NO2, CO), sumber data, eksplorasi awal, identifikasi anomali | `02_data_understanding.ipynb` |
| 3. Data Collection | Menentukan batas wilayah (GeoJSON), crawling data satelit via openEO/CDSE, menyimpan ke CSV | `03_data_collection_dan_visualisasi.ipynb`, `data/*.csv` |
| 4. Visualisasi & Analisis | Membuat grafik time series (harian & agregat mingguan), menandai anomali | Grafik di notebook 03 |
| 5. Deployment | Build & publish sebagai Jupyter Book ke GitHub Pages | Website `https://<username>.github.io/PSD/intro.html` |

## 1.5 Batasan Proyek (Scope & Limitations)

- Data berasal dari **satelit (Sentinel-5P/TROPOMI)**, bukan pengukuran
  langsung di permukaan tanah — nilainya mewakili rata-rata kolom udara di
  atas wilayah Desa Bundah (resolusi spasial ± 3.5 × 7 km), bukan titik
  spesifik seperti di depan rumah warga tertentu.
- Polutan yang dianalisis dibatasi pada **NO2 dan CO** saja, karena
  keduanya paling relevan dengan sumber emisi lokal (transportasi, mesin
  diesel, pembakaran biomassa) dan tersedia harian dari sensor yang sama.
  Polutan lain (SO2, O3, CH4, aerosol index) berada di luar cakupan versi
  ini, meski bisa ditambahkan dengan pipeline yang sama.
- Rentang waktu dibatasi **1 September 2025 – 31 Agustus 2026** (12 bulan
  terakhir), sesuai ketentuan tugas.
- Batas wilayah menggunakan **polygon GeoJSON hasil gambar manual** di
  geojson.io (perkiraan area Desa Bundah), bukan data batas administratif
  resmi presisi tinggi dari BIG/BPS.
- Akan ada **hari-hari tanpa data** akibat tutupan awan tebal, karena
  sensor optik TROPOMI tidak bisa menembus awan — ini keterbatasan
  inheren dari data satelit optik, bukan kegagalan proses crawling.
- Proyek ini bersifat **deskriptif** (menggambarkan kondisi & tren), belum
  masuk ke tahap pemodelan prediktif atau analisis kausal formal.

## 1.6 Kriteria Keberhasilan

Proyek dianggap berhasil jika:

1. Data NO2 dan CO berhasil diambil dan tersimpan sebagai CSV time series
   dengan cakupan minimal 1 tahun (1 Sep 2025 – 31 Agu 2026).
2. Eksplorasi data understanding berhasil mengidentifikasi karakteristik
   dan anomali data secara wajar (bukan asal-asalan).
3. Grafik time series (harian dan/atau agregat mingguan) berhasil dibuat
   dan merepresentasikan tren dengan jelas.
4. Seluruh proses terdokumentasi dan dipublikasikan sebagai web statis
   (Jupyter Book) yang bisa diakses lewat GitHub Pages.