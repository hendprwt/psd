# 4. Migrasi Data ke Cloud (Aiven) & Statistik di KNIME

## 4.1 Ringkasan alur

Data time series NO2 & CO yang sudah dihasilkan minggu lalu
(`data/kualitas_udara_bundah_sreseh.csv`) dipindahkan ke database cloud
**Aiven PostgreSQL**, lalu ditarik ke **KNIME Analytics Platform** untuk
eksplorasi statistik lebih lanjut.

```{note}
🔒 Jangan taruh Service URI/host/password Aiven yang **asli** di halaman
ini atau file manapun yang di-push ke repo publik. Contoh di bawah sengaja
memakai placeholder.
```

Alur singkatnya:

1. Buat tabel di Aiven lewat PG Studio.
2. Hubungkan Aiven ke DBeaver, import CSV ke tabel tersebut.
3. Hubungkan Aiven ke KNIME (PostgreSQL Connector → DB Table Selector → DB
   Reader).
4. Tambahkan node **Statistics** untuk melihat ringkasan statistik semua
   kolom numerik (`no2`, `co`) sekaligus.

## 4.2 Struktur tabel di Aiven

```sql
CREATE TABLE kualitas_udara_bundah (
    date TIMESTAMP,
    no2  NUMERIC,
    co   NUMERIC
);
```

Koneksi DBeaver/KNIME memakai parameter berikut (ganti dengan kredensial
kamu sendiri dari dashboard Aiven, dan pastikan `sslmode=require`):

| Parameter | Nilai |
|---|---|
| Host | `<host-aiven-kamu>.aivencloud.com` |
| Port | `<port-aiven-kamu>` |
| Database | `defaultdb` |
| User | `avnadmin` |
| Password | *(ambil dari dashboard Aiven, jangan hardcode di file publik)* |
| SSL mode | `require` |

## 4.3 Node Statistics — penjelasan, rumus, dan contoh perhitungan

Node **Statistics** di KNIME menghitung beberapa ringkasan sekaligus untuk
setiap kolom numerik (`no2` dan `co`). Supaya perhitungannya mudah
ditelusuri manual, contoh di bawah memakai **5 hari pertama** dari dataset
asli (bukan keseluruhan 362 hari):

| No | Tanggal | NO2 (mol/m²) | CO (mol/m²) |
|---|---|---|---|
| 1 | 2025-09-01 | 0.000014 | 0.028432 |
| 2 | 2025-09-02 | 0.000016 | 0.023283 |
| 3 | 2025-09-03 | 0.000011 | 0.024006 |
| 4 | 2025-09-04 | 0.000033 | 0.029112 |
| 5 | 2025-09-05 | 0.000019 | 0.031187 |

Contoh perhitungan di bawah pakai kolom **CO** (n = 5), karena angkanya
lebih mudah dibaca manual. Cara yang sama berlaku persis untuk NO2.

---

### a. Row Count (jumlah baris)

Jumlah total baris/observasi yang dibaca node DB Reader.

$$n = \\text{jumlah baris pada tabel}$$

**Contoh:** dari 5 baris contoh di atas, $n = 5$. Untuk dataset penuh
(1 Sep 2025 – 31 Agu 2026), $n = 362$ hari.

### b. Missing Value (nilai kosong)

Jumlah baris di mana nilai kolom tersebut `NULL`/kosong — biasanya karena
hari itu tertutup awan sehingga satelit tidak menghasilkan pembacaan valid.

$$\\text{Missing} = \\sum_{i=1}^{n} \\mathbb{1}(x_i = \\text{NULL})$$

**Contoh:** pada 5 baris contoh di atas, missing = 0 (semua terisi).
Tapi untuk dataset penuh, hasil eksplorasi minggu lalu menunjukkan CO
kosong di **190 dari 362 hari** (± 52,5%) — karena tutupan awan musim
hujan.

### c. Minimum & Maximum

Nilai terkecil dan terbesar dalam kolom — dipakai untuk mendeteksi nilai
tak wajar (outlier).

$$\\text{Min} = \\min(x_1, x_2, ..., x_n) \\qquad \\text{Max} = \\max(x_1, x_2, ..., x_n)$$

**Contoh (CO):**
$$\\text{Min} = 0.023283 \\qquad \\text{Max} = 0.031187$$

### d. Sum (jumlah total)

$$\\text{Sum} = \\sum_{i=1}^{n} x_i$$

**Contoh (CO):**
$$0.028432 + 0.023283 + 0.024006 + 0.029112 + 0.031187 = 0.136020$$

### e. Mean (rata-rata)

$$\\bar{x} = \\frac{1}{n}\\sum_{i=1}^{n} x_i = \\frac{\\text{Sum}}{n}$$

**Contoh (CO):**
$$\\bar{x} = \\frac{0.136020}{5} = 0.027204 \\text{ mol/m}^2$$

### f. Median (nilai tengah)

Urutkan data dari kecil ke besar, ambil nilai di tengah (kalau $n$ genap,
rata-rata dua nilai tengah).

**Contoh (CO):** data diurutkan → `0.023283, 0.024006, 0.028432, 0.029112, 0.031187`
Karena $n=5$ (ganjil), median = nilai ke-3 = **0.028432**.

### g. Variance (ragam)

Mengukur seberapa jauh nilai-nilai menyebar dari rata-ratanya. KNIME
memakai **sample variance** (pembagi $n-1$):

$$s^2 = \\frac{1}{n-1}\\sum_{i=1}^{n} (x_i - \\bar{x})^2$$

**Contoh (CO)**, dengan $\\bar{x} = 0.027204$:

| $x_i$ | $x_i - \\bar{x}$ | $(x_i-\\bar{x})^2$ |
|---|---|---|
| 0.028432 | 0.001228 | 0.0000015 |
| 0.023283 | -0.003921 | 0.0000154 |
| 0.024006 | -0.003198 | 0.0000102 |
| 0.029112 | 0.001908 | 0.0000036 |
| 0.031187 | 0.003983 | 0.0000159 |

Jumlah $(x_i-\\bar{x})^2 = 0.0000466$

$$s^2 = \\frac{0.0000466}{5-1} = 0.00001165$$

### h. Standard Deviation (simpangan baku)

Akar dari variance — dalam satuan yang sama dengan data aslinya, jadi
lebih mudah diinterpretasi daripada variance.

$$s = \\sqrt{s^2}$$

**Contoh (CO):**
$$s = \\sqrt{0.00001165} \\approx 0.003414 \\text{ mol/m}^2$$

Ini sejalan dengan hasil `describe()` di notebook Data Understanding untuk
seluruh dataset (172 hari valid), yang menunjukkan std CO ≈ 0.003667 —
nilainya masuk akal karena contoh kecil ini cuma memakai 5 dari 362 hari.

---

### Ringkasan tabel Statistics (interpretasi untuk dataset penuh)

| Statistik | NO2 (362 hari, 190 valid) | CO (362 hari, 172 valid) | Arti |
|---|---|---|---|
| Missing | 172 hari (47,5%) | 190 hari (52,5%) | Hari tertutup awan/tanpa data valid |
| Min | -0.000022 | 0.014774 | Nilai NO2 negatif = derau retrieval, bukan emisi negatif |
| Max | 0.000052 | 0.038664 | Kemungkinan lonjakan pembakaran lahan |
| Mean | 0.000021 | 0.028697 | Tingkat dasar konsentrasi polutan |
| Median | 0.000020 | 0.028716 | Mirip dengan mean → distribusi relatif simetris |
| Std. Dev | 0.000011 | 0.003667 | Sebaran data relatif kecil, cukup stabil |

## 4.4 Pra-pemrosesan lanjutan di KNIME

Setelah node Statistics, alur pra-pemrosesan yang sama seperti time series
pada umumnya:

- **String to Date&Time**: memastikan kolom `date` dikenali sebagai
  format waktu, bukan teks.
- **Missing Value**: mengisi hari-hari kosong (akibat tutupan awan) dengan
  interpolasi linear, supaya time series tidak terputus untuk keperluan
  visualisasi/pemodelan lanjutan.
- **GroupBy / Time Series Aggregation**: merangkum data harian menjadi
  rata-rata mingguan/bulanan untuk melihat tren jangka panjang lebih
  jelas (sudah dicoba sebelumnya di notebook 03 versi Python).
