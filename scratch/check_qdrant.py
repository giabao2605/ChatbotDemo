import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

load_dotenv()
client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'), timeout=60)
collection_name = 'TaiLieuKyThuat_v2'

query_filter = models.Filter(
    should=[
        models.FieldCondition(key='metadata.ma_chinh', match=models.MatchValue(value='9.3.03951')),
        models.FieldCondition(key='metadata.ma_lien_quan', match=models.MatchValue(value='9.3.03951')),
        models.FieldCondition(key='metadata.file_goc', match=models.MatchValue(value='9.3.03951')),
        models.FieldCondition(key='metadata.ma_vat_tu', match=models.MatchValue(value='9.3.03951'))
    ]
)

try:
    results, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=query_filter,
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    print(f'Found {len(results)} exact metadata matches in Qdrant.')
    for res in results:
        m = res.payload.get('metadata', {})
        print(f"doc_id: {m.get('doc_id')}, ma_chinh: {m.get('ma_chinh')}, file_goc: {m.get('file_goc')}")
except Exception as e:
    print(f"Error: {e}")
