import nbformat as nbf

nb = nbf.read('materi/16_klasifikasi_lulc_jatim.ipynb', as_version=4)

new_code = '''# ─ Koneksi Copernicus ─
_sesi_api = {}

def siapkan_koneksi():
    if "token" not in _sesi_api:
        c_id = os.environ.get("CDSE_CLIENT_ID") or input("CDSE Client ID     : ").strip()
        c_sec = os.environ.get("CDSE_CLIENT_SECRET") or getpass.getpass("CDSE Client Secret : ").strip()
        resp = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data={"grant_type": "client_credentials", "client_id": c_id, "client_secret": c_sec}
        )
        if resp.status_code != 200:
            raise Exception(f"Gagal otentikasi CDSE! {resp.text}")
        _sesi_api["token"] = resp.json()["access_token"]
    return _sesi_api["token"]

# ─ Evalscript sederhana: single scene leastCC, masking cloud ─
EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: ["B02","B03","B04","B05","B06","B07","B08","B8A","B11","B12","CLM","dataMask"],
    output: { bands: 10, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  if (sample.dataMask === 0) return [NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN];
  if (sample.CLM === 1)      return [NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN];
  return [sample.B02, sample.B03, sample.B04, sample.B05,
          sample.B06, sample.B07, sample.B08, sample.B8A,
          sample.B11, sample.B12];
}
"""

def unduh_median_bbox(bbox_obj, ukuran_px):
    """Unduh nilai 10 band dari scene terbaik (leastCC) via raw requests Copernicus API."""
    token = siapkan_koneksi()
    w, h = ukuran_px

    # Konversi BBox sentinelhub ke list [minx, miny, maxx, maxy]
    if hasattr(bbox_obj, 'min_x'):
        bbox_list = [bbox_obj.min_x, bbox_obj.min_y, bbox_obj.max_x, bbox_obj.max_y]
    elif hasattr(bbox_obj, 'lower_left'):
        ll = bbox_obj.lower_left
        ur = bbox_obj.upper_right
        bbox_list = [ll[0], ll[1], ur[0], ur[1]]
    else:
        bbox_list = list(bbox_obj)

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
                    "maxCloudCoverage": BATAS_AWAN,
                    "mosaickingOrder": "leastCC"
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
        headers={"Authorization": f"Bearer {token}", "Accept": "image/tiff"},
        timeout=60
    )
    if req.status_code != 200:
        raise Exception(f"HTTP {req.status_code}: {req.text[:300]}")

    import rasterio
    from rasterio.io import MemoryFile
    with MemoryFile(req.content) as mem, mem.open() as ds:
        arr = ds.read()   # shape: (10, h, w)
        return np.transpose(arr, (1, 2, 0))  # shape: (h, w, 10)
'''

for idx, cell in enumerate(nb.cells):
    if 'def unduh_median_bbox' in cell.source or '_sesi_api' in cell.source:
        nb.cells[idx].source = new_code
        print(f"Cell {idx} replaced")
        break

nbf.write(nb, 'materi/16_klasifikasi_lulc_jatim.ipynb')
print("Notebook updated.")
