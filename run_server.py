import sys
import os

# Thêm src/ vào Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Chạy RAG Server
import uvicorn
from mech_chatbot.api.rag_server import app, RAG_SERVER_HOST, RAG_SERVER_PORT

if __name__ == "__main__":
    print(f"Starting RAG Server on {RAG_SERVER_HOST}:{RAG_SERVER_PORT}")
    uvicorn.run(
        "mech_chatbot.api.rag_server:app",
        host=RAG_SERVER_HOST,
        port=RAG_SERVER_PORT,
        log_level="info",
        reload=False,
        workers=1,
    )
