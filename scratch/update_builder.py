import re
with open('scratch/build_nb16.py', 'r', encoding='utf8') as f:
    text = f.read()

with open('scratch/patch_nb16.py', 'r', encoding='utf8') as f:
    patch = f.read()
    new_code = patch.split("new_code = '''")[1].split("'''")[0]

text = re.sub(r'# ─ Koneksi Copernicus ─.*?return np\.asarray\(req\.get_data\(\)\[0\], dtype=np\.float32\)', new_code.replace('\\', '\\\\'), text, flags=re.DOTALL)

with open('scratch/build_nb16.py', 'w', encoding='utf8') as f:
    f.write(text)
print('Builder script updated.')
