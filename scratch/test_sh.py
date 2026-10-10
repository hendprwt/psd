import os
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, BBox, CRS, MimeType

ID = os.environ.get("CDSE_CLIENT_ID") or "dbdb4e56-42d4-4f9e-bf36-54b9d0bba623" # User might have put it in env
SEC = os.environ.get("CDSE_CLIENT_SECRET") or "some_secret"

print("Client ID:", ID)

cfg = SHConfig()
cfg.sh_client_id = ID
cfg.sh_client_secret = SEC
cfg.sh_base_url = "https://sh.dataspace.copernicus.eu"
cfg.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

# Try defining it with the true name "sentinel-2-l2a"
try:
    koleksi = DataCollection.SENTINEL2_L2A.define_from(
        "sentinel-2-l2a", service_url=cfg.sh_base_url)
except Exception:
    koleksi = [c for c in DataCollection.get_available_collections() if c.name == "sentinel-2-l2a"][0]

bbox = BBox([111.0, -8.85, 111.0003, -8.8497], crs=CRS.WGS84)

EVALSCRIPT = """//VERSION=3
function setup() {
  return {
    input: ["B02","B03","B04"],
    output: { bands: 3, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  return [sample.B02, sample.B03, sample.B04];
}
"""

req = SentinelHubRequest(
    evalscript=EVALSCRIPT,
    input_data=[SentinelHubRequest.input_data(
        data_collection=koleksi,
        time_interval=("2025-01-01", "2025-01-31"),
        maxcc=0.3)],
    responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
    bbox=bbox, size=(3, 3), config=cfg)

try:
    data = req.get_data()
    print("Success!", data[0].shape)
except Exception as e:
    import traceback
    traceback.print_exc()
