# Lab #17: Multi-Memory Agent với LangGraph

**Mô tả:** Dự án xây dựng một AI Agent sử dụng framework `LangGraph` tích hợp hệ thống đa bộ nhớ (Multi-Memory Stack) nhằm quản lý ngữ cảnh thông minh, lưu trữ hồ sơ người dùng và truy xuất thông tin ngữ nghĩa.

## 1. Kiến trúc Hệ thống (Architecture)
Agent được trang bị 4 phân vùng bộ nhớ chuyên biệt:
- **Short-Term Memory (Conversation Buffer):** Lưu trữ ngữ cảnh hội thoại ngắn hạn trực tiếp trong state của LangGraph.
- **Long-Term Profile (Redis):** Lưu trữ các thông tin hồ sơ tĩnh, sở thích cá nhân, sự kiện dài hạn. (Tự động fallback về bộ nhớ giả lập nếu không có Redis Server).
- **Episodic Memory (JSON Log):** Lưu trữ nhật ký trải nghiệm, các sự kiện trong quá khứ.
- **Semantic Memory (ChromaDB + OpenAI Embeddings):** Truy xuất thông tin ngữ nghĩa dạng Vector để tìm kiếm các dữ kiện quá khứ cực nhanh.

Ngoài ra hệ thống tích hợp các logic cốt lõi:
- **Memory Router:** Phân tích ý định người dùng (Intent Classification) để định tuyến đến đúng bộ nhớ cần thiết.
- **Context Window Manager:** Tự động cắt tỉa (auto-trim) dựa trên phân cấp ưu tiên 4 tầng (4-level hierarchy) để tiết kiệm token budget mà không làm mất System Prompt.
- **LLM Conflict Resolution:** Dùng structured outputs để tự động trích xuất và giải quyết mâu thuẫn dữ liệu hồ sơ (Ví dụ: Cập nhật thông tin dị ứng từ "thịt bò" sang "đậu nành").

## 2. Cài đặt (Installation)

1. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Cấu hình biến môi trường:**
   Tạo file `.env` (hoặc copy từ `.env.example`) và điền API Keys của bạn:
   ```env
   OPENAI_API_KEY="sk-..."
   REDIS_URL="redis://..."
   ```

## 3. Chạy thử nghiệm tương tác (Interactive Test)

Chạy kịch bản chat trực tiếp trên terminal để thử nghiệm khả năng lưu/nhớ của Agent:
```bash
python3 src/agent/test_interactive.py
```
- Gõ `/clear` để xoá toàn bộ bộ nhớ của phiên hiện tại.
- Thử nhập các câu chứa thông tin cá nhân (VD: *"Tôi tên là Tài"*, *"Tôi là Kỹ sư AI"*) sau đó hỏi lại để xem Agent sử dụng loại bộ nhớ nào (Redis/Chroma) để trả lời.

## 4. Chạy Benchmark và Đánh giá hiệu suất

Chạy kiểm tra tự động trên 10 kịch bản hội thoại đa lượt (Multi-turn conversations) để đánh giá tỷ lệ tận dụng ngữ cảnh, điểm số relevance và ngân sách token:

```bash
# 1. Chạy đánh giá (sẽ gọi OpenAI API)
python3 src/benchmark/evaluator.py

# 2. Sinh báo cáo Markdown
python3 src/benchmark/generate_report.py
```
Kết quả sẽ được xuất trực tiếp ra file `benchmark_report.md`. Đọc thêm về phân tích rủi ro quyền riêng tư (Privacy Risks) tại file `REFLECTION.md`.

## 5. Chấm điểm Lab (Automated Grading)

Dự án đi kèm một script tự động kiểm tra code và chấm điểm theo đúng Rubric đánh giá của Lab 17:
```bash
python3 tests/check_lab.py
```
