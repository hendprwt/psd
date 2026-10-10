import nbformat as nbf
nb = nbf.read('materi/16_klasifikasi_lulc_jatim.ipynb', as_version=4)
src = nb.cells[13].source
has_simple = 'function evaluatePixel(sample)' in src
has_orbit = 'mosaicking' in src and 'ORBIT' in src
has_leastCC = 'leastCC' in src
print('Simple 1-sample evalscript:', has_simple)
print('ORBIT removed:', not has_orbit)
print('leastCC present:', has_leastCC)
