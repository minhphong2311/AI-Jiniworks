---
trigger: always_on
description: Các quy tắc cốt lõi trước khi hoàn thành task (ngắn gọn, tối ưu token).
---

# Core Workflow Rules

Trước khi đánh dấu hoàn thành bất kỳ task nào, bạn **BẮT BUỘC** phải:
1. Chạy unit tests và sửa toàn bộ lỗi (nếu có).
2. Gọi Subagent Reviewer để tự đánh giá lại bug, code style và các quy tắc dự án.

*(Nếu cần quy trình chi tiết về test và review, hãy kích hoạt skill `finish_task`).*
