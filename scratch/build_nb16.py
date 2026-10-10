import nbformat as nbf

nb = nbf.v4.new_notebook()

def md(text): nb.cells.append(nbf.v4.new_markdown_cell(text))
def code(text): nb.cells.append(nbf.v4.new_code_cell(text))

# ============================================================
# JUDUL & PENDAHULUAN
# ============================================================
md("""# Pemetaan Penggunaan dan Tutupan Lahan (LULC) Jawa Timur
## Citra Sentinel-2A · Random Forest · Streamlit Web GIS · Folium + Google Satellite

> **Mata Kuliah:** Sistem Informasi Geografis — Analisis Spasial Penggunaan Lahan & Kebijakan  
> **Dataset:** Shapefile poligon hasil digitasi manual + Citra Sentinel-2A Level-2A (Copernicus Data Space)

---

Notebook ini menjabarkan alur kerja **end-to-end** pemetaan tutupan/penggunaan lahan di Jawa Timur: dari pemahaman data, pengumpulan citra satelit, ekstraksi fitur spektral, hingga pelatihan model dan penayangan peta interaktif di atas citra Google Maps. Selain dokumentasi analitik di sini, sistem informasi geografisnya juga diwujudkan sebagai **aplikasi web Streamlit** yang dapat di-*deploy* secara publik.

## Daftar Isi
1. [Data Understanding](#1-data-understanding)
2. [Data Collection](#2-data-collection)
3. [Deskripsi Fitur & Rumus](#3-deskripsi-fitur--rumus)
4. [Eksplorasi Data (EDA)](#4-eksplorasi-data-eda)
5. [Pemodelan Klasifikasi — Eksperimen Multi-Model](#5-pemodelan-klasifikasi--eksperimen-multi-model)
6. [Eksperimen Lanjutan (Hyperparameter & Kombinasi Fitur)](#6-eksperimen-lanjutan)
7. [Peta Hasil Klasifikasi (Folium + Google Satellite)](#7-peta-hasil-klasifikasi)
8. [Kesimpulan](#8-kesimpulan)
""")

# ============================================================
# BAB 1 — DATA UNDERSTANDING
# ============================================================
md("""## 1. Data Understanding

### 1.1 Konteks dan Urgensi Analisis

Pertumbuhan penduduk yang cepat di Jawa Timur mendorong alih fungsi lahan secara masif — area persawahan tergerus permukiman, mangrove pesisir berkurang, dan kawasan industri terus meluas. Memantau perubahan ini secara manual tidak efisien dan mahal. Citra multispektral **Sentinel-2A** menyediakan rekaman permukaan bumi setiap ~5 hari dengan resolusi 10 meter secara gratis, sehingga sangat ideal untuk pemetaan tutupan lahan berbasis *machine learning*.

### 1.2 Tujuan Analisis Land Use and Land Cover (LULC)

Analisis ini memiliki beberapa sasaran konkret:

1. **Klasifikasi tutupan lahan** — Memetakan wilayah Jawa Timur ke dalam **6 kelas LULC** (sawah, rumah/permukiman, laut/perairan terbuka, mangrove, lahan hijau, danau/ranu) berdasarkan nilai reflektansi Sentinel-2A beserta indeks spektral turunannya.

2. **Pemahaman karakteristik spektral per kelas** — Mengidentifikasi kombinasi band dan indeks yang paling efektif membedakan satu kelas dari kelas lain (misalnya: mangrove vs. lahan hijau, atau danau vs. sawah yang tergenang).

3. **Perbandingan dan seleksi model** — Menguji beberapa algoritma klasifikasi (*Random Forest, Support Vector Machine, Gradient Boosting, K-Nearest Neighbors*) dan memilih yang menghasilkan akurasi, Kappa, dan F1-score tertinggi.

4. **Eksperimen sistematis** — Menyelidiki pengaruh rasio train/test split, kombinasi fitur, dan hyperparameter model terhadap kinerja prediksi.

5. **Peta interaktif** — Menampilkan hasil prediksi piksel skala Jawa Timur di atas citra satelit Google/Esri melalui Folium dan mengemas semuanya menjadi aplikasi web GIS Streamlit yang dapat diakses publik.

### 1.3 Wilayah Studi

Wilayah cakupan adalah **Provinsi Jawa Timur, Indonesia** (koordinat approx. 111°–114,6° Bujur Timur; 6,5°–8,8° Lintang Selatan). Keragaman lanskap Jawa Timur sangat tinggi: dari dataran pesisir bermangrove di utara dan selatan, hamparan persawahan di Sidoarjo–Mojokerto, kawasan industri Surabaya–Gresik, lahan hijau (hutan) di pegunungan tengah, hingga danau-danau volcanic (Ranu Grati, Ranu Lamongan, dll.).

### 1.4 Kelas LULC dan Sumber Data Referensi

Data latih berupa **shapefile poligon** yang diperoleh dari digitasi manual menggunakan citra satelit resolusi tinggi. Sistem ini menggunakan **6 kelas** yang sesuai dengan kategori tutupan lahan dalam SNI 7645:2010 (Klasifikasi Tutupan Lahan Indonesia):

| ID | Kelas | File Shapefile | Keterangan |
|---|---|---|---|
| 1 | Sawah | `sawah_surabaya.shp` | Lahan pertanian padi berawa/irigasi |
| 2 | Rumah/Permukiman | `rumah_jatim.shp` | Area perumahan dan hunian padat |
| 3 | Laut | `input.shp` | Perairan terbuka dan lepas pantai |
| 4 | Mangrove | `mangrove_surabaya.shp` | Hutan mangrove pesisir |
| 5 | Lahan Hijau | `lahan_hijau_jatim.shp` | Hutan, kebun, RTH, vegetasi umum |
| 6 | Danau/Ranu | `danau_jatim.shp` | Danau vulkanik (Ranu-ranu) & waduk |

> **Acuan SNI 7645:2010** — Klasifikasi tutupan lahan Indonesia menggunakan hierarki bertingkat. Kelas yang dipakai di sini termasuk dalam kategori Level II (Lahan Bervegetasi Terbudidayakan: Sawah; Lahan Terbangun: Permukiman; Lahan Bervegetasi Alami: Mangrove, Hutan; Perairan: Danau/Waduk, Laut).

### 1.5 Band Sentinel-2A — Deskripsi Lengkap

Sentinel-2A membawa sensor **MSI (MultiSpectral Instrument)** yang merekam 13 saluran spektral dari UV-tampak hingga SWIR. Produk yang digunakan adalah **Level-2A (Surface Reflectance)** — citra yang sudah terkoreksi atmosfer oleh algoritma Sen2Cor, sehingga nilai piksel merepresentasikan reflektansi permukaan nyata (skala 0–1).

| Band | Nama | Panjang Gelombang (nm) | Resolusi | Fungsi Utama | Digunakan? |
|---|---|---|---|---|---|
| B1 | Coastal Aerosol | 443 | 60 m | Koreksi aerosol & studi perairan pesisir | ❌ |
| B2 | Blue (Biru) | 492 | 10 m | Penetrasi air, deteksi sedimen, diskriminasi vegetasi/bangunan | ✅ |
| B3 | Green (Hijau) | 560 | 10 m | Puncak pantulan klorofil, indeks air | ✅ |
| B4 | Red (Merah) | 665 | 10 m | Penyerapan klorofil, diskriminasi vegetasi vs lahan terbuka | ✅ |
| B5 | Red Edge 1 | 704 | 20 m | Konsentrasi klorofil, kesehatan vegetasi | ✅ |
| B6 | Red Edge 2 | 740 | 20 m | Struktur kanopi, indeks vegetasi tingkat lanjut | ✅ |
| B7 | Red Edge 3 | 783 | 20 m | Biomassa, tutupan kanopi | ✅ |
| B8 | NIR (Near-Infrared) | 833 | 10 m | Biomassa vegetasi, diskriminasi daratan/air | ✅ |
| B8A | Narrow NIR (Red Edge 4) | 865 | 20 m | Kadar air vegetasi, koreksi vegetasi | ✅ |
| B9 | Water Vapour | 945 | 60 m | Koreksi uap air atmosfer | ❌ |
| B10 | SWIR-Cirrus | 1374 | 60 m | Deteksi awan tipis (Cirrus) — tidak ada di L2A | ❌ |
| B11 | SWIR 1 | 1614 | 20 m | Kelembapan vegetasi/tanah, area terbangun, pembeda air | ✅ |
| B12 | SWIR 2 | 2202 | 20 m | Tanah terbuka, area terbangun, jejak kebakaran | ✅ |

> **Catatan:** Band B1, B9, B10 dikecualikan karena dirancang untuk koreksi atmosfer — bukan untuk diskriminasi jenis tutupan lahan. Pada produk L2A, B10 (cirrus) tidak tersedia sama sekali.

### 1.6 Alur Kerja Sistem

```
Shapefile (6 Kelas)
       ↓
Ekstraksi Titik Sampel
       ↓
Download Citra Sentinel-2A (Copernicus CDSE API)
       ↓  ← Komposit Median + Masking SCL (Awan)
Kalkulasi 8 Indeks Spektral (NDVI, NDWI, MNDWI, NDBI, NDRE, EVI, SAVI, BSI)
       ↓
Dataset CSV (10 band + 8 indeks = 18 fitur)
       ↓
EDA → Tanda Tangan Spektral, Boxplot, Heatmap Korelasi
       ↓
Train/Test Split (Stratified 80:20)
       ↓
Eksperimen Multi-Model (RF, SVM, GBM, KNN)
       ↓
Hyperparameter Tuning (GridSearchCV + RepeatedKFold)
       ↓
Prediksi Seluruh Piksel AOI (Tiled Inference)
       ↓
Peta Interaktif Folium (Google/Esri Satellite)
       ↓
Aplikasi Streamlit (deploy publik)
```
""")

# ============================================================
# BAB 2 — DATA COLLECTION
# ============================================================
md("""## 2. Data Collection

### 2.1 Persiapan Lingkungan dan Konfigurasi Global

Seluruh citra satelit diambil dari **Copernicus Data Space Ecosystem (CDSE)** melalui **Sentinel Hub Process API** yang gratis (terdapat kuota bulanan). Keunggulan pendekatan API ini dibanding mengunduh file citra penuh: server Copernicus yang mengerjakan komposit median dan masking awan, sehingga hanya nilai piksel bersih yang ditransfer ke komputer lokal.

**Cara mendapatkan kredensial CDSE (cukup sekali):**
1. Buat akun gratis di [dataspace.copernicus.eu](https://dataspace.copernicus.eu).
2. Login → buka [Sentinel Hub Dashboard](https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings).
3. Pilih *OAuth clients* → *Create new* → beri nama → klik *Create*.
4. Salin **Client ID** dan **Client Secret** (Secret hanya tampil sekali!).
5. Saat notebook dijalankan, masukkan keduanya ke prompt, atau set sebagai environment variable `CDSE_CLIENT_ID` dan `CDSE_CLIENT_SECRET`.

> ⚠️ **Jangan tulis Secret langsung di notebook** yang akan dipublikasikan di web statis!
""")

code("""# Uncomment untuk instalasi (restart kernel setelahnya)
# %pip install -q geopandas sentinelhub folium seaborn scikit-learn pillow requests
""")

code("""import os, math, time, getpass, warnings, io
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import geopandas as gpd
import folium
from folium.raster_layers import ImageOverlay
from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union
from IPython.display import display, Markdown
from concurrent.futures import ThreadPoolExecutor

import requests
from PIL import Image

from sentinelhub import (SHConfig, SentinelHubRequest, DataCollection, BBox, CRS,
                         MimeType, bbox_to_dimensions)

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import (train_test_split, RepeatedStratifiedKFold,
                                     cross_val_score, GridSearchCV)
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             cohen_kappa_score, f1_score)

import joblib

# ──────────────────────────────────────────────────────────────
# DIREKTORI KERJA
# ──────────────────────────────────────────────────────────────
DIR_KERJA = os.path.dirname(os.path.abspath("__file__")) if "__file__" in dir() else os.getcwd()
DIR_DATA  = os.path.join(DIR_KERJA, "..", "data", "digitasi")

print("Direktori kerja  :", DIR_KERJA)
print("Direktori data   :", os.path.abspath(DIR_DATA))
""")

code("""# ──────────────────────────────────────────────────────────────
# KONFIGURASI UTAMA — sesuaikan di sini saja
# ──────────────────────────────────────────────────────────────

# Rentang waktu pencarian citra Sentinel-2A
TGL_AWAL  = "2025-01-01"
TGL_AKHIR = "2025-12-31"
BATAS_AWAN = 30              # maksimum persen tutupan awan per scene (filter awal)
HANYA_2A   = False           # True = buang citra dari Sentinel-2B/2C/2D

ANGKA_ACAK = 42              # seed untuk reproduktibilitas
BERKAS_CSV = os.path.join(DIR_KERJA, "dataset_lulc_jatim.csv")
ULANGI_UNDUH = False         # True = paksa ekstraksi ulang dari Copernicus

# ──────────────────────────────────────────────────────────────
# DEFINISI 6 KELAS LULC
# ──────────────────────────────────────────────────────────────
DEFINISI_KELAS = {
    1: dict(label="Sawah",         berkas="sawah_surabaya",              jml_target=60, warna="#F4D03F"),
    2: dict(label="Rumah",         berkas="rumah_jatim",                 jml_target=60, warna="#E74C3C"),
    3: dict(label="Laut",          berkas="input",                       jml_target=35, warna="#0D47A1"),
    4: dict(label="Mangrove",      berkas="mangrove_surabaya",           jml_target=60, warna="#1E8449"),
    5: dict(label="Lahan Hijau",   berkas="lahan_hijau_jatim",           jml_target=60, warna="#27AE60"),
    6: dict(label="Danau",         berkas="danau_jatim",                 jml_target=50, warna="#2E86C1"),
}

DAFTAR_KELAS = [v["label"] for v in DEFINISI_KELAS.values()]
PALET_WARNA  = {v["label"]: v["warna"] for v in DEFINISI_KELAS.values()}
JML_TARGET   = sum(v["jml_target"] for v in DEFINISI_KELAS.values())

print(f"Kelas LULC ({len(DEFINISI_KELAS)})  :", DAFTAR_KELAS)
print(f"Target total sampel : {JML_TARGET}")
""")

md("""### 2.2 Pemuatan Shapefile Referensi

Setiap shapefile berisi poligon area contoh hasil digitasi manual. Kode ini memeriksa dan menyeragamkan sistem koordinat ke EPSG:4326 (WGS-84 geografis), memperbaiki geometri tidak valid, serta menghitung luas area (dalam Hektar) menggunakan CRS proyeksi UTM 49S.""")

code("""def muat_shp(jalur):
    \"\"\"Muat shapefile, perbaiki CRS dan geometri tidak valid.\"\"\"
    gdf = gpd.read_file(jalur)
    # Standarisasi ke EPSG:4326
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    # Hapus geometri kosong / null
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    # Perbaiki self-intersection dan geometri rusak
    gdf["geometry"] = gdf.geometry.apply(lambda g: g if g.is_valid else g.buffer(0))
    return gdf[["geometry"]].reset_index(drop=True)

def cari_shp(nama_berkas):
    \"\"\"Cari file .shp di seluruh subfolder DIR_DATA secara rekursif.\"\"\"
    nama_target = nama_berkas.lower()
    for root, _, files in os.walk(DIR_DATA):
        for f in files:
            if f.lower().endswith(".shp") and f[:-4].lower() == nama_target:
                return os.path.join(root, f)
    raise FileNotFoundError(
        f"Tidak ditemukan: {nama_berkas}.shp di '{os.path.abspath(DIR_DATA)}'")

# ─ Muat semua shapefile ─
jalur_shp  = {k: cari_shp(v["berkas"]) for k, v in DEFINISI_KELAS.items()}
koleksi_shp = {k: muat_shp(p)          for k, p in jalur_shp.items()}

# ─ Tampilkan ringkasan ─
baris_ringkas = []
for k, v in DEFINISI_KELAS.items():
    gdf = koleksi_shp[k]
    luas_ha = gdf.to_crs(32749).area.sum() / 1e4   # EPSG:32749 (UTM 49S) → Ha
    bb = gdf.total_bounds
    baris_ringkas.append({
        "ID": k, "Kelas": v["label"], "N Poligon": len(gdf),
        "Luas (Ha)": round(luas_ha, 1), "Target Sampel": v["jml_target"],
        "BT Min": round(bb[0], 3), "LS Min": round(bb[1], 3),
        "BT Max": round(bb[2], 3), "LS Max": round(bb[3], 3),
    })

df_ringkas = pd.DataFrame(baris_ringkas).set_index("ID")
display(df_ringkas)
""")

md("""### 2.3 Pemilihan Titik Sampel

Titik sampel dipilih secara acak dari interior poligon menggunakan fungsi `representative_point()` (satu titik per poligon yang dijamin berada di dalam poligon). Jika jumlah poligon melebihi target, dipilih subset secara acak. Jika kurang, titik acak tambahan ditambahkan dari poligon yang sudah ada. Strategi ini memastikan distribusi spasial yang merata dan menghindari duplikasi nilai piksel yang berdekatan (*spatial autocorrelation*).
""")

code("""generator = np.random.default_rng(ANGKA_ACAK)

def titik_interior_acak(poligon, rng, maks_coba=500):
    \"\"\"Hasilkan titik acak yang pasti berada di dalam poligon.\"\"\"
    xmin, ymin, xmax, ymax = poligon.bounds
    for _ in range(maks_coba):
        pt = Point(rng.uniform(xmin, xmax), rng.uniform(ymin, ymax))
        if poligon.contains(pt):
            return pt
    return poligon.representative_point()   # fallback aman

def pilih_sampel(gdf, n_target, rng):
    \"\"\"Pilih n_target titik sampel dari GeoDataFrame poligon.\"\"\"
    polys = list(gdf.geometry)
    urutan = rng.permutation(len(polys))
    titik_terpilih = []

    if len(polys) >= n_target:
        for idx in urutan[:n_target]:
            titik_terpilih.append((polys[idx].representative_point(), int(idx)))
    else:
        for idx in urutan:
            titik_terpilih.append((polys[idx].representative_point(), int(idx)))
        while len(titik_terpilih) < n_target:
            idx = int(rng.integers(len(polys)))
            titik_terpilih.append((titik_interior_acak(polys[idx], rng), idx))

    return titik_terpilih

# ─ Himpun semua titik sampel ─
rekaman = []
for k, v in DEFINISI_KELAS.items():
    for pt, pid in pilih_sampel(koleksi_shp[k], v["jml_target"], generator):
        rekaman.append({
            "id_kelas": k, "kelas": v["label"],
            "id_poligon": pid, "lon": pt.x, "lat": pt.y
        })

df_titik = pd.DataFrame(rekaman).reset_index(drop=True)
print(f"Total titik sampel terpilih: {len(df_titik)}")
display(df_titik["kelas"].value_counts().reindex(DAFTAR_KELAS).rename("Jumlah Titik").to_frame())
""")

md("""### 2.4 Peta Sebaran Titik Sampel dan Poligon Referensi""")

code("""fig, ax = plt.subplots(figsize=(12, 7))
for k, v in DEFINISI_KELAS.items():
    koleksi_shp[k].plot(ax=ax, facecolor=v["warna"], edgecolor="black",
                        alpha=0.55, linewidth=0.6, label=f"{v['label']} ({len(koleksi_shp[k])} poligon)")
    sub = df_titik[df_titik["id_kelas"] == k]
    ax.scatter(sub["lon"], sub["lat"], s=14, c=v["warna"], edgecolors="white",
               linewidths=0.5, zorder=5)

ax.set_title("Peta Sebaran Poligon Sampel dan Titik Representatif — 6 Kelas LULC Jawa Timur",
             fontsize=12, fontweight="bold", pad=14)
ax.set_xlabel("Bujur Timur (°)"); ax.set_ylabel("Lintang Selatan (°)")
ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(DIR_KERJA, "peta_sampel.png"), dpi=150)
plt.show()
""")

md("""### 2.5 Pengambilan Citra Sentinel-2A dari Copernicus CDSE

Permintaan citra dilakukan melalui **Sentinel Hub Process API** menggunakan library `sentinelhub-py`. Satu *evalscript* (kode JavaScript kecil) dikirim ke server Copernicus untuk:
1. **Menyaring citra** sesuai rentang tanggal dan persentase awan (`MAX_CLOUD`).
2. **Menghapus piksel awan** menggunakan lapisan SCL (Scene Classification Layer): kelas 3 (bayangan), 8–9 (awan), 10 (cirrus), 11 (salju) dihilangkan.
3. **Menghitung komposit median** dari semua citra bersih — sehingga sisa awan dan variasi musim teredam.
4. **Menyeragamkan resolusi** band 20 m (B5–B7, B8A, B11, B12) ke grid 10 m secara otomatis.

Hasilnya: 10 band reflektansi surface (nilai 0–1) per titik sampel.
""")

code('''# ─ Koneksi Copernicus ─
_sesi_api = {}

def siapkan_koneksi():
    if "token" not in _sesi_api:
        import os, getpass, requests
        c_id = os.environ.get("CDSE_CLIENT_ID") or input("CDSE Client ID     : ").strip()
        c_sec = os.environ.get("CDSE_CLIENT_SECRET") or getpass.getpass("CDSE Client Secret : ").strip()
        resp = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data={"grant_type": "client_credentials", "client_id": c_id, "client_secret": c_sec}
        )
        if resp.status_code != 200:
            raise Exception("Gagal otentikasi CDSE!")
        _sesi_api["token"] = resp.json()["access_token"]
    return _sesi_api["token"]

# ─ Evalscript komposit median dengan masking SCL ─
EVALSCRIPT = """//VERSION=3
const FILTER_2A = {hanya2a};
function setup() {
  return {
    input: [{ bands: ["B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12","SCL","dataMask"] }],
    output: { bands: 10, sampleType: "FLOAT32" },
    mosaicking: "ORBIT"
  };
}
function median1D(arr) {
  if (arr.length === 0) return NaN;
  arr.sort(function(a,b){return a-b;});
  var m = Math.floor(arr.length/2);
  return arr.length%2 ? arr[m] : (arr[m-1]+arr[m])/2;
}
function evaluatePixel(samples, scenes) {
  var nama = ["B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12"];
  var buf = nama.map(function(){return [];});
  for (var i=0; i<samples.length; i++) {
    var s=samples[i];
    if (s.dataMask===0) continue;
    var c=s.SCL;
    if (c===3||c===8||c===9||c===10||c===11) continue;
    if (FILTER_2A) {
      var pid=scenes.orbits[i].tiles[0].productId;
      if (pid.indexOf("S2A")!==0) continue;
    }
    for (var k=0;k<nama.length;k++) buf[k].push(s[nama[k]]);
  }
  if (buf[0].length===0) return nama.map(function(){return NaN;});
  return buf.map(median1D);
}
""".replace("{hanya2a}", "true" if HANYA_2A else "false")

def unduh_median_bbox(bbox, ukuran_px):
    \"\"\"Unduh komposit median 10 band via raw requests Copernicus API.\"\"\"
    import requests, numpy as np
    token = siapkan_koneksi()
    w, h = ukuran_px
    # sentinelhub-py BBox diubah ke list [minx, miny, maxx, maxy]
    bbox_list = list(bbox) if hasattr(bbox, '__iter__') else bbox
    skema = {
        "input": {
            "bounds": {
                "bbox": bbox_list,
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": f"{TGL_AWAL}T00:00:00Z",
                        "to": f"{TGL_AKHIR}T23:59:59Z"
                    },
                    "maxCloudCoverage": BATAS_AWAN
                }
            }]
        },
        "output": {
            "width": w, "height": h,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}]
        },
        "evalscript": EVALSCRIPT
    }
    
    req = requests.post(
        "https://sh.dataspace.copernicus.eu/api/v1/process", 
        json=skema, 
        headers={"Authorization": f"Bearer {token}", "Accept": "image/tiff"}
    )
    if req.status_code != 200:
        raise Exception(f"HTTP {req.status_code}: {req.text[:200]}")
    
    import rasterio
    from rasterio.io import MemoryFile
    with MemoryFile(req.content) as mem, mem.open() as dt_src:
        arr = dt_src.read()
        return np.transpose(arr, (1, 2, 0))
''')

code("""def ekstrak_semua_titik(df_titik):
    \"\"\"Loop seluruh titik sampel, unduh piksel tengah kotak 30x30 m dari Copernicus.\"\"\"
    tabel_band = []
    N = len(df_titik)
    for nomor, (_, baris) in enumerate(df_titik.iterrows(), start=1):
        pad_lat = 15 / 111320.0
        pad_lon = 15 / (111320.0 * math.cos(math.radians(baris.lat)))
        kotak = BBox([baris.lon - pad_lon, baris.lat - pad_lat,
                      baris.lon + pad_lon, baris.lat + pad_lat], crs=CRS.WGS84)
        nilai = [np.nan] * 10
        for percobaan in range(3):
            try:
                arr = unduh_median_bbox(kotak, (3, 3))
                nilai = list(arr[1, 1, :])     # piksel tengah dari grid 3×3
                break
            except Exception as err:
                if percobaan == 2:
                    print(f"\\n[GAGAL titik {nomor}]: {str(err)[:120]}")
                time.sleep(5)
        tabel_band.append(nilai)
        print(f"\\rProses titik {nomor}/{N} ...", end="")
    print()
    return pd.DataFrame(tabel_band, columns=NAMA_BAND, index=df_titik.index)

NAMA_BAND = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12"]

if os.path.exists(BERKAS_CSV) and not ULANGI_UNDUH:
    df = pd.read_csv(BERKAS_CSV)
    print(f"Dataset dimuat dari {BERKAS_CSV} ({len(df)} baris)")
else:
    df_band = ekstrak_semua_titik(df_titik)
    df = df_titik.join(df_band)
    df = tambah_indeks(df)
    df.to_csv(BERKAS_CSV, index=False)
    print(f"Dataset disimpan: {BERKAS_CSV}")

df = df.replace([np.inf, -np.inf], np.nan)
n_awal = len(df)
df = df.dropna(subset=NAMA_BAND + NAMA_INDEKS).reset_index(drop=True)
print(f"Sampel valid: {len(df)} (dibuang {n_awal - len(df)} titik nodata/awan)")
display(df.head(3))
""")

# ============================================================
# BAB 3 — DESKRIPSI FITUR
# ============================================================
md("""## 3. Deskripsi Fitur & Rumus

### 3.1 Band Reflektansi (10 Fitur Asli)

| Fitur | Panjang Gelombang | Rentang | Peran dalam LULC |
|---|---|---|---|
| B2 | 492 nm (Biru) | 0–1 | Pantulan beton/aspal tinggi; air biru cerah; vegetasi rendah |
| B3 | 560 nm (Hijau) | 0–1 | Puncak pantulan klorofil sehat; kontras dengan merah |
| B4 | 665 nm (Merah) | 0–1 | Vegetasi menyerap kuat; tanah/bangunan pantulan sedang |
| B5 | 704 nm (Red Edge 1) | 0–1 | Batas transisi klorofil → NIR; sangat sensitif ke kesehatan vegetasi |
| B6 | 740 nm (Red Edge 2) | 0–1 | Pembeda kerapatan kanopi |
| B7 | 783 nm (Red Edge 3) | 0–1 | Biomassa vegetasi tinggi |
| B8 | 833 nm (NIR) | 0–1 | Vegetasi sangat tinggi; air sangat rendah/nol — pembeda daratan/air terbaik |
| B8A | 865 nm (Narrow NIR) | 0–1 | Kadar air tanaman, sedikit lebih presisi dari B8 |
| B11 | 1614 nm (SWIR 1) | 0–1 | Kelembapan tanah/vegetasi; area terbangun dan industri pantulan lebih tinggi |
| B12 | 2202 nm (SWIR 2) | 0–1 | Membedakan material bangunan, tanah terbakar, lahan terbuka |

> **Rumus konversi DN → Reflektansi (L2A):** Copernicus sudah memproses di server — hasil API sudah dalam unit reflektansi surface (0–1).

### 3.2 Indeks Spektral (8 Fitur Turunan)

Indeks spektral adalah kombinasi aritmetika antar band yang dirancang untuk menonjolkan karakteristik tertentu sambil menekan pengaruh lain (sudut matahari, kondisi atmosfer sisa, dll).

| Indeks | Nama Lengkap | Rumus | Rentang | Interpretasi untuk LULC |
|---|---|---|---|---|
| **NDVI** | Normalized Difference Vegetation Index | $\\frac{B8 - B4}{B8 + B4}$ | −1 s/d 1 | Positif tinggi → vegetasi lebat (Mangrove, Lahan Hijau, Sawah fase tanam); negatif → air/bangunan |
| **NDWI** | Normalized Difference Water Index (McFeeters) | $\\frac{B3 - B8}{B3 + B8}$ | −1 s/d 1 | Positif → permukaan air; efektif untuk Danau, sawah tergenang |
| **MNDWI** | Modified NDWI (Xu 2006) | $\\frac{B3 - B11}{B3 + B11}$ | −1 s/d 1 | Lebih kuat memisahkan air dari area terbangun vs. NDWI biasa |
| **NDBI** | Normalized Difference Built-up Index | $\\frac{B11 - B8}{B11 + B8}$ | −1 s/d 1 | Positif → area terbangun (Rumah, Industri); negatif → vegetasi |
| **NDRE** | Normalized Difference Red Edge | $\\frac{B8 - B5}{B8 + B5}$ | −1 s/d 1 | Sensitif terhadap klorofil — membedakan Mangrove vs. Lahan Hijau vs. Sawah |
| **EVI** | Enhanced Vegetation Index | $\\frac{2.5(B8 - B4)}{B8 + 6B4 - 7.5B2 + 1}$ | ≈−1 s/d 1 | Koreksi atmosfer & backscatter tanah; tidak jenuh di kanopi rapat (Mangrove) |
| **SAVI** | Soil-Adjusted Vegetation Index | $\\frac{1.5(B8 - B4)}{B8 + B4 + 0.5}$ | ≈−1.5 s/d 1.5 | Seperti NDVI tapi menekan kontaminasi pantulan tanah — berguna Sawah fase kering |
| **BSI** | Bare Soil Index | $\\frac{(B11+B4)-(B8+B2)}{(B11+B4)+(B8+B2)}$ | −1 s/d 1 | Positif → tanah terbuka / permukaan keras (Industri, area konstruksi) |
""")

code("""NAMA_INDEKS = ["NDVI","NDWI","MNDWI","NDBI","NDRE","EVI","SAVI","BSI"]
SEMUA_FITUR = NAMA_BAND + NAMA_INDEKS

def tambah_indeks(df_in):
    \"\"\"Hitung 8 indeks spektral dari kolom band dan tambahkan ke DataFrame.\"\"\"
    d = df_in.copy()
    eps = 1e-9
    nd = lambda a, b: (a - b) / (a + b + eps)
    d["NDVI"]  = nd(d["B8"],  d["B4"])
    d["NDWI"]  = nd(d["B3"],  d["B8"])
    d["MNDWI"] = nd(d["B3"],  d["B11"])
    d["NDBI"]  = nd(d["B11"], d["B8"])
    d["NDRE"]  = nd(d["B8"],  d["B5"])
    d["EVI"]   = 2.5 * (d["B8"] - d["B4"]) / (d["B8"] + 6*d["B4"] - 7.5*d["B2"] + 1)
    d["SAVI"]  = 1.5 * (d["B8"] - d["B4"]) / (d["B8"] + d["B4"] + 0.5)
    d["BSI"]   = ((d["B11"] + d["B4"]) - (d["B8"] + d["B2"])) / \\
                 ((d["B11"] + d["B4"]) + (d["B8"] + d["B2"]) + eps)
    return d

print(f"Total fitur yang digunakan: {len(SEMUA_FITUR)}")
print(f"  • Band asli (reflektansi) : {len(NAMA_BAND)} — {NAMA_BAND}")
print(f"  • Indeks spektral         : {len(NAMA_INDEKS)} — {NAMA_INDEKS}")
""")

# ============================================================
# BAB 4 — EDA
# ============================================================
md("""## 4. Eksplorasi Data (EDA)

### 4.1 Distribusi Kelas dan Jumlah Sampel""")

code("""jml_per_kelas = df["kelas"].value_counts().reindex(DAFTAR_KELAS)
print("Jumlah kelas  :", df["kelas"].nunique())
print("Total sampel  :", len(df))
display(jml_per_kelas.to_frame("Jumlah Sampel"))

fig, ax = plt.subplots(figsize=(9, 4))
bar_warna = [PALET_WARNA[k] for k in jml_per_kelas.index]
batang = ax.bar(jml_per_kelas.index, jml_per_kelas.values, color=bar_warna, edgecolor="black", linewidth=0.7)
ax.bar_label(batang, padding=3)
ax.set_title("Distribusi Sampel per Kelas LULC", fontsize=12, fontweight="bold")
ax.set_ylabel("Jumlah Sampel"); ax.set_xlabel("")
ax.tick_params(axis="x", rotation=15)
ax.grid(axis="y", alpha=0.35)
plt.tight_layout(); plt.show()
""")

md("### 4.2 Statistik Deskriptif Fitur")

code("""print("Statistik keseluruhan fitur:")
display(df[SEMUA_FITUR].describe().T.round(4))
print("\\nRata-rata nilai fitur per kelas:")
display(df.groupby("kelas")[SEMUA_FITUR].mean().reindex(DAFTAR_KELAS).round(3))
""")

md("""### 4.3 Tanda Tangan Spektral (*Spectral Signature*)

Grafik reflektansi rata-rata per band untuk setiap kelas. Pola khasnya:
- **Vegetasi** (Mangrove, Lahan Hijau, Sawah) — pantulan rendah di B4 (klorofil menyerap), lonjakan tajam di NIR (B8).
- **Air** (Danau) — nilai rendah dan terus turun mendekati nol di NIR/SWIR.
- **Bangunan & Industri** — pantulan datar atau naik ke arah SWIR, terutama B11–B12.
""")

code("""lambda_nm = [492, 560, 665, 704, 740, 783, 833, 865, 1614, 2202]
rata_band = df.groupby("kelas")[NAMA_BAND].mean().reindex(DAFTAR_KELAS)

fig, ax = plt.subplots(figsize=(11, 5))
for kls in DAFTAR_KELAS:
    ax.plot(lambda_nm, rata_band.loc[kls].values,
            marker="o", linewidth=2.2, label=kls, color=PALET_WARNA[kls])

ax.set_xlabel("Panjang Gelombang (nm)", fontsize=11)
ax.set_ylabel("Rata-rata Reflektansi Permukaan", fontsize=11)
ax.set_title("Tanda Tangan Spektral 6 Kelas LULC — Sentinel-2A", fontsize=12, fontweight="bold")
ax.set_xticks(lambda_nm)
ax.set_xticklabels([f"B2\\n492", "B3\\n560", "B4\\n665", "B5\\n704", "B6\\n740",
                    "B7\\n783", "B8\\n833", "B8A\\n865", "B11\\n1614", "B12\\n2202"], fontsize=8)
ax.legend(loc="upper left", fontsize=10, framealpha=0.9)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(DIR_KERJA, "spectral_signature.png"), dpi=150)
plt.show()
""")

md("### 4.4 Boxplot Distribusi Indeks Spektral per Kelas")

code("""fig, sumbu = plt.subplots(2, 4, figsize=(20, 9))
for ax, indeks in zip(sumbu.ravel(), NAMA_INDEKS):
    sns.boxplot(data=df, x="kelas", y=indeks, order=DAFTAR_KELAS,
                palette=PALET_WARNA, ax=ax, fliersize=2.5, linewidth=0.8)
    ax.set_title(indeks, fontsize=11, fontweight="bold")
    ax.set_xlabel(""); ax.tick_params(axis="x", rotation=45, labelsize=8)
plt.suptitle("Sebaran Nilai Indeks Spektral per Kelas LULC", fontsize=13, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(os.path.join(DIR_KERJA, "boxplot_indeks.png"), dpi=150)
plt.show()
""")

md("""### 4.5 Matriks Korelasi Antar Fitur

Korelasi tinggi antara indeks berbasis NIR wajar (NDVI, EVI, SAVI, NDRE semua menggunakan B8). Ini tidak menjadi masalah untuk **Random Forest** (algoritma terbaik kami) karena pohon keputusan bersifat tidak sensitif terhadap skala maupun kolinearitas — berbeda dengan regresi linear atau SVM linear.""")

code("""fig, ax = plt.subplots(figsize=(13, 10))
sns.heatmap(df[SEMUA_FITUR].corr(), cmap="RdBu_r", center=0,
            annot=True, fmt=".1f", annot_kws={"size": 6.5},
            linewidths=0.3, ax=ax)
ax.set_title("Matriks Korelasi Fitur Sentinel-2A", fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(DIR_KERJA, "korelasi_fitur.png"), dpi=150)
plt.show()
""")

# ============================================================
# BAB 5 — PEMODELAN
# ============================================================
md("""## 5. Pemodelan Klasifikasi — Eksperimen Multi-Model

### 5.1 Pembagian Data Training dan Testing

Data dibagi dengan rasio **80% latih / 20% uji** menggunakan `stratify=y` agar proporsi keenam kelas tetap konsisten di kedua bagian.
""")

code("""UKURAN_UJI = 0.20
X = df[SEMUA_FITUR]
y = df["kelas"]

X_latih, X_uji, y_latih, y_uji = train_test_split(
    X, y, test_size=UKURAN_UJI, stratify=y, random_state=ANGKA_ACAK)

tb_split = pd.DataFrame({
    "Total"   : y.value_counts(),
    "Latih"   : y_latih.value_counts(),
    "Uji"     : y_uji.value_counts(),
}).reindex(DAFTAR_KELAS)
tb_split.loc["TOTAL"] = tb_split.sum()

print(f"Jumlah Kelas         : {y.nunique()}")
print(f"Jumlah Data Latih    : {len(X_latih)} ({len(X_latih)/len(X):.0%})")
print(f"Jumlah Data Uji      : {len(X_uji)} ({len(X_uji)/len(X):.0%})")
display(tb_split.astype(int))
""")

md("""### 5.2 Definisi dan Perbandingan Empat Model

Empat algoritma dibandingkan: **Random Forest (RF), Support Vector Machine (SVM), Gradient Boosting (GBM), K-Nearest Neighbors (KNN)**. Setiap model dievaluasi menggunakan **Repeated Stratified 5-Fold Cross-Validation (10 ulangan)** sehingga hasilnya stabil dan tidak bergantung pada satu partisi acak.

| Algoritma | Cara Kerja Singkat | Keunggulan | Kelemahan |
|---|---|---|---|
| **Random Forest** | Ensemble dari N pohon keputusan; tiap pohon dilatih pada subsampel data dan fitur acak; keputusan akhir dari mayoritas suara | Tidak perlu standarisasi; robust terhadap outlier; menghasilkan *feature importance* | Sulit diinterpretasi secara visual; lambat untuk N pohon besar |
| **SVM** | Mencari hyperplane pemisah dengan margin maksimum; kernel RBF memetakan data ke dimensi lebih tinggi | Efektif di ruang berdimensi tinggi; regularisasi bawaan | Perlu standarisasi; scaling sensitif; lambat di data besar |
| **Gradient Boosting** | Ensemble sekuensial: tiap pohon memperbaiki kesalahan pohon sebelumnya dengan gradient descent | Akurasi tinggi; fleksibel | Lama dilatih; mudah overfitting jika n_estimators terlalu besar |
| **KNN** | Memprediksi kelas berdasarkan mayoritas k tetangga terdekat di ruang fitur | Sederhana, non-parametrik | Perlu standarisasi; lambat saat prediksi (lazy learner) |
""")

code("""cv_stratified = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=ANGKA_ACAK)

kandidat_model = {
    "Random Forest": Pipeline([
        ("rf", RandomForestClassifier(n_estimators=200, random_state=ANGKA_ACAK, n_jobs=-1))
    ]),
    "SVM (RBF)": Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(kernel="rbf", probability=True, random_state=ANGKA_ACAK))
    ]),
    "Gradient Boosting": Pipeline([
        ("gb", GradientBoostingClassifier(n_estimators=150, random_state=ANGKA_ACAK))
    ]),
    "KNN": Pipeline([
        ("scaler", StandardScaler()),
        ("knn", KNeighborsClassifier(n_neighbors=5, weights="distance"))
    ]),
}

hasil_cv = []
for nama_model, pipeline in kandidat_model.items():
    skor_acc = cross_val_score(pipeline, X, y, cv=cv_stratified, scoring="accuracy", n_jobs=-1)
    skor_f1  = cross_val_score(pipeline, X, y, cv=cv_stratified, scoring="f1_macro",  n_jobs=-1)
    hasil_cv.append({
        "Model": nama_model,
        "Akurasi CV (mean)": skor_acc.mean(),
        "Akurasi CV (std)": skor_acc.std(),
        "F1 Macro CV (mean)": skor_f1.mean(),
    })

df_cv = pd.DataFrame(hasil_cv).sort_values("Akurasi CV (mean)", ascending=False).reset_index(drop=True)
display(df_cv.round(4))
MODEL_TERBAIK_NAMA = df_cv.loc[0, "Model"]
print(f"\\n→ Model dengan CV accuracy tertinggi: {MODEL_TERBAIK_NAMA}")
""")

code("""# Visualisasi perbandingan CV accuracy
fig, ax = plt.subplots(figsize=(9, 4))
warna_bar = ["#27AE60" if i == 0 else "#85929E" for i in range(len(df_cv))]
bar = ax.barh(df_cv["Model"][::-1], df_cv["Akurasi CV (mean)"][::-1],
              color=warna_bar[::-1], edgecolor="black", linewidth=0.7)
ax.bar_label(bar, fmt="%.4f", padding=4, fontsize=9)
ax.set_xlabel("Akurasi CV (Repeated Stratified 5-Fold, 10x)")
ax.set_title("Perbandingan Akurasi Cross-Validation — 4 Model Klasifikasi", fontweight="bold")
ax.set_xlim(0, 1.08)
ax.grid(axis="x", alpha=0.35)
plt.tight_layout()
plt.savefig(os.path.join(DIR_KERJA, "perbandingan_model.png"), dpi=150)
plt.show()
""")

md("""### 5.3 Evaluasi Model Terbaik pada Data Testing""")

code("""pipeline_terbaik = kandidat_model[MODEL_TERBAIK_NAMA]
pipeline_terbaik.fit(X_latih, y_latih)
prediksi_uji = pipeline_terbaik.predict(X_uji)

akurasi_uji = accuracy_score(y_uji, prediksi_uji)
kappa_uji   = cohen_kappa_score(y_uji, prediksi_uji)
f1_uji      = f1_score(y_uji, prediksi_uji, average="macro")

print(f"Model  : {MODEL_TERBAIK_NAMA}")
print(f"Akurasi (Testing) : {akurasi_uji:.4f}")
print(f"Kappa  (Testing)  : {kappa_uji:.4f}")
print(f"F1 Macro (Testing): {f1_uji:.4f}")
print()
print(classification_report(y_uji, prediksi_uji, labels=DAFTAR_KELAS, zero_division=0))

mat_konfus = confusion_matrix(y_uji, prediksi_uji, labels=DAFTAR_KELAS)
fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(mat_konfus, annot=True, fmt="d", cmap="YlOrRd",
            xticklabels=DAFTAR_KELAS, yticklabels=DAFTAR_KELAS,
            linewidths=0.4, ax=ax)
ax.set_xlabel("Prediksi", fontsize=11); ax.set_ylabel("Aktual", fontsize=11)
ax.set_title(f"Confusion Matrix — {MODEL_TERBAIK_NAMA} (Data Testing)", fontweight="bold")
ax.tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(DIR_KERJA, "confusion_matrix.png"), dpi=150)
plt.show()
""")

# ============================================================
# BAB 6 — EKSPERIMEN LANJUTAN
# ============================================================
md("""## 6. Eksperimen Lanjutan

### 6.1 Eksperimen Rasio Train/Test Split""")

code("""hasil_rasio = []
for fraksi_uji in [0.10, 0.20, 0.30, 0.40]:
    skor_rasio = []
    for ulang in range(10):
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=fraksi_uji, stratify=y, random_state=ANGKA_ACAK + ulang)
        pip = kandidat_model[MODEL_TERBAIK_NAMA]
        pip.fit(X_tr, y_tr)
        skor_rasio.append(accuracy_score(y_te, pip.predict(X_te)))
    hasil_rasio.append({
        "Rasio (Latih:Uji)": f"{int((1-fraksi_uji)*100)}:{int(fraksi_uji*100)}",
        "Fraksi Uji": fraksi_uji,
        "Rata-rata Akurasi": np.mean(skor_rasio),
        "Std Dev": np.std(skor_rasio),
    })

df_rasio = pd.DataFrame(hasil_rasio)
display(df_rasio.round(4))
""")

md("### 6.2 Eksperimen Kombinasi Fitur")

code("""skenario = {
    "A — 4 Band Utama (B2,B3,B4,B8)":          ["B2","B3","B4","B8"],
    "B — 10 Band Asli Sentinel-2A":             NAMA_BAND,
    "C — 8 Indeks Spektral Saja":               NAMA_INDEKS,
    "D — Pilihan Indeks (NDVI,MNDWI,NDBI,BSI)": ["NDVI","MNDWI","NDBI","BSI"],
    "E — Gabungan 18 Fitur (Band+Indeks)":      SEMUA_FITUR,
}

hasil_fitur_exp = []
for judul, kolom in skenario.items():
    pip = kandidat_model[MODEL_TERBAIK_NAMA]
    sv = cross_val_score(pip, df[kolom], y, cv=cv_stratified, scoring="accuracy", n_jobs=-1)
    sf = cross_val_score(pip, df[kolom], y, cv=cv_stratified, scoring="f1_macro",  n_jobs=-1)
    hasil_fitur_exp.append({
        "Skenario": judul, "Jml Fitur": len(kolom),
        "Akurasi CV": sv.mean(), "Std": sv.std(), "F1 Macro CV": sf.mean()
    })

df_fitur_exp = pd.DataFrame(hasil_fitur_exp).sort_values("Akurasi CV", ascending=False).reset_index(drop=True)
display(df_fitur_exp.round(4))
print(f"\\n→ Skenario fitur terbaik: {df_fitur_exp.loc[0, 'Skenario']}")
FITUR_AKHIR = skenario[df_fitur_exp.loc[0, "Skenario"]]
""")

md("### 6.3 Tuning Hyperparameter Model Terbaik (GridSearchCV)")

code("""# Hanya lakukan tuning jika Random Forest (model yang paling umum terbaik)
if MODEL_TERBAIK_NAMA == "Random Forest":
    param_grid_rf = {
        "rf__n_estimators": [100, 200, 300],
        "rf__max_depth":    [None, 15, 25],
        "rf__min_samples_split": [2, 5],
    }
    grid_search = GridSearchCV(
        kandidat_model["Random Forest"], param_grid_rf,
        cv=RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=ANGKA_ACAK),
        scoring="accuracy", n_jobs=-1, verbose=0)
    grid_search.fit(df[FITUR_AKHIR], y)

    tb_grid = pd.DataFrame(grid_search.cv_results_)[[
        "param_rf__n_estimators", "param_rf__max_depth",
        "param_rf__min_samples_split", "mean_test_score", "std_test_score"
    ]].sort_values("mean_test_score", ascending=False).head(10).reset_index(drop=True)
    display(tb_grid.round(4))

    print(f"\\nHyperparameter terbaik : {grid_search.best_params_}")
    print(f"Akurasi CV terbaik     : {grid_search.best_score_:.4f}")
    MODEL_FINAL = grid_search.best_estimator_
else:
    MODEL_FINAL = kandidat_model[MODEL_TERBAIK_NAMA]
    MODEL_FINAL.fit(df[FITUR_AKHIR], y)
    print(f"Model final ({MODEL_TERBAIK_NAMA}) sudah dilatih dengan fitur terbaik.")
""")

md("### 6.4 Evaluasi Model Final pada Data Testing")

code("""MODEL_FINAL.fit(X_latih[FITUR_AKHIR], y_latih)
pred_final = MODEL_FINAL.predict(X_uji[FITUR_AKHIR])

ak_final = accuracy_score(y_uji, pred_final)
kp_final = cohen_kappa_score(y_uji, pred_final)
f1_final = f1_score(y_uji, pred_final, average="macro")

print(f"=== Evaluasi Model Final ({MODEL_TERBAIK_NAMA}) ===")
print(f"Akurasi  : {ak_final:.4f}")
print(f"Kappa    : {kp_final:.4f}")
print(f"F1 Macro : {f1_final:.4f}\\n")
print(classification_report(y_uji, pred_final, labels=DAFTAR_KELAS, zero_division=0))

# Simpan model untuk Streamlit
joblib.dump(MODEL_FINAL, os.path.join(DIR_KERJA, "model_lulc_jatim.pkl"))
joblib.dump(FITUR_AKHIR, os.path.join(DIR_KERJA, "fitur_model.pkl"))
print("Model disimpan: model_lulc_jatim.pkl, fitur_model.pkl")
""")

# ============================================================
# BAB 7 — PETA FOLIUM
# ============================================================
md("""## 7. Peta Hasil Klasifikasi (Folium + Google Satellite)

### 7.1 Prediksi Piksel Skala Jawa Timur

Model final digunakan untuk mengklasifikasi seluruh piksel Area of Interest (AOI) Jawa Timur secara bertahap per ubin (*tile*) agar permintaan ke Copernicus tetap ringan dan tidak melebihi batas memori. Setiap ubin yang selesai langsung disimpan ke disk sehingga jika proses terputus, bisa dilanjutkan dari ubin terakhir.
""")

code("""# ─ Latih ulang dengan semua data berlabel ─
MODEL_PETA = kandidat_model[MODEL_TERBAIK_NAMA]
MODEL_PETA.fit(df[FITUR_AKHIR], df["kelas"])

# ─ Konfigurasi raster output ─
AOI_JATIM  = [111.0, -8.85, 114.65, -6.75]   # [barat, selatan, timur, utara]
RESOLUSI_M = 120           # meter per piksel (60=cepat, 120=lebih cepat, 30=detail)
UKURAN_TILE = 500          # piksel per sisi ubin
BERKAS_PETA = os.path.join(DIR_KERJA, "raster_klasifikasi.npz")
PAKSA_ULANG = False

def hex_ke_rgb(hex_str):
    h = hex_str.lstrip("#")
    return [int(h[i:i+2], 16) for i in (0, 2, 4)]

def klasifikasi_aoi_tiled(aoi, res_m, tile_px, model, fitur, berkas_simpan, paksa=False):
    barat, selatan, timur, utara = aoi
    dx = res_m / 111320.0
    W = int(math.ceil((timur - barat) / dx))
    H = int(math.ceil((utara - selatan) / dx))
    n_tile = math.ceil(H / tile_px) * math.ceil(W / tile_px)
    print(f"Raster: {W} × {H} piksel ({W*H:,}px) → {n_tile} ubin @ {tile_px}px")

    kode_kelas = {nm: i for i, nm in enumerate(DAFTAR_KELAS)}
    label = np.full((H, W), -1, dtype=np.int8)
    
    if os.path.exists(berkas_simpan) and not paksa:
        try:
            z = np.load(berkas_simpan, allow_pickle=True)
            if z["label"].shape == (H, W):
                label = z["label"].copy()
                n_terisi = (label >= 0).sum()
                print(f"Melanjutkan dari simpanan ({n_terisi/(H*W):.1%} piksel sudah ada)")
        except Exception:
            pass

    n, gagal = 0, []
    for r0 in range(0, H, tile_px):
        for c0 in range(0, W, tile_px):
            r1 = min(r0 + tile_px, H)
            c1 = min(c0 + tile_px, W)
            n += 1
            if (label[r0:r1, c0:c1] >= 0).mean() > 0.5:
                print(f"\\rUbin {n}/{n_tile} (lewati — sudah ada)", end="")
                continue

            bbox_ubin = BBox([
                barat + c0*dx, utara - r1*dx,
                barat + c1*dx, utara - r0*dx
            ], crs=CRS.WGS84)
            arr = None
            for coba in range(3):
                try:
                    arr = unduh_median_bbox(bbox_ubin, (c1-c0, r1-r0))
                    break
                except Exception as err:
                    if coba == 2:
                        gagal.append((r0, c0, str(err)[:200]))
                    time.sleep(10)
            
            print(f"\\rUbin {n}/{n_tile}", end="")
            if arr is None:
                continue

            h_u, w_u = arr.shape[:2]
            df_u = tambah_indeks(
                pd.DataFrame(arr.reshape(-1, 10), columns=NAMA_BAND))
            df_u = df_u.replace([np.inf, -np.inf], np.nan)
            mask_valid = df_u[SEMUA_FITUR].notna().all(axis=1).values

            blok = np.full(h_u * w_u, -1, dtype=np.int8)
            if mask_valid.any():
                pred = model.predict(df_u.loc[mask_valid, fitur])
                blok[mask_valid] = [kode_kelas[p] for p in pred]
            label[r0:r0+h_u, c0:c0+w_u] = blok.reshape(h_u, w_u)

            batas_tmp = [[utara - H*dx, barat], [utara, barat + W*dx]]
            np.savez_compressed(berkas_simpan, label=label,
                                batas=np.array(batas_tmp), aoi=np.array(aoi),
                                resolusi=res_m, fitur=np.array(fitur))
            time.sleep(1.5)

    print()
    if gagal:
        print(f"[!] {len(gagal)} ubin gagal diunduh.")
    batas = [[utara - H*dx, barat], [utara, barat + W*dx]]
    return label, batas

label_raster, batas_raster = klasifikasi_aoi_tiled(
    AOI_JATIM, RESOLUSI_M, UKURAN_TILE, MODEL_PETA, FITUR_AKHIR, BERKAS_PETA, PAKSA_ULANG)
print(f"\\nRaster selesai: {label_raster.shape}")
""")

code("""# ─ Buat gambar RGBA dari array label ─
H_r, W_r = label_raster.shape
gambar_rgba = np.zeros((H_r, W_r, 4), dtype=np.uint8)
for idx_kls, nama_kls in enumerate(DAFTAR_KELAS):
    warna_rgb = hex_ke_rgb(PALET_WARNA[nama_kls])
    gambar_rgba[label_raster == idx_kls] = warna_rgb + [255]

# ─ Statistik luas hasil klasifikasi ─
tengah_lat = (AOI_JATIM[1] + AOI_JATIM[3]) / 2
luas_per_piksel_ha = (RESOLUSI_M**2 * math.cos(math.radians(tengah_lat))) / 1e4
hitung_px = np.bincount(label_raster[label_raster >= 0].astype(int), minlength=len(DAFTAR_KELAS))

df_luas = pd.DataFrame({
    "Kelas": DAFTAR_KELAS,
    "Piksel": hitung_px,
    "Luas (Ha)": (hitung_px * luas_per_piksel_ha).round(0),
    "Persen (%)": (100 * hitung_px / max(hitung_px.sum(), 1)).round(2)
}).set_index("Kelas")
print(f"Piksel nodata: {(label_raster < 0).sum():,}")
display(df_luas)
""")

md("""### 7.2 Peta Interaktif Folium — Basemap Google Satellite""")

code("""# ─ Unduh citra satelit Esri untuk basemap tertanam ─
def unduh_mosaik_esri(aoi, zoom=10):
    \"\"\"Unduh tile satelit Esri untuk AOI pada tingkat zoom tertentu.\"\"\"
    n = 2 ** zoom
    def lon_lat_ke_xy(lon, lat):
        x = (lon + 180) / 360 * n
        y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
        return x, y
    def x_ke_lon(x): return x / n * 360 - 180
    def y_ke_lat(y): return math.degrees(math.atan(math.sinh(math.pi * (1 - 2*y/n))))

    x0, y0 = lon_lat_ke_xy(aoi[0], aoi[3])
    x1, y1 = lon_lat_ke_xy(aoi[2], aoi[1])
    xa, xb, ya, yb = int(x0), int(x1), int(y0), int(y1)

    kanvas = Image.new("RGB", ((xb-xa+1)*256, (yb-ya+1)*256), (170, 170, 170))
    url_tile = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

    def minta_tile(xy_):
        x, y = xy_
        try:
            resp = requests.get(url_tile.format(z=zoom, x=x, y=y),
                                headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
            return x, y, Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception:
            return x, y, None

    daftar_tile = [(x, y) for x in range(xa, xb+1) for y in range(ya, yb+1)]
    with ThreadPoolExecutor(max_workers=8) as ekse:
        for x, y, im in ekse.map(minta_tile, daftar_tile):
            if im:
                kanvas.paste(im, ((x-xa)*256, (y-ya)*256))

    bts = [[y_ke_lat(yb+1), x_ke_lon(xa)], [y_ke_lat(ya), x_ke_lon(xb+1)]]
    return kanvas, bts

mosaik_satelit, batas_satelit = unduh_mosaik_esri(AOI_JATIM, zoom=10)
PATH_SATELIT = os.path.join(DIR_KERJA, "satelit_jatim.jpeg")
mosaik_satelit.save(PATH_SATELIT, quality=85)
print("Citra satelit disimpan:", PATH_SATELIT)
""")

code("""# ─ Bangun peta Folium ─
pusat_peta = [(AOI_JATIM[1] + AOI_JATIM[3]) / 2, (AOI_JATIM[0] + AOI_JATIM[2]) / 2]
peta = folium.Map(location=pusat_peta, zoom_start=8, tiles=None, control_scale=True)

# Basemap online: Google Hybrid dan Esri Satellite
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    attr="Google Maps Hybrid", name="Google Hybrid (Online)",
    max_zoom=21, overlay=False, control=True
).add_to(peta)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery", name="Esri Satellite (Online)",
    max_zoom=19, overlay=False, control=True, show=False
).add_to(peta)

# Layer satelit tertanam (cadangan jika offline)
ImageOverlay(image=PATH_SATELIT, bounds=batas_satelit, opacity=1.0,
             name="Satelit (Tertanam Esri)", interactive=False, zindex=1).add_to(peta)

# Layer hasil klasifikasi
ImageOverlay(image=gambar_rgba, bounds=batas_raster, opacity=0.60,
             name=f"Klasifikasi LULC ({MODEL_TERBAIK_NAMA})", interactive=False, zindex=5).add_to(peta)

# Titik sampel per kelas (sembunyikan secara default)
for nama_kls in DAFTAR_KELAS:
    grp = folium.FeatureGroup(name=f"Sampel: {nama_kls}", show=False)
    sub = df[df["kelas"] == nama_kls]
    for _, baris in sub.iterrows():
        folium.CircleMarker(
            location=[baris.lat, baris.lon], radius=5,
            color="white", weight=1, fill=True,
            fill_color=PALET_WARNA[nama_kls], fill_opacity=0.95,
            popup=folium.Popup(f"<b>{nama_kls}</b><br>({baris.lon:.4f}°, {baris.lat:.4f}°)", max_width=200)
        ).add_to(grp)
    grp.add_to(peta)

# Batas AOI
grp_aoi = folium.FeatureGroup(name="Batas Area Studi Jawa Timur")
folium.Rectangle(
    [[AOI_JATIM[1], AOI_JATIM[0]], [AOI_JATIM[3], AOI_JATIM[2]]],
    color="white", weight=2, fill=False, dash_array="8"
).add_to(grp_aoi)
grp_aoi.add_to(peta)

# Legenda LULC
item_legenda = "".join(
    f'<div style="margin:3px 0;display:flex;align-items:center">'
    f'<span style="display:inline-block;width:15px;height:15px;'
    f'background:{PALET_WARNA[k]};border:1px solid #333;margin-right:7px;flex-shrink:0"></span>'
    f'<span style="font-size:12px">{k}</span></div>'
    for k in DAFTAR_KELAS
)
html_legenda = (
    f'<div style="position:fixed;bottom:35px;left:35px;z-index:9999;background:rgba(255,255,255,0.93);'
    f'padding:12px 15px;border:1px solid #999;border-radius:8px;font-family:Arial,sans-serif;'
    f'box-shadow:2px 2px 6px rgba(0,0,0,0.2);">'
    f'<div style="font-weight:bold;font-size:13px;margin-bottom:6px">Legenda LULC</div>'
    f'{item_legenda}'
    f'<div style="font-size:10px;color:#666;margin-top:6px">Model: {MODEL_TERBAIK_NAMA}</div>'
    f'</div>'
)
peta.get_root().html.add_child(folium.Element(html_legenda))

folium.LayerControl(collapsed=False).add_to(peta)
peta.fit_bounds([[AOI_JATIM[1], AOI_JATIM[0]], [AOI_JATIM[3], AOI_JATIM[2]]])

PATH_PETA_HTML = os.path.join(DIR_KERJA, "peta_lulc_jatim.html")
peta.save(PATH_PETA_HTML)
print(f"Peta interaktif disimpan: {PATH_PETA_HTML}")
from IPython.display import IFrame
display(IFrame(src=PATH_PETA_HTML, width="100%", height="650px"))
""")

# ============================================================
# BAB 8 — KESIMPULAN
# ============================================================
md("""## 8. Kesimpulan""")

code("""rasio_terbaik = df_rasio.sort_values("Rata-rata Akurasi", ascending=False).iloc[0]
kelas_f1 = pd.Series(
    f1_score(y_uji, pred_final, labels=DAFTAR_KELAS, average=None, zero_division=0),
    index=DAFTAR_KELAS)
kelas_terendah = kelas_f1.idxmin()

display(Markdown(f\"\"\"
### Ringkasan Hasil Analisis

**Data & Sampel:**
- Total {len(df)} sampel dari **{df['kelas'].nunique()} kelas LULC** Jawa Timur.
- Distribusi: {', '.join(f'{k}: {v}' for k, v in jml_per_kelas.items())}.
- Pembagian **80:20** → {len(X_latih)} data latih, {len(X_uji)} data uji.

**Fitur:**
- 10 band reflektansi Sentinel-2A + 8 indeks spektral = **18 fitur**.
- Skenario terbaik: *{df_fitur_exp.loc[0, 'Skenario']}* ({len(FITUR_AKHIR)} fitur).

**Pemodelan:**
- Empat algoritma dibandingkan (RF, SVM, GBM, KNN) via Repeated Stratified CV.
- **Model terbaik: {MODEL_TERBAIK_NAMA}** (CV akurasi: {df_cv.loc[0, 'Akurasi CV (mean)']:.2%}).
- Evaluasi final (testing 20%): Akurasi **{ak_final:.2%}**, Kappa **{kp_final:.3f}**, F1 Macro **{f1_final:.3f}**.

**Eksperimen:**
- Rasio terbaik: **{rasio_terbaik['Rasio (Latih:Uji)']}** ({rasio_terbaik['Rata-rata Akurasi']:.2%}).
- Kelas dengan F1 terendah: **{kelas_terendah}** ({kelas_f1.min():.2f}) — perlu sampel tambahan.

**Peta & Sistem Informasi:**
- Hasil klasifikasi ditampilkan dalam `peta_lulc_jatim.html` di atas basemap Google/Esri Satellite.
- Model disimpan di `model_lulc_jatim.pkl` untuk digunakan dalam aplikasi **Streamlit Web GIS**.
\"\"\"))
""")

# Tulis notebook
import os
output_path = r'c:\Users\HYPE AMD\Documents\kuliah\psd\materi\16_klasifikasi_lulc_jatim.ipynb'
nbf.write(nb, output_path)
print(f"Notebook ditulis ke: {output_path}")
