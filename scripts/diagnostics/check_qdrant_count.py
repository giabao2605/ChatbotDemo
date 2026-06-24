from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient

load_dotenv()

qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

print("QDRANT_URL =", qdrant_url)
print("HAS_API_KEY =", bool(qdrant_api_key))

client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key
)

info = client.get_collection("TaiLieuKyThuat_v2")

print("points_count =", info.points_count)
print("vectors_count =", getattr(info, "vectors_count", None))