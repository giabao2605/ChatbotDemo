import csv
import os
import sys
import time

# Them thu muc goc vao sys.path de import duoc rag_logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_logic import chat_with_rag
from logger_config import logger

def run_evaluation():
    csv_file = r"c:\Users\bao.nguyen\.gemini\antigravity\brain\e7a35397-4b4f-44b2-ad83-088006ecf1e1\artifacts\eval_golden_set.csv"
    output_file = os.path.join(os.path.dirname(__file__), "evaluation_results.md")
    
    if not os.path.exists(csv_file):
        print(f"Khong tim thay file {csv_file}")
        return

    results = []
    print("BAT DAU CHAY EVALUATION RAG... (vui long doi, ket qua se duoc luu vao file evaluation_results.md)")

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("# 🧪 Kết Quả Đánh Giá RAG Pipeline\n\n")
        
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                level = row["Level"]
                question = row["Cau_Hoi"]
                expected = row["Dap_An_Chuan"]
                
                print(f"Dang chay cau {i+1}...")
                
                out.write(f"### Câu {i+1}: {level}\n")
                out.write(f"**❓ Câu hỏi:** {question}\n\n")
                
                start_time = time.time()
                
                try:
                    # Goi RAG
                    stream, ref_text, ref_images, _ = chat_with_rag(question)
                    bot_answer = ""
                    for chunk in stream:
                        bot_answer += chunk
                    
                    latency = time.time() - start_time
                    
                    out.write(f"**⏱ Thời gian:** {latency:.2f}s\n\n")
                    out.write(f"**🤖 Bot trả lời:**\n> {bot_answer.strip()}\n\n")
                    out.write(f"**✅ Đáp án chuẩn:**\n> {expected}\n\n")
                    
                    if ref_text:
                        out.write(f"**📚 Nguồn trích dẫn (Bot):** {ref_text.strip().replace(chr(10), ' ')}\n\n")
                    
                    out.write("---\n")
                    
                    results.append({
                        "cau_hoi": question,
                        "dap_an_bot": bot_answer,
                        "dap_an_chuan": expected,
                        "thoi_gian": latency
                    })
                except Exception as e:
                    out.write(f"**❌ Lỗi RAG:** {e}\n\n---\n")

    print("\nDa hoan tat test. Vui long mo file scripts/evaluation_results.md de xem ket qua chi tiet.")

if __name__ == "__main__":
    # Ep kieu in stdout mac dinh thanh utf-8 cho chac an tren windows
    sys.stdout.reconfigure(encoding='utf-8')
    run_evaluation()
