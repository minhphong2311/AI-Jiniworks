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
- Kiểm tra TUYỆT ĐỐI KHÔNG sử dụng thẻ <svg> trực tiếp trong HTML.

## 4. Kiểm tra Class và Rule
- Kiểm tra class được đặt đúng theo quy chuẩn của dự án.
- Kiểm tra không tạo class trùng lặp.
- Kiểm tra không tạo class không cần thiết.
- Kiểm tra sử dụng đúng Typography Class của dự án.
- Kiểm tra sử dụng đúng HTML Template của dự án.
- Kiểm tra `.con-box` LUÔN sử dụng `h4.h4-tit01` làm tiêu đề trực tiếp (ngay bên trong `.con-box`, KHÔNG dùng `h5` hoặc `h6` thay thế `h4` ở cấp này dù content ngắn hay dài).
- Kiểm tra `.con-box02` sử dụng `h5.h5-tit01`. Lưu ý: `h5` KHÔNG được đặt trực tiếp trong `.con-box`; nếu có `h5` thì phải bọc trong `.con-box02` HOẶC bên trong một component con như `.bg-box`, `.notice-box`, `.info-wrap` (chứ không phải là tiêu đề cấp `.con-box`).
- Kiểm tra `.con-box03` sử dụng `h6.h6-tit01`. Quy tắc tương tự: `h6` đặt trong `.con-box03` HOẶC trong component con, KHÔNG phải tiêu đề trực tiếp của `.con-box`.
- Kiểm tra Không lồng ghép thẻ bọc thừa (`.con-box02`, `.con-box03`) vào trong `.con-box` chỉ để chứa `h5`/`h6` đứng đơn lẻ khi đã có component con phù hợp (`.bg-box`, `.notice-box`). Nếu component con đã chứa `h5`/`h6`, KHÔNG cần thêm `.con-box02`/`.con-box03` bọc ngoài.
- Kiểm tra Không dùng thẻ bọc thừa (`.container-box`) trong `.btn-box`: Nút bấm đặt trực tiếp bên trong `.btn-box`.
- Kiểm tra Xử lý ký tự đặc biệt trong đoạn chú thích (`.mark-p`): BẮT BUỘC XÓA BỎ ký tự hoa thị `※` ở đầu câu của thẻ `<p class="mark-p">` (vì CSS đã tự sinh ra). Tuyệt đối không giữ lại ký tự này.
- Kiểm tra Xử lý padding cho đoạn văn cuối cùng: Nếu có nhiều đoạn văn (`.con-p`) liên tiếp, hoặc đoạn văn nằm sát trên `.mark-p`, thẻ `<p>` cuối cùng bắt buộc phải có class `no-pd` (`<p class="con-p no-pd">`).
- Kiểm tra Caption của Table (`<caption>`): BẮT BUỘC phải có thẻ `<strong>` đi kèm trước `<span>`. Nội dung của thẻ `<strong>` phải lấy chính xác từ thẻ tiêu đề `<h>` nằm ngay phía trên bảng.
- Kiểm tra Quy tắc định dạng danh sách: KHÔNG dùng thẻ `<p>` và `<br>` để làm danh sách. Các đoạn văn bản có đánh số (1., 2., 3.) phải dùng `<ol class="ol-type01">` và `<li>`. Danh sách gạch đầu dòng dùng `<ul class="ul-type-dot">` hoặc `<ul class="ul-type-bar">` và `<li>`.
- Kiểm tra Nút bấm & Biểu tượng (Button & Link Icons): TUYỆT ĐỐI KHÔNG để các ký tự mũi tên hoặc icon (như `↗`, `→`, `➔`, `➜`, `›`, `»`, `▼`, `▲`, `+`, `↓`, v.v.) dưới dạng text thuần (unicode) bên trong nội dung văn bản của thẻ nút bấm (`<a>`, `<button>`, `.btn`, `.btn-link`, `.btn-file`, `.link-btn`). Mọi mũi tên hoặc biểu tượng đi kèm nút bấm BẮT BUỘC phải là ICON (dùng class có sẵn như `.btn-link` có `ico-open.png` qua `::before`, `.btn-file` có `ico-download.png` qua `::before`, hoặc dùng ảnh `.png` qua CSS pseudo-element). Nội dung text bên trong nút bấm CHỈ chứa nhãn chữ thuần túy (VD: `<a class="btn btn-link" ...>관련 링크 01</a>`). Ưu tiên tái sử dụng (override) trực tiếp `.btn-link:before` (hoặc `.btn-file:before`) đã có sẵn trong `style.css` thay vì tạo thêm `::after`. Nếu bắt buộc phải dùng `::after`, BẮT BUỘC phải tắt hoàn toàn `::before` bằng `.btn-link:before { content: none; }`, TUYỆT ĐỐI KHÔNG để tồn tại đồng thời cả 2 pseudo-elements `::before` và `::after` trên cùng một nút.

## 5. Kiểm tra Hình ảnh
- Kiểm tra toàn bộ hình ảnh đã được export.
- Kiểm tra hình ảnh sử dụng đúng định dạng .jpg.
- Kiểm tra đúng kích thước theo thiết kế.
- Kiểm tra đúng tỷ lệ, không bị méo hoặc cắt.
- Kiểm tra đúng đường dẫn hình ảnh.
- Kiểm tra icon không bị mờ hoặc vỡ hình và sử dụng đúng định dạng .png.
- Kiểm tra TUYỆT ĐỐI KHÔNG sử dụng định dạng .svg (cả file .svg, thẻ <svg>, lẫn mã data:image/svg+xml trong CSS).

## 6. Kiểm tra CSS
- Kiểm tra CSS đúng với thiết kế.
- Kiểm tra không có CSS trùng lặp.
- Kiểm tra không có CSS dư thừa.
- Kiểm tra không sử dụng inline style.
- Kiểm tra không sử dụng mã data:image/svg+xml trong CSS background-image.
- Đối với các đường kẻ hoặc đường nối giữa các khối hộp: BẮT BUỘC chỉ sử dụng pseudo-elements CSS (::before và ::after) trên các khối để vẽ, không tạo thẻ div bọc hoặc ảnh rác.
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

**LƯU Ý NGHIÊM NGẶT:** Phải kiểm tra thị giác với độ sắc bén và chi tiết cao nhất. Không được bỏ qua bất kỳ sai lệch nào. Nếu phát hiện bất kỳ sự khác biệt nào về mũi tên, icon, đường kẻ, màu sắc, font chữ hoặc bố cục so với thiết kế Figma, BẮT BUỘC phải chỉ rõ điểm cần sửa và trả về `STATUS: NEEDS_FIX`!