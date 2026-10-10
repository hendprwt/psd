"""
Test cepat ke Sentinel Hub API dengan evalscript sederhana (bukan ORBIT).
Jalankan: python scratch\test_api.py
Lalu input Client ID dan Secret kalau diminta.
"""
import os, requests

EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: ["B02","B03","B04","B08"],
    output: { bands: 4, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  if (sample.dataMask === 0) return [NaN,NaN,NaN,NaN];
  return [sample.B02, sample.B03, sample.B04, sample.B08];
}
"""

c_id  = os.environ.get("CDSE_CLIENT_ID")  or input("Client ID  : ").strip()
c_sec = os.environ.get("CDSE_CLIENT_SECRET") or input("Secret     : ").strip()

resp = requests.post(
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
    data={"grant_type": "client_credentials", "client_id": c_id, "client_secret": c_sec}
)
if resp.status_code != 200:
    print("AUTH GAGAL:", resp.text); exit(1)

token = resp.json()["access_token"]
print("Token OK!")

skema = {
    "input": {
        "bounds": {
            "bbox": [112.6000, -7.2500, 112.6027, -7.2473],   # ~270m x 270m → 90m/px untuk 3x3
            "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
        },
        "data": [{
            "type": "sentinel-2-l2a",
            "dataFilter": {
                "timeRange": {"from": "2025-01-01T00:00:00Z", "to": "2025-06-30T23:59:59Z"},
                "maxCloudCoverage": 30,
                "mosaickingOrder": "leastCC"
            }
        }]
    },
    "output": {
        "width": 3, "height": 3,
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
print(f"Status: {req.status_code}")
if req.status_code == 200:
    import rasterio, numpy as np
    from rasterio.io import MemoryFile
    with MemoryFile(req.content) as mem, mem.open() as ds:
        arr = ds.read()
        print("Array shape:", arr.shape)
        print("Sample values (tengah):", arr[:, 1, 1])
    print("\n✅ SUKSES! API bekerja dengan benar.")
else:
    print("GAGAL:", req.text[:500])
