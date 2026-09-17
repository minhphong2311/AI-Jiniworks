---
name: finish_task
description: Hướng dẫn chi tiết cách chạy Unit Test và cách gọi Subagent Reviewer để đánh giá code trước khi kết thúc một task.
---

# Quy trình Hoàn thành Task (Testing & Reviewing)

Bạn chỉ được gọi Skill này khi chuẩn bị kết thúc một task (đã code xong).

## 1. Yêu cầu về Unit Test (TDD)
- Bạn phải đảm bảo mọi thay đổi logic đều có test case đi kèm (bao gồm happy path và edge cases).
- Sử dụng pytest (hoặc framework tương ứng của dự án).
- Môi trường test phải được cô lập (sử dụng fixture/mock), tuyệt đối không làm thay đổi thư mục `data/` hay `output/` thực tế của dự án.
- Chạy lệnh test trên terminal (vd: `pytest tests/`). Nếu có lỗi, bạn phải sửa cho đến khi Pass toàn bộ.

## 2. Yêu cầu gọi Subagent Reviewer
- Không được kết thúc lượt làm việc nếu chưa được Reviewer thông qua.
- Mở một Subagent (sử dụng công cụ `invoke_subagent` nếu có, hoặc tạo prompt cho Subagent Reviewer).
- Cung cấp cho Reviewer bản tóm tắt các file đã sửa, yêu cầu tìm kiếm bug, check style, và đối chiếu với Rules của dự án.
- Nếu Reviewer báo lỗi, hãy tiến hành sửa và yêu cầu Review lại. Khi nào Reviewer "Approve" thì task mới chính thức hoàn thành.
