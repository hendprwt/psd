import nbformat as nbf

nb = nbf.read('materi/16_klasifikasi_lulc_jatim.ipynb', as_version=4)

# Fix cell 14: move NAMA_BAND definition to TOP of cell (before ekstrak_semua_titik)
old_src = nb.cells[14].source

# Remove NAMA_BAND from wherever it appears in cell 14
old_src = old_src.replace(
    '\nNAMA_BAND = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12"]\n',
    '\n'
)

# Prepend constants at top of cell (they're already defined in cell 13 now, but just in case)
header = '''NAMA_BAND   = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12"]
NAMA_INDEKS = ["NDVI","NDWI","MNDWI","NDBI","NDRE","EVI","SAVI","BSI"]
SEMUA_FITUR = NAMA_BAND + NAMA_INDEKS

'''
nb.cells[14].source = header + old_src

nbf.write(nb, 'materi/16_klasifikasi_lulc_jatim.ipynb')
print("Cell 14 fixed.")
print("Preview:")
print(nb.cells[14].source[:300])
