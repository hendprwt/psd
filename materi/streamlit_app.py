"""
Sistem Informasi Geografis — Klasifikasi Penggunaan Lahan Jawa Timur
Berbasis Sentinel-2A + Random Forest

Jalankan: streamlit run streamlit_app.py
"""

import os, math, io, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from PIL import Image
import joblib
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# ──────────────────────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SIG Klasifikasi Lahan Jawa Timur",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# KONSTAN
# ──────────────────────────────────────────────────────────────
DIR_APP    = os.path.dirname(os.path.abspath(__file__))
DIR_MATERI = DIR_APP  # file .pkl dan .npz ada di folder yang sama dengan app
# Jika app diletakkan di folder lain, sesuaikan:
# DIR_MATERI = os.path.join(DIR_APP, "materi")

DAFTAR_KELAS = ["Sawah", "Rumah", "Laut", "Mangrove", "Lahan Hijau", "Danau"]
PALET_WARNA  = {
    "Sawah"       : "#F4D03F",
    "Rumah"       : "#E74C3C",
    "Laut"        : "#0D47A1",
    "Mangrove"    : "#1E8449",
    "Lahan Hijau" : "#27AE60",
    "Danau"       : "#2E86C1",
}
NAMA_BAND   = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12"]
NAMA_INDEKS = ["NDVI","NDWI","MNDWI","NDBI","NDRE","EVI","SAVI","BSI"]
SEMUA_FITUR = NAMA_BAND + NAMA_INDEKS

AOI_JATIM = [111.0, -8.85, 114.65, -6.75]   # [barat, selatan, timur, utara]

def hex_ke_rgb(h):
    h = h.lstrip("#"); return [int(h[i:i+2], 16) for i in (0, 2, 4)]

# ──────────────────────────────────────────────────────────────
# MUAT ARTEFAK (model, raster, dataset)
# ──────────────────────────────────────────────────────────────
@st.cache_resource
def muat_model():
    path = os.path.join(DIR_MATERI, "model_lulc_jatim.pkl")
    if os.path.exists(path):
        return joblib.load(path)
    return None

@st.cache_resource
def muat_raster():
    path = os.path.join(DIR_MATERI, "raster_klasifikasi.npz")
    if os.path.exists(path):
        z = np.load(path, allow_pickle=True)
        return z["label"], z["batas"].tolist()
    return None, None

@st.cache_data
def muat_dataset():
    path = os.path.join(DIR_MATERI, "dataset_lulc_jatim.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

@st.cache_data
def muat_fitur():
    path = os.path.join(DIR_MATERI, "fitur_model.pkl")
    if os.path.exists(path):
        return joblib.load(path)
    return SEMUA_FITUR

# ──────────────────────────────────────────────────────────────
# FUNGSI INDEKS
# ──────────────────────────────────────────────────────────────
def hitung_indeks(df_in):
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
    d["BSI"]   = ((d["B11"] + d["B4"]) - (d["B8"] + d["B2"])) / \
                 ((d["B11"] + d["B4"]) + (d["B8"] + d["B2"]) + eps)
    return d

# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Lambang_Jawa_Timur.svg/220px-Lambang_Jawa_Timur.svg.png",
             width=90)
    st.title("🗺️ SIG Klasifikasi Lahan")
    st.caption("Jawa Timur — Sentinel-2A")
    st.divider()

    halaman = st.radio("Navigasi", [
        "📋 Beranda & Informasi",
        "🗺️ Peta Interaktif",
        "🔬 Prediksi Piksel Tunggal",
        "📊 Statistik & Grafik",
        "ℹ️ Tentang Metode",
    ])
    st.divider()
    st.caption("Sistem Informasi Geografis · Analisis Spasial Penggunaan Lahan")

# ──────────────────────────────────────────────────────────────
# HALAMAN 1 — BERANDA
# ──────────────────────────────────────────────────────────────
if halaman == "📋 Beranda & Informasi":
    st.title("Sistem Informasi Geografis")
    st.subheader("Klasifikasi Penggunaan dan Tutupan Lahan (LULC) Jawa Timur")
    st.markdown("""
    Aplikasi ini merupakan implementasi **Sistem Informasi Geografis berbasis analisis spasial** 
    untuk klasifikasi tutupan/penggunaan lahan di Provinsi Jawa Timur menggunakan citra satelit 
    **Sentinel-2A** dan algoritma **Random Forest**.
    """)

    st.divider()
    col1, col2, col3 = st.columns(3)

    model = muat_model()
    df_data = muat_dataset()
    label_r, _ = muat_raster()

    with col1:
        st.metric("Kelas LULC", len(DAFTAR_KELAS), "SNI 7645:2010")
    with col2:
        n_sampel = len(df_data) if df_data is not None else "—"
        st.metric("Sampel Latih+Uji", n_sampel)
    with col3:
        status_model = "✅ Siap" if model is not None else "⚠️ Belum tersedia"
        st.metric("Status Model", status_model)

    st.divider()
    st.subheader("6 Kelas LULC yang Diklasifikasikan")
    kol = st.columns(3)
    info_kelas = {
        "Sawah"       : "Lahan pertanian padi irigasi / tadah hujan. Nilai NDVI dan NDWI tinggi saat tergenang.",
        "Rumah"       : "Kawasan perumahan dan permukiman padat. NDBI positif, NDVI rendah.",
        "Laut"        : "Perairan terbuka dan lepas pantai. Nilai reflektansi mendekati nol di semua band inframerah.",
        "Mangrove"    : "Hutan mangrove pesisir. NDVI dan EVI sangat tinggi karena kerapatan kanopi.",
        "Lahan Hijau" : "Hutan, kebun, RTH umum. Tanda tangan spektral vegetasi kuat di NIR.",
        "Danau"       : "Danau vulkanik (Ranu-ranu) & waduk. NDWI positif, NIR mendekati nol.",
    }
    for i, (nama, deskripsi) in enumerate(info_kelas.items()):
        with kol[i % 3]:
            warna = PALET_WARNA[nama]
            st.markdown(
                f'<div style="border-left:5px solid {warna};padding:8px 12px;'
                f'margin-bottom:10px;background:#f8f9fa;border-radius:4px">'
                f'<b style="color:{warna}">{nama}</b><br>'
                f'<small style="color:#555">{deskripsi}</small></div>',
                unsafe_allow_html=True)

    st.divider()
    st.subheader("Acuan Klasifikasi — SNI 7645:2010")
    st.markdown("""
    Klasifikasi tutupan lahan mengacu pada **Standar Nasional Indonesia (SNI) 7645:2010** 
    tentang Klasifikasi Penutup Lahan yang ditetapkan oleh Badan Informasi Geospasial (BIG).
    
    | Hierarki | Kelas dalam SNI | Implementasi di Sistem Ini |
    |---|---|---|
    | Lahan Bervegetasi Terbudidayakan | Sawah Irigasi, Sawah Tadah Hujan | **Sawah** |
    | Lahan Terbangun — Permukiman | Area Perumahan/Hunian | **Rumah** |
    | Perairan Daratan | Danau, Waduk, Ranu | **Danau** |
    | Lahan Bervegetasi Alami — Mangrove | Hutan Mangrove | **Mangrove** |
    | Lahan Bervegetasi Alami — Hutan & Perkebunan | Hutan, Kebun | **Lahan Hijau** |
    | Perairan Laut | Perairan Terbuka / Laut | **Laut** |
    """)

# ──────────────────────────────────────────────────────────────
# HALAMAN 2 — PETA INTERAKTIF
# ──────────────────────────────────────────────────────────────
elif halaman == "🗺️ Peta Interaktif":
    st.title("🗺️ Peta Klasifikasi LULC Jawa Timur")

    col_kontrol, col_peta = st.columns([1, 3])

    with col_kontrol:
        st.subheader("Pengaturan Peta")
        opasitas = st.slider("Transparansi Layer Klasifikasi", 0.0, 1.0, 0.55, 0.05)
        tampil_sampel = st.checkbox("Tampilkan Titik Sampel", value=False)
        tampil_batas  = st.checkbox("Tampilkan Batas AOI", value=True)

        jenis_basemap = st.selectbox("Basemap", [
            "Google Hybrid",
            "Google Satellite",
            "Esri Satellite",
            "OpenStreetMap",
        ])

        st.divider()
        st.subheader("Legenda")
        for nama_kls, warna in PALET_WARNA.items():
            st.markdown(
                f'<div style="display:flex;align-items:center;margin:3px 0">'
                f'<div style="width:18px;height:18px;background:{warna};border:1px solid #333;'
                f'margin-right:8px;border-radius:3px;flex-shrink:0"></div>'
                f'<span style="font-size:13px">{nama_kls}</span></div>',
                unsafe_allow_html=True)

    with col_peta:
        label_r, batas_r = muat_raster()
        df_data = muat_dataset()

        pusat = [(AOI_JATIM[1] + AOI_JATIM[3]) / 2,
                 (AOI_JATIM[0] + AOI_JATIM[2]) / 2]

        basemap_urls = {
            "Google Hybrid":     "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            "Google Satellite":  "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            "Esri Satellite":    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "OpenStreetMap":     "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        }
        basemap_attr = {
            "Google Hybrid":    "Google Maps",
            "Google Satellite": "Google Maps",
            "Esri Satellite":   "Esri World Imagery",
            "OpenStreetMap":    "© OpenStreetMap contributors",
        }

        peta = folium.Map(location=pusat, zoom_start=8, tiles=None, control_scale=True)
        folium.TileLayer(
            tiles=basemap_urls[jenis_basemap],
            attr=basemap_attr[jenis_basemap],
            name=jenis_basemap, max_zoom=21
        ).add_to(peta)

        if label_r is not None and batas_r is not None:
            H_r, W_r = label_r.shape
            rgba = np.zeros((H_r, W_r, 4), dtype=np.uint8)
            for idx, nm in enumerate(DAFTAR_KELAS):
                rgba[label_r == idx] = hex_ke_rgb(PALET_WARNA[nm]) + [255]

            from folium.raster_layers import ImageOverlay
            ImageOverlay(image=rgba, bounds=batas_r, opacity=opasitas,
                         name="Klasifikasi LULC", interactive=False, zindex=5).add_to(peta)
        else:
            st.warning("⚠️ Raster klasifikasi belum tersedia. Jalankan notebook 16 terlebih dahulu.")

        if tampil_sampel and df_data is not None:
            for nm in DAFTAR_KELAS:
                grp = folium.FeatureGroup(name=f"Sampel: {nm}", show=True)
                sub = df_data[df_data["kelas"] == nm]
                for _, brs in sub.iterrows():
                    folium.CircleMarker(
                        [brs["lat"], brs["lon"]], radius=5,
                        color="white", weight=1, fill=True,
                        fill_color=PALET_WARNA[nm], fill_opacity=0.9,
                        popup=f"{nm}"
                    ).add_to(grp)
                grp.add_to(peta)

        if tampil_batas:
            folium.Rectangle(
                [[AOI_JATIM[1], AOI_JATIM[0]], [AOI_JATIM[3], AOI_JATIM[2]]],
                color="white", weight=2, fill=False, dash_array="8",
                tooltip="Batas Area Studi Jawa Timur"
            ).add_to(peta)

        folium.LayerControl(collapsed=True).add_to(peta)
        peta.fit_bounds([[AOI_JATIM[1], AOI_JATIM[0]], [AOI_JATIM[3], AOI_JATIM[2]]])

        st_folium(peta, width="100%", height=600)

# ──────────────────────────────────────────────────────────────
# HALAMAN 3 — PREDIKSI TUNGGAL
# ──────────────────────────────────────────────────────────────
elif halaman == "🔬 Prediksi Piksel Tunggal":
    st.title("🔬 Prediksi Kelas untuk Satu Titik Koordinat")
    st.markdown("""
    Masukkan nilai **10 band reflektansi Sentinel-2A** (skala 0–1) untuk satu piksel, 
    lalu sistem akan menghitung indeks spektral dan memprediksi kelas LULC-nya.
    """)

    model = muat_model()
    fitur_model = muat_fitur()

    if model is None:
        st.error("Model belum tersedia. Jalankan notebook 16 sampai selesai untuk menghasilkan model_lulc_jatim.pkl.")
    else:
        st.subheader("Input Nilai Band (Reflektansi Permukaan, 0–1)")
        st.caption("Nilai tipikal Sentinel-2A L2A. Vegetasi: B8 tinggi; Air: semua mendekati nol; Bangunan: B11/B12 tinggi.")

        kol1, kol2, kol3, kol4, kol5 = st.columns(5)
        kolom_input = [kol1, kol2, kol3, kol4, kol5, kol1, kol2, kol3, kol4, kol5]
        nilai_band_default = [0.04, 0.07, 0.05, 0.10, 0.20, 0.25, 0.28, 0.29, 0.17, 0.09]
        nilai_band = {}
        for band, kol_w, default in zip(NAMA_BAND, kolom_input, nilai_band_default):
            with kol_w:
                nilai_band[band] = st.number_input(band, 0.0, 1.0, default, 0.001, format="%.4f")

        if st.button("🔍 Prediksi Kelas", type="primary"):
            df_input = pd.DataFrame([nilai_band])
            df_input = hitung_indeks(df_input)
            df_input = df_input.replace([float("inf"), float("-inf")], float("nan"))

            if df_input[fitur_model].isna().any().any():
                st.error("Ada nilai band yang menghasilkan NaN saat kalkulasi indeks. Periksa kembali inputan.")
            else:
                prediksi = model.predict(df_input[fitur_model])[0]
                warna_kls = PALET_WARNA.get(prediksi, "#888888")

                st.divider()
                st.markdown(
                    f'<div style="background:{warna_kls}22;border:2px solid {warna_kls};'
                    f'border-radius:10px;padding:20px;text-align:center;margin:10px 0">'
                    f'<div style="font-size:18px;color:{warna_kls};font-weight:bold">Hasil Prediksi</div>'
                    f'<div style="font-size:32px;font-weight:900;color:{warna_kls};margin:8px 0">'
                    f'{prediksi}</div></div>',
                    unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("Nilai Indeks Spektral Terkalkulasi")
                    df_indeks_tampil = df_input[NAMA_INDEKS].T.rename(columns={0: "Nilai"}).round(4)
                    st.dataframe(df_indeks_tampil, use_container_width=True)

                with col_b:
                    st.subheader("Profil Spektral Input")
                    lambda_nm = [492, 560, 665, 704, 740, 783, 833, 865, 1614, 2202]
                    fig, ax = plt.subplots(figsize=(5, 3))
                    ax.plot(lambda_nm, [nilai_band[b] for b in NAMA_BAND],
                            marker="o", color=warna_kls, linewidth=2.5, label=prediksi)
                    ax.set_xlabel("λ (nm)", fontsize=9); ax.set_ylabel("Reflektansi", fontsize=9)
                    ax.set_title("Tanda Tangan Spektral", fontsize=9)
                    ax.grid(alpha=0.3); ax.legend(fontsize=8)
                    plt.tight_layout()
                    st.pyplot(fig)

# ──────────────────────────────────────────────────────────────
# HALAMAN 4 — STATISTIK & GRAFIK
# ──────────────────────────────────────────────────────────────
elif halaman == "📊 Statistik & Grafik":
    st.title("📊 Statistik Dataset dan Visualisasi")

    df_data = muat_dataset()
    if df_data is None:
        st.warning("Dataset belum tersedia. Jalankan notebook 16 terlebih dahulu.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "Distribusi Kelas", "Tanda Tangan Spektral", "Boxplot Indeks", "Korelasi Fitur"])

        with tab1:
            jml = df_data["kelas"].value_counts().reindex(DAFTAR_KELAS)
            col_tabel, col_grafik = st.columns(2)
            with col_tabel:
                st.subheader("Jumlah Sampel per Kelas")
                st.dataframe(jml.rename("Jumlah").to_frame(), use_container_width=True)
                st.metric("Total Sampel", len(df_data))
                st.metric("Jumlah Kelas", df_data["kelas"].nunique())
            with col_grafik:
                fig, ax = plt.subplots(figsize=(6, 4))
                warna_bar = [PALET_WARNA[k] for k in jml.index]
                bars = ax.bar(jml.index, jml.values, color=warna_bar, edgecolor="black", linewidth=0.7)
                ax.bar_label(bars, padding=3)
                ax.set_title("Distribusi Sampel", fontweight="bold")
                ax.set_ylabel("Jumlah"); ax.tick_params(axis="x", rotation=20)
                ax.grid(axis="y", alpha=0.35)
                plt.tight_layout(); st.pyplot(fig)

        with tab2:
            st.subheader("Tanda Tangan Spektral Rata-rata per Kelas")
            lambda_nm = [492, 560, 665, 704, 740, 783, 833, 865, 1614, 2202]
            rata = df_data.groupby("kelas")[NAMA_BAND].mean().reindex(DAFTAR_KELAS)
            fig, ax = plt.subplots(figsize=(10, 5))
            for kls in DAFTAR_KELAS:
                ax.plot(lambda_nm, rata.loc[kls].values,
                        marker="o", linewidth=2.2, label=kls, color=PALET_WARNA[kls])
            ax.set_xlabel("Panjang Gelombang (nm)")
            ax.set_ylabel("Reflektansi Permukaan")
            ax.set_title("Tanda Tangan Spektral — Sentinel-2A", fontweight="bold")
            ax.legend(); ax.grid(alpha=0.3)
            plt.tight_layout(); st.pyplot(fig)

        with tab3:
            st.subheader("Distribusi Indeks Spektral per Kelas")
            indeks_dipilih = st.selectbox("Pilih Indeks:", NAMA_INDEKS)
            fig, ax = plt.subplots(figsize=(9, 5))
            sns.boxplot(data=df_data, x="kelas", y=indeks_dipilih,
                        order=DAFTAR_KELAS, palette=PALET_WARNA, ax=ax)
            ax.set_title(f"Distribusi {indeks_dipilih} per Kelas LULC", fontweight="bold")
            ax.set_xlabel(""); ax.tick_params(axis="x", rotation=20)
            ax.grid(axis="y", alpha=0.3)
            plt.tight_layout(); st.pyplot(fig)

        with tab4:
            st.subheader("Matriks Korelasi Fitur")
            fitur_tersedia = [f for f in SEMUA_FITUR if f in df_data.columns]
            fig, ax = plt.subplots(figsize=(12, 9))
            sns.heatmap(df_data[fitur_tersedia].corr(), cmap="RdBu_r", center=0,
                        annot=True, fmt=".1f", annot_kws={"size": 6}, linewidths=0.3, ax=ax)
            ax.set_title("Matriks Korelasi Fitur Sentinel-2A", fontweight="bold")
            plt.tight_layout(); st.pyplot(fig)

        st.divider()
        st.subheader("Statistik Deskriptif")
        fitur_tersedia = [f for f in SEMUA_FITUR if f in df_data.columns]
        st.dataframe(df_data[fitur_tersedia].describe().T.round(4), use_container_width=True)

# ──────────────────────────────────────────────────────────────
# HALAMAN 5 — TENTANG METODE
# ──────────────────────────────────────────────────────────────
elif halaman == "ℹ️ Tentang Metode":
    st.title("ℹ️ Tentang Metode dan Data")

    st.subheader("Algoritma Klasifikasi — Random Forest")
    st.markdown(r"""
    **Random Forest** adalah algoritma *ensemble learning* yang membangun banyak pohon keputusan 
    secara paralel, masing-masing dilatih pada subset data dan fitur yang dipilih acak 
    (*Bootstrap Aggregating / Bagging*). Prediksi akhir diperoleh dari mayoritas suara pohon-pohon tersebut.

    **Keunggulan untuk Klasifikasi Lahan:**
    - Tidak memerlukan standarisasi fitur — cocok untuk campuran band dan indeks spektral.
    - Robust terhadap outlier (piksel berawan yang lolos masking).
    - Menghasilkan *Feature Importance* untuk mengidentifikasi band/indeks paling diskriminatif.
    - Tidak mudah overfitting berkat mekanisme bagging.

    **Rumus *Out-of-Bag Error* (estimasi generalisasi internal):**
    $$
    OOB\text{-}Error = \frac{1}{N}\sum_{i=1}^{N} \mathbf{1}[\hat{y}_i^{OOB} \neq y_i]
    $$
    """)

    st.divider()
    st.subheader("Metrik Evaluasi")
    st.markdown(r"""
    | Metrik | Rumus | Interpretasi |
    |---|---|---|
    | **Akurasi** | $\frac{TP+TN}{TP+TN+FP+FN}$ | Proporsi prediksi benar keseluruhan |
    | **Presisi** | $\frac{TP}{TP+FP}$ | Ketepatan prediksi positif |
    | **Recall** | $\frac{TP}{TP+FN}$ | Kelengkapan deteksi kelas positif |
    | **F1-Score** | $\frac{2 \cdot P \cdot R}{P+R}$ | Rata-rata harmonik presisi dan recall |
    | **Kappa Cohen** | $\frac{P_o - P_e}{1 - P_e}$ | Kesepakatan di atas peluang acak; $\kappa > 0.8$ = sangat baik |
    """)

    st.divider()
    st.subheader("Indeks Spektral Sentinel-2A")
    df_indeks_info = pd.DataFrame({
        "Indeks": NAMA_INDEKS,
        "Rumus": [
            "(B8−B4)/(B8+B4)", "(B3−B8)/(B3+B8)", "(B3−B11)/(B3+B11)",
            "(B11−B8)/(B11+B8)", "(B8−B5)/(B8+B5)",
            "2.5(B8−B4)/(B8+6B4−7.5B2+1)",
            "1.5(B8−B4)/(B8+B4+0.5)",
            "[(B11+B4)−(B8+B2)]/[(B11+B4)+(B8+B2)]"
        ],
        "Rentang": ["−1 s/d 1"]*8,
        "Kegunaan Utama": [
            "Kerapatan vegetasi", "Kandungan air permukaan", "Air vs. area terbangun",
            "Area terbangun", "Kesehatan vegetasi (klorofil)",
            "Vegetasi rapat (koreksi atmosfer)", "Vegetasi (koreksi pengaruh tanah)",
            "Tanah terbuka / permukaan keras"
        ]
    })
    st.dataframe(df_indeks_info, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Sumber Data")
    st.markdown("""
    - **Citra Satelit:** Sentinel-2A Level-2A (Surface Reflectance), Copernicus Data Space Ecosystem
    - **Shapefile Referensi:** Digitasi manual menggunakan citra resolusi tinggi — 6 kelas LULC Jawa Timur
    - **Standar Klasifikasi:** SNI 7645:2010 Klasifikasi Penutup Lahan (Badan Informasi Geospasial)
    - **Basemap Peta:** Google Maps Satellite / Esri World Imagery
    """)
