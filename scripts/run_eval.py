import json
import os
import sys
import time

# Them thu muc goc vao sys.path de import duoc rag_logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_logic import chat_with_rag
from logger_config import logger

def run_evaluation():
    golden_set_file = os.path.join(os.path.dirname(__file__), "golden_set.jsonl")
    output_file = os.path.join(os.path.dirname(__file__), "eval_report.md")
    
    if not os.path.exists(golden_set_file):
        print(f"Khong tim thay file {golden_set_file}")
        return

    test_cases = []
    with open(golden_set_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                test_cases.append(json.loads(line))

    print("BAT DAU CHAY EVALUATION RAG... (vui long doi, ket qua se duoc luu vao file eval_report.md)")

    total_tests = len(test_cases)
    passed_tests = 0

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("# 🧪 Kết Quả Đánh Giá RAG Pipeline\n\n")
        out.write(f"**Tổng số câu hỏi test:** {total_tests}\n\n")
        out.write("---\n\n")
        
        for i, case in enumerate(test_cases):
            test_id = case.get("id", f"Test_{i+1}")
            level = case.get("level", "N/A")
            question = case.get("question", "")
            expected_keywords = case.get("expected_keywords", [])
            expected_sources = case.get("expected_sources", [])
            should_refuse = case.get("should_refuse", False)
            
            print(f"Dang chay cau {i+1}/{total_tests}: [{test_id}]...")
            
            out.write(f"### Câu {i+1}: [{test_id}] {level}\n")
            out.write(f"**❓ Câu hỏi:** {question}\n\n")
            out.write(f"- **Kỳ vọng Keywords:** {expected_keywords}\n")
            if expected_sources:
                out.write(f"- **Kỳ vọng Sources:** {expected_sources}\n")
            out.write(f"- **Từ chối (Should refuse):** {should_refuse}\n\n")
            
            start_time = time.time()
            
            try:
                # Goi RAG
                stream, ref_text, ref_images, new_part_ids = chat_with_rag(question)
                bot_answer = ""
                for chunk in stream:
                    bot_answer += chunk
                
                latency = time.time() - start_time
                
                # Auto grading
                bot_answer_lower = bot_answer.lower()
                
                # Check keywords (Neu any tu khoa ky vong xuat hien la pass cho refusal, hoac All cho binh thuong)
                keywords_passed = True
                failed_keywords = []
                if should_refuse:
                    # Voi cau tu choi, chi can 1 trong cac ly do la duoc
                    if expected_keywords:
                        keywords_passed = any(kw.lower() in bot_answer_lower for kw in expected_keywords)
                        if not keywords_passed:
                            failed_keywords = expected_keywords
                else:
                    for kw in expected_keywords:
                        if kw.lower() not in bot_answer_lower:
                            keywords_passed = False
                            failed_keywords.append(kw)
                
                # Check refusal
                refusal_keywords = ["không ghi thông tin", "tài liệu hiện tại không", "từ chối", "không đủ", "thiếu dữ kiện", "không tự ước lượng"]
                actual_refused = any(rk in bot_answer_lower for rk in refusal_keywords)
                refusal_passed = (should_refuse == actual_refused)
                
                # Check sources
                sources_passed = True
                failed_sources = []
                if ref_text:
                    ref_text_lower = ref_text.lower()
                    for src in expected_sources:
                        if src.lower() not in ref_text_lower and src.lower() not in bot_answer_lower:
                            sources_passed = False
                            failed_sources.append(src)
                elif expected_sources and not should_refuse:
                    sources_passed = False
                    failed_sources = expected_sources
                
                is_pass = keywords_passed and refusal_passed and sources_passed
                
                if is_pass:
                    passed_tests += 1
                    status_icon = "✅ **PASSED**"
                else:
                    status_icon = "❌ **FAILED**"
                
                out.write(f"**Trạng thái:** {status_icon}\n\n")
                if not is_pass:
                    if not keywords_passed:
                        out.write(f"- Lỗi: Không khớp keywords kỳ vọng: {failed_keywords}\n")
                    if not refusal_passed:
                        out.write(f"- Lỗi: Phản hồi từ chối không khớp kỳ vọng (Kỳ vọng từ chối: {should_refuse}, Thực tế: {actual_refused})\n")
                    if not sources_passed:
                        out.write(f"- Lỗi: Không tìm thấy nguồn: {failed_sources}\n")
                    out.write("\n")

                out.write(f"**⏱ Thời gian:** {latency:.2f}s\n\n")
                out.write(f"**🤖 Bot trả lời:**\n> {bot_answer.strip().replace(chr(10), chr(10)+'> ')}\n\n")
                
                if ref_text:
                    out.write(f"**📚 Nguồn trích dẫn (Bot):**\n{ref_text.strip()}\n\n")
                
                out.write("---\n")

            except Exception as e:
                out.write(f"**Trạng thái:** ❌ ERROR\n\n")
                out.write(f"**Lỗi RAG:** {e}\n\n---\n")

        # Summary 
        out.write(f"\n## TỔNG KẾT\n")
        out.write(f"- Số câu test: {total_tests}\n")
        out.write(f"- Pass: {passed_tests}\n")
        out.write(f"- Fail: {total_tests - passed_tests}\n")
        out.write(f"- Accuracy: {(passed_tests/total_tests)*100 if total_tests > 0 else 0:.1f}%\n")

    print(f"\nDa hoan tat test. Pass {passed_tests}/{total_tests}. Vui long mo file scripts/eval_report.md de xem ket qua chi tiet.")

if __name__ == "__main__":
    # Ep kieu in stdout mac dinh thanh utf-8 cho chac an tren windows
    sys.stdout.reconfigure(encoding='utf-8')
    run_evaluation()
