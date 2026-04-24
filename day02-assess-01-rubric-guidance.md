# Rubric — Lab #17: Build Multi-Memory Agent với LangGraph

**Mục đích:** Chấm bài Lab #17 bản 2 giờ, đúng theo slide.  
**Tổng điểm:** 100 điểm.  
**Hình thức nộp:** Nhóm nộp source/notebook + data files + `BENCHMARK.md`.

> Lab #17 chấm theo mục tiêu: agent có full memory stack, dùng LangGraph hoặc skeleton LangGraph, và có benchmark so sánh no-memory vs with-memory trên 10 multi-turn conversations.

---

## Overview

| Hạng mục | Điểm |
|----------|------:|
| 1. Full memory stack (4 backends/interface) | 25 |
| 2. LangGraph state/router + prompt injection | 30 |
| 3. Save/update memory + conflict handling | 15 |
| 4. Benchmark 10 multi-turn conversations | 20 |
| 5. Reflection privacy/limitations | 10 |
| **Tổng** | **100** |

---

## 1. Full memory stack — 25 điểm

**Cần chấm:**

- Có đủ 4 memory types ở mức interface:
  - short-term;
  - long-term profile;
  - episodic;
  - semantic.
- Mỗi memory có cách lưu/retrieve riêng, không gộp tất cả thành một blob mơ hồ.
- Chấp nhận backend thật hoặc backend giả lập, miễn là interface rõ.

Backend được chấp nhận:

| Memory type | Backend chấp nhận |
|-------------|-------------------|
| Short-term | list/sliding window/conversation buffer |
| Long-term profile | Redis, dict, JSON, simple KV store |
| Episodic | JSON list/file/log store |
| Semantic | Chroma, FAISS, vector search, keyword search fallback |

| Mức | Điểm | Mô tả |
|-----|------|-------|
| Tốt | 20-25 | Có đủ 4 memory types, interface rõ, mapping đúng vai trò từng loại |
| Trung bình | 10-19 | Có 3/4 memory types hoặc có 4 loại nhưng interface còn nhập nhằng |
| Kém | 0-9 | Chỉ có short-term/profile, thiếu episodic hoặc semantic |

---

## 2. LangGraph state/router + prompt injection — 30 điểm

**Cần chấm:**

- Có `MemoryState` hoặc state dict tương đương.
- Có node/function `retrieve_memory(state)`.
- Router gom memory từ nhiều backends vào state.
- Prompt có section rõ cho profile, episodic, semantic, recent conversation.
- Có trim/token budget cơ bản.

Code shape mong đợi:

```python
class MemoryState(TypedDict):
    messages: list
    user_profile: dict
    episodes: list[dict]
    semantic_hits: list[str]
    memory_budget: int
```

Lưu ý:

- Có thể dùng LangGraph thật hoặc skeleton LangGraph.
- Không full điểm nếu retrieve memory xong nhưng không inject vào prompt.

| Mức | Điểm | Mô tả |
|-----|------|-------|
| Tốt | 24-30 | State/router rõ, prompt sạch, 4 loại memory được dùng đúng chỗ |
| Trung bình | 12-23 | Có state/router nhưng prompt còn rối, hoặc thiếu 1-2 section memory |
| Kém | 0-11 | Không có router rõ ràng, hoặc memory không đi vào prompt |

---

## 3. Save/update memory + conflict handling — 15 điểm

**Cần chấm:**

- Có update ít nhất 2 profile facts.
- Có ghi episodic memory khi task hoàn tất hoặc có outcome rõ.
- Nếu user sửa fact cũ, fact mới được ưu tiên.
- Không append bừa khiến profile mâu thuẫn.

Test bắt buộc:

```text
User: Tôi dị ứng sữa bò.
User: À nhầm, tôi dị ứng đậu nành chứ không phải sữa bò.
Expected profile: allergy = đậu nành
```

| Mức | Điểm | Mô tả |
|-----|------|-------|
| Tốt | 12-15 | Update đúng, episodic save có ý nghĩa, conflict handling rõ |
| Trung bình | 6-11 | Có update nhưng conflict handling hoặc episodic save còn yếu |
| Kém | 0-5 | Hầu như không save/update, hoặc lưu fact mâu thuẫn |

---

## 4. Benchmark 10 multi-turn conversations — 20 điểm

**Cần chấm:**

- `BENCHMARK.md` có đúng 10 multi-turn conversations hoặc tương đương.
- Mỗi conversation có nhiều turn, không chỉ 1 prompt đơn lẻ.
- Có so sánh `no-memory` và `with-memory`.
- Có đủ nhóm test quan trọng:
  - profile recall;
  - conflict update;
  - episodic recall;
  - semantic retrieval;
  - trim/token budget.

Mẫu bảng benchmark:

| # | Scenario | No-memory result | With-memory result | Pass? |
|---|----------|------------------|---------------------|-------|
| 1 | Recall user name after 6 turns | Không biết | Linh | Pass |
| 2 | Allergy conflict update | Sữa bò | Đậu nành | Pass |
| 3 | Recall previous debug lesson | Không biết | Dùng docker service name | Pass |
| 4 | Retrieve FAQ chunk | Sai/thiếu | Đúng chunk | Pass |

Không bắt buộc đo latency thật. Có thể dùng word count/character count để ước lượng token/cost.

| Mức | Điểm | Mô tả |
|-----|------|-------|
| Tốt | 16-20 | Có 10 conversations rõ ràng, so sánh tốt, bao phủ đủ nhóm test |
| Trung bình | 8-15 | Có benchmark nhưng thiếu vài nhóm test hoặc mô tả còn sơ sài |
| Kém | 0-7 | Không đủ 10 conversations hoặc không có no-memory vs with-memory |

---

## 5. Reflection privacy/limitations — 10 điểm

**Cần chấm:**

- Nhận diện được ít nhất 1 rủi ro PII/privacy.
- Nêu được memory nào nhạy cảm nhất.
- Có đề cập deletion, TTL, consent, hoặc risk của retrieval sai.
- Có ít nhất 1 limitation kỹ thuật của solution hiện tại.

Gợi ý reflection:

1. Memory nào giúp agent nhất?
2. Memory nào rủi ro nhất nếu retrieve sai?
3. Nếu user yêu cầu xóa memory, xóa ở backend nào?
4. Điều gì sẽ làm system fail khi scale?

| Mức | Điểm | Mô tả |
|-----|------|-------|
| Tốt | 8-10 | Reflection cụ thể, có privacy + limitation kỹ thuật rõ |
| Trung bình | 4-7 | Có reflection nhưng còn chung chung |
| Kém | 0-3 | Không có reflection hoặc rất hời hợt |

---

## Bonus

Bonus chỉ dùng để phân biệt nhóm mạnh, không thay thế phần core.

| Bonus | Điểm gợi ý |
|-------|------------:|
| Redis thật chạy ổn | +2 |
| Chroma/FAISS thật chạy ổn | +2 |
| LLM-based extraction có parse/error handling | +2 |
| Token counting tốt hơn word count | +2 |
| Graph flow demo rõ, dễ explain | +2 |

Nếu chương trình cần thang 100 cố định, dùng bonus để tie-break thay vì cộng vượt trần.

---

## Red flags khi chấm

- Chỉ có short-term + profile, nhưng vẫn tự nhận là full memory stack.
- Có LangGraph name-drop nhưng không có state/router thật.
- Có database thật nhưng prompt không inject memory.
- Benchmark không phải multi-turn conversations, chỉ là 10 câu hỏi rời.
- Không có semantic retrieval test nào.
- Không có conflict update test nào.
- Lưu PII nhạy cảm nhưng không nhắc consent/TTL/deletion.

---

## Grading band summary

| Mức | Điểm | Đặc điểm |
|-----|------|----------|
| Tốt | 80-100 | Đủ 4 memory types, router rõ, benchmark 10 conversations, reflection tốt |
| Trung bình | 50-79 | Có phần lớn kiến trúc nhưng benchmark hoặc save/update còn yếu |
| Kém | < 50 | Thiếu full stack, thiếu router, hoặc benchmark không đạt yêu cầu |