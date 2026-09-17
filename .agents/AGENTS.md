# Core Project & Mindset Rules (AI Jiniworks)
## 1. Nguyên tắc Hệ thống & Backend
- **Tech Stack:** Python Flask, UI AdminLTE. Không Database SQL, chỉ JSON.
- **File Tạm:** Debug/test để ở scratch/. Xóa sau khi dùng.
- **Git:** KHÔNG tự động git push.
- **Unit Test:** Phải có test (pytest) trên môi trường cô lập (mock_env).
## 2. Kiến trúc Frontend & UI (Yêu cầu gọi Skill)
- ⚠️ **KHI LÀM VIỆC VỚI UI/HTML/CSS:** Bắt buộc gọi skill ui_ux_guidelines để đọc đặc tả UI trước khi code.
## 3. Hoàn thành Task (Yêu cầu gọi Skill)
- ⚠️ **TRƯỚC KHI HOÀN THÀNH:** Bắt buộc chạy Unit test (Pass) và gọi Subagent Reviewer.
- Nếu không rõ cách làm, hãy gọi skill inish_task.
## 4. Tư duy Kỹ thuật
- **Suy nghĩ trước khi code:** Trình bày rõ điểm đánh đổi. Có cách đơn giản hơn hãy nói ra.
- **Đơn giản là trên hết:** Code tối thiểu. Không tự ý abstract.
- **Sửa mang tính phẫu thuật:** Chỉ chạm vào những gì bắt buộc. Xóa dead code.
- **Mục tiêu rõ ràng:** Chuyển tác vụ thành test (VD: Viết test -> Pass). Lên kế hoạch kiểm chứng.
