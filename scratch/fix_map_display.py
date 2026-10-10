import nbformat as nbf
import re

nb = nbf.read('materi/16_klasifikasi_lulc_jatim.ipynb', as_version=4)

target_idx = -1
for i, cell in enumerate(nb.cells):
    if 'peta.save(PATH_PETA_HTML)' in cell.source:
        target_idx = i
        break

if target_idx != -1:
    src = nb.cells[target_idx].source
    
    new_src = re.sub(r'peta\s*$', '', src)
    new_src += '\nfrom IPython.display import IFrame\ndisplay(IFrame(src=PATH_PETA_HTML, width="100%", height="650px"))'
    
    nb.cells[target_idx].source = new_src
    nbf.write(nb, 'materi/16_klasifikasi_lulc_jatim.ipynb')
    print('Fixed map display using IFrame in Notebook.')
    
    # Also fix it in the builder so it doesn't break if run again
    with open('scratch/build_nb16.py', 'r', encoding='utf8') as f:
        text = f.read()
    
    text = re.sub(
        r'print\(f"Peta interaktif disimpan: \{PATH_PETA_HTML\}"\)\s+peta',
        'print(f"Peta interaktif disimpan: {PATH_PETA_HTML}")\nfrom IPython.display import IFrame\ndisplay(IFrame(src=PATH_PETA_HTML, width="100%", height="650px"))',
        text
    )
    with open('scratch/build_nb16.py', 'w', encoding='utf8') as f:
        f.write(text)

