# Figma → HTML Quality Checklist

Bộ quy chuẩn kiểm tra chất lượng giao diện (Single Source of Truth) dành cho AI Vision & Code Review.

## 1. Độ Khớp Thị Giác & Figma (Visual Match)
- **Layout & Spacing**: Khớp 100% bố cục, kích thước, vị trí, căn lề, margin, padding, gap, border-radius và màu nền theo thiết kế Figma.
- **Typography & Màu sắc**: Đúng font-family, font-size, font-weight, line-height, letter-spacing, màu chữ và khoảng cách dòng/đoạn.
- **Đường viền & Đường kẻ khối**: Giữ đúng màu sắc và độ dày viền (như `border-top` màu chủ đạo trên các box `.info-wrap`, `.notice-box`). Đường kẻ/nối giữa các khối chỉ dùng pseudo-elements (`::before`, `::after`), tuyệt đối không tạo thẻ `div` bọc hoặc ảnh rác.
- **Responsive**: Co giãn mượt mà trên Desktop, Tablet, Mobile; không vỡ layout, không tràn viền hay xuất hiện thanh cuộn ngang.

## 2. Quy Chuẩn Cấu Trúc HTML Dự Án (Strict Project Rules)
- **Heading Hierarchy**: 
  - Tiêu đề trực tiếp của `.con-box` **LUÔN LUÔN** là `h4.h4-tit01` (KHÔNG dùng `h5` hoặc `h6` thay thế `h4` ở cấp này dù content ngắn hay dài).
  - Thẻ `h5.h5-tit01` dùng trong `.con-box02` hoặc bên trong component con (`.bg-box`, `.notice-box`, `.info-wrap`). Thẻ `h6.h6-tit01` dùng trong `.con-box03` hoặc component con.
  - Không lồng ghép thẻ bọc thừa (`.con-box02`, `.con-box03`) vào trong `.con-box` chỉ để chứa `h5`/`h6` khi đã có component con phù hợp.
- **Không dùng thẻ bọc thừa**: Đặt nút bấm trực tiếp bên trong `.btn-box` (KHÔNG bọc thêm `.container-box`).
- **Chú thích (`.mark-p`)**: BẮT BUỘC XÓA BỎ ký tự hoa thị `※` ở đầu câu thẻ `<p class="mark-p">` và `<p class="mark-p01">` (vì CSS đã tự sinh).
- **Padding đoạn văn cuối**: Nếu có nhiều đoạn văn (`.con-p`) liên tiếp hoặc nằm ngay phía trên `.mark-p`, thẻ `<p>` cuối cùng bắt buộc phải có class `no-pd` (`<p class="con-p no-pd">`).
- **Caption Bảng (`<caption>`)**: BẮT BUỘC có thẻ `<strong>` trước `<span>`. Nội dung `<strong>` phải lấy chính xác từ tiêu đề `<h>` nằm ngay phía trên bảng.
- **Định dạng Danh sách**: KHÔNG dùng `<p>` kèm `<br>` để làm danh sách. Danh sách có số thứ tự dùng `<ol class="ol-type01">` + `<li>`. Danh sách gạch đầu dòng/chấm tròn dùng `<ul class="ul-type-dot">` hoặc `<ul class="ul-type-bar">` + `<li>`.
- **Nút Bấm & Biểu Tượng (Button & Link Icons)**: 
  - TUYỆT ĐỐI KHÔNG để các ký tự mũi tên hoặc biểu tượng (`↗`, `→`, `➔`, `➜`, `›`, `»`, `▼`, `▲`, `+`, `↓`, v.v.) dưới dạng text unicode trong nội dung nút bấm (`<a>`, `<button>`, `.btn`, `.btn-link`, `.btn-file`, `.link-btn`).
  - Mọi dấu hiệu mũi tên/icon bắt buộc phải là ICON (dùng class hệ thống hoặc CSS pseudo-elements `::before` / `::after` với ảnh `.png`). Text nút bấm CHỈ chứa nhãn chữ thuần túy (VD: `<a class="btn btn-link" ...>관련 링크 01</a>`).
  - Ưu tiên tái sử dụng (override) `::before` có sẵn. Nếu bắt buộc dùng `::after`, phải tắt hoàn toàn `::before` bằng `.btn-link:before { content: none; }`, TUYỆT ĐỐI KHÔNG render đồng thời cả 2 pseudo-elements `::before` và `::after` trên cùng 1 nút.

## 3. Quy Chuẩn Hình Ảnh & CSS
- **Hình ảnh**: Export đầy đủ, đúng kích thước, đúng tỷ lệ, đường dẫn chuẩn `./images/{slug}/`. Icon dạng `.png` sắc nét, không vỡ.
- **CẤM SVG HOÀN TOÀN**: TUYỆT ĐỐI KHÔNG sử dụng định dạng `.svg` (cả file `.svg`, thẻ `<svg>`, lẫn mã `data:image/svg+xml` trong CSS).
- **CSS Clean & Scoping**: Không dùng inline style. Mỗi rule CSS 1 dòng riêng. Scoping theo class cha cụ thể.

## 4. Tiêu Chí Đánh Giá & Output
- **Kiểm tra thị giác nghiêm ngặt**: So sánh sắc nét từng chi tiết với Figma.
- Nếu phát hiện bất kỳ sai lệch nào về mũi tên, icon, đường kẻ, màu sắc, font chữ hoặc bố cục: BẮT BUỘC liệt kê chi tiết điểm cần sửa và trả về `STATUS: NEEDS_FIX`!
- Nếu toàn bộ giao diện đã khớp hoàn hảo 100% với Figma: Trả về `STATUS: PERFECT`.