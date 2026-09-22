import httpx

url = "https://guzdgiqfqqbuetbpickr.supabase.co"
service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd1emRnaXFmcXFidWV0YnBpY2tyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTY0MTU1MCwiZXhwIjoyMTA1MjE3NTUwfQ.Y4dO9UaCUmHujTKo7ZzUZmVjPfwQk-Wv8LmEidZi4PM"
headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}

tables = ["personas", "face_embeddings", "recognition_logs", "ml_training_records"]
for t in tables:
    r = httpx.get(f"{url}/rest/v1/{t}?select=*&limit=0", headers=headers, timeout=10)
    status = "EXISTS" if r.status_code == 200 else f"MISSING ({r.status_code})"
    print(f"  {t}: {status}")

r = httpx.post(
    f"{url}/rest/v1/rpc/match_face_embedding",
    headers=headers,
    json={"query_embedding": [0]*512, "match_threshold": 0.75, "match_count": 1},
    timeout=10,
)
fn_status = "EXISTS" if r.status_code in [200, 404] else f"ERROR ({r.status_code})"
print(f"  match_face_embedding: {fn_status}")

r = httpx.get(f"{url}/storage/v1/bucket/face-images", headers=headers, timeout=10)
print(f"  face-images bucket: {'EXISTS' if r.status_code == 200 else 'MISSING'} ({r.status_code})")
