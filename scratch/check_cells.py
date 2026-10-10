import nbformat as nbf

nb = nbf.read('materi/16_klasifikasi_lulc_jatim.ipynb', as_version=4)

# Print cell 14 to see extraction code
src14 = nb.cells[14].source
print("=== CELL 14 (extraction) ===")
print(src14)
