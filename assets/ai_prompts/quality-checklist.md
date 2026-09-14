# Figma → HTML Quality Checklist

## 1. Kiểm tra Layout
- Kiểm tra kích thước (width, height) đã đúng với thiết kế.
- Kiểm tra vị trí (position) của từng thành phần.
- Kiểm tra khoảng cách (margin, padding, gap).
- Kiểm tra căn lề (align, justify).
- Kiểm tra border, border-radius.
- Kiểm tra màu nền (background).
- Kiểm tra shadow, opacity (nếu có).
- Kiểm tra thứ tự hiển thị (z-index) nếu có nhiều lớp.

## 2. Kiểm tra Typography
- Kiểm tra font-family.
- Kiểm tra font-size.
- Kiểm tra font-weight.
- Kiểm tra line-height.
- Kiểm tra letter-spacing.
- Kiểm tra màu chữ.
- Kiểm tra text-align.
- Kiểm tra text-transform (nếu có).
- Kiểm tra xuống dòng giống thiết kế.
- Kiểm tra khoảng cách giữa các đoạn văn bản.

## 3. Kiểm tra HTML Structure
- Kiểm tra cấu trúc HTML đúng với thiết kế.
- Kiểm tra thứ tự các phần tử giống Figma.
- Kiểm tra cấu trúc cha - con (Hierarchy).
- Kiểm tra sử dụng đúng thẻ HTML theo quy chuẩn của dự án.
- Kiểm tra không có thẻ HTML hoặc phần tử dư thừa.

## 4. Kiểm tra Class và Rule
- Kiểm tra class được đặt đúng theo quy chuẩn của dự án.
- Kiểm tra không tạo class trùng lặp.
- Kiểm tra không tạo class không cần thiết.
- Kiểm tra sử dụng đúng Typography Class của dự án.
- Kiểm tra sử dụng đúng HTML Template của dự án.
- Kiểm tra `.con-box` sử dụng `h4`.
- Kiểm tra `.con-box02` sử dụng `h5`.
- Kiểm tra `.con-box03` sử dụng `h6`.
- Kiểm tra Không lồng ghép thẻ bọc thừa (`.con-box02`) trong `.con-box`: Các phần tử nội dung trực tiếp đặt ngang hàng với thẻ `h4` bên trong `.con-box`.
- Kiểm tra Không dùng thẻ bọc thừa (`.container-box`) trong `.btn-box`: Nút bấm đặt trực tiếp bên trong `.btn-box`.
- Kiểm tra Xử lý ký tự đặc biệt trong đoạn chú thích (`.mark-p`, `.mark-p01`): BẮT BUỘC XÓA BỎ ký tự hoa thị `※` ở đầu câu của thẻ `<p class="mark-p">` và `<p class="mark-p01">` (vì CSS đã tự sinh ra). Tuyệt đối không giữ lại ký tự này.
- Kiểm tra Xử lý padding cho đoạn văn cuối cùng: Nếu có nhiều đoạn văn (`.con-p`) liên tiếp, hoặc đoạn văn nằm sát trên `.mark-p`, thẻ `<p>` cuối cùng bắt buộc phải có class `no-pd` (`<p class="con-p no-pd">`).
- Kiểm tra Caption của Table (`<caption>`): BẮT BUỘC phải có thẻ `<strong>` đi kèm trước `<span>`. Nội dung của thẻ `<strong>` phải lấy chính xác từ thẻ tiêu đề `<h>` nằm ngay phía trên bảng.
- Kiểm tra Quy tắc định dạng danh sách: KHÔNG dùng thẻ `<p>` và `<br>` để làm danh sách. Các đoạn văn bản có đánh số (1., 2., 3.) phải dùng `<ol class="ol-type01">` và `<li>`. Danh sách gạch đầu dòng dùng `<ul class="ul-type-dot">` hoặc `<ul class="ul-type-bar">` và `<li>`.

## 5. Kiểm tra Hình ảnh
- Kiểm tra toàn bộ hình ảnh đã được export.
- Kiểm tra hình ảnh sử dụng đúng định dạng (.jpg hoặc .png).
- Kiểm tra đúng kích thước theo thiết kế.
- Kiểm tra đúng tỷ lệ, không bị méo hoặc cắt.
- Kiểm tra đúng đường dẫn hình ảnh.
- Kiểm tra icon không bị mờ hoặc vỡ hình.

## 6. Kiểm tra CSS
- Kiểm tra CSS đúng với thiết kế.
- Kiểm tra không có CSS trùng lặp.
- Kiểm tra không có CSS dư thừa.
- Kiểm tra không sử dụng inline style.
- Kiểm tra animation và transition (nếu có).

## 7. Kiểm tra Responsive
- Kiểm tra giao diện Desktop.
- Kiểm tra giao diện Tablet.
- Kiểm tra giao diện Mobile.
- Kiểm tra không xuất hiện thanh cuộn ngang.
- Kiểm tra hình ảnh không bị méo.
- Kiểm tra text không bị vỡ bố cục.
- Kiểm tra khoảng cách giữa các thành phần trên từng thiết bị.

## 8. Kiểm tra Chức năng
- Kiểm tra tất cả link hoạt động đúng.
- Kiểm tra button hoạt động đúng.
- Kiểm tra hiệu ứng hover.
- Kiểm tra trạng thái active.
- Kiểm tra trạng thái focus.
- Kiểm tra các thành phần tương tác khác (nếu có).

## 9. So sánh với Figma
- Kiểm tra giao diện tổng thể giống Figma.
- Kiểm tra bố cục.
- Kiểm tra typography.
- Kiểm tra màu sắc.
- Kiểm tra khoảng cách.
- Kiểm tra hình ảnh.
- Kiểm tra icon.
- Kiểm tra từng section giống với thiết kế.
- Click Preview và so sánh lại với Figma.
- Nếu phát hiện khác biệt, tự động chỉnh sửa HTML/CSS và kiểm tra lại.

## 10. Kiểm tra Chất lượng Code
- Kiểm tra HTML được format đúng.
- Kiểm tra CSS được format đúng.
- Kiểm tra không có code dư thừa.
- Kiểm tra không có class hoặc id không sử dụng.
- Kiểm tra không có lỗi HTML.
- Kiểm tra không có lỗi CSS.

## 11. Hoàn thành
- Xác nhận toàn bộ giao diện giống với thiết kế Figma.
- Xác nhận toàn bộ Rule của dự án đã được tuân thủ.
- Xác nhận Preview giống thiết kế trước khi hoàn thành.