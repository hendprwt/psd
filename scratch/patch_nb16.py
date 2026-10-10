import nbformat as nbf
import re

new_code = '''# ─ Koneksi Copernicus ─
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
function setup() {{
  return {{
    input: [{{ bands: ["B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12","SCL","dataMask"] }}],
    output: {{ bands: 10, sampleType: "FLOAT32" }},
    mosaicking: "ORBIT"
  }};
}}
function median1D(arr) {{
  if (arr.length === 0) return NaN;
  arr.sort(function(a,b){{return a-b;}});
  var m = Math.floor(arr.length/2);
  return arr.length%2 ? arr[m] : (arr[m-1]+arr[m])/2;
}}
function evaluatePixel(samples, scenes) {{
  var nama = ["B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12"];
  var buf = nama.map(function(){{return [];}});
  for (var i=0; i<samples.length; i++) {{
    var s=samples[i];
    if (s.dataMask===0) continue;
    var c=s.SCL;
    if (c===3||c===8||c===9||c===10||c===11) continue;
    if (FILTER_2A) {{
      var pid=scenes.orbits[i].tiles[0].productId;
      if (pid.indexOf("S2A")!==0) continue;
    }}
    for (var k=0;k<nama.length;k++) buf[k].push(s[nama[k]]);
  }}
  if (buf[0].length===0) return nama.map(function(){{return NaN;}});
  return buf.map(median1D);
}}
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
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
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
'''

nb_file = 'materi/16_klasifikasi_lulc_jatim.ipynb'
nb = nbf.read(nb_file, as_version=4)

for idx, cell in enumerate(nb.cells):
    if 'def unduh_median_bbox' in cell.source:
        nb.cells[idx].source = new_code
        break

nbf.write(nb, nb_file)
print("Notebook updated.")
