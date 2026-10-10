import nbformat as nbf

nb = nbf.read('materi/16_klasifikasi_lulc_jatim.ipynb', as_version=4)

# Find cell index that has _sesi_api / unduh_median_bbox
target_idx = None
for idx, cell in enumerate(nb.cells):
    if 'def unduh_median_bbox' in cell.source or '_sesi_api' in cell.source:
        target_idx = idx
        break

print(f"Target cell: {target_idx}")

# The tambah_indeks function to prepend
tambah_indeks_code = '''NAMA_BAND   = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12"]
NAMA_INDEKS = ["NDVI","NDWI","MNDWI","NDBI","NDRE","EVI","SAVI","BSI"]
SEMUA_FITUR = NAMA_BAND + NAMA_INDEKS

def tambah_indeks(df_in):
    """Hitung 8 indeks spektral dari kolom band dan tambahkan ke DataFrame."""
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

'''

# Prepend tambah_indeks to the target cell
nb.cells[target_idx].source = tambah_indeks_code + nb.cells[target_idx].source

# Also fix band column names: notebook uses B2/B3 style (from NAMA_BAND)
# but the extraction loop used NAMA_BAND = ["B2","B3",...] already
# Verify NAMA_BAND is defined in the cell that runs extraction
extrak_idx = None
for idx, cell in enumerate(nb.cells):
    if 'ekstrak_semua_titik' in cell.source and 'NAMA_BAND' in cell.source:
        extrak_idx = idx
        print(f"Extraction cell: {idx}")
        print(cell.source[cell.source.find('NAMA_BAND'):cell.source.find('NAMA_BAND')+60])
        break

nbf.write(nb, 'materi/16_klasifikasi_lulc_jatim.ipynb')
print("Done. tambah_indeks added before unduh_median_bbox cell.")
