---
name: ui_ux_guidelines
description: Cấu trúc thư mục, kiến trúc giao diện, routing, quy tắc HTML/CSS/JS (AdminLTE) của dự án Jiniworks CMS.
---
# 1. Cấu trúc thư mục & Kiến trúc chung
- **templates/ và static/**: HTML, CSS, JS cho Web UI Flask gốc.
- **assets/**: Tài nguyên deploy.
  - assets/ai_prompts/: HTML mồi.
  - assets/img/: Hình tĩnh.
  - assets/layout/: Layout tĩnh.
- **data/**: CSDL JSON. Ẩn gitignore.
- **deployer/**: Module deploy CMS.
# 2. Quy tắc Routing
- URL trình duyệt là đuôi .do (ví dụ /preview/phong01/test/test01.do).
- Mở iframe dùng đường dẫn raw .html.
- Folder luôn lấy từ root ancestor slug.
- ID UUID dùng để sửa/xóa.
# 3. Đặc tả UI/UX đầy đủ

1. Điều hướng và Thương hiệu (Navbar):
   - Logo thương hiệu ở góc trái là chữ **AI Jiniworks** kích thước lớn (~1.65rem), được hiển thị dưới dạng chữ có màu sắc đặc trưng gradient (`linear-gradient(135deg, #00aeef, #8cc63f)`). Không có biểu tượng icon đi kèm.
2. Giao diện danh sách Site (index.html):
   - Không sử dụng thanh Sidebar bên trái. Bố cục hiển thị toàn màn hình (full-width/full-screen) sử dụng cấu trúc Top Navigation (`layout-top-nav`) của AdminLTE.
   - Khoảng cách lề trên (Top Padding) của nội dung chính được căn chỉnh đều với hai bên (sử dụng class `pt-3` khoảng ~16px) để tạo sự cân đối.
   - Phải có ô Tìm kiếm Site (Search Site) ở phía trên cùng để lọc nhanh danh sách Site theo ID hoặc Tên bằng JavaScript (tìm kiếm instant thời gian thực).
   - Các Site được hiển thị dưới dạng Box/Card mô phỏng cấu trúc bảng quản trị hosting gồm:
     - Header: Chứa Monitor Icon, Site ID (nền xám), và Tên Site.
     - Body: Hiển thị thống kê thực tế số lượng Trang con bên trong Site (Tổng số Trang, số Trang đã tạo files, số Trang chưa tạo files) kèm theo thanh tiến độ hoàn thành (progress bar).
     - Footer: Chứa cụm biểu tượng hành động chia làm hai nhóm:
       - Nhóm trái: ⚙️ Manage Site / Setup Menu, ➕ Add Menu.
       - Nhóm phải: 🛡️ Open CMS Admin, 📝 Edit Site Info, 🗑️ Delete Site.
3. Khi nhấn "Add Site", hiển thị popup nhập:
   - Site ID
   - Site Name
   - Cms Url
   - Css (Mỗi link 1 dòng)
   - Js (Mỗi link 1 dòng)
   - System Login:
     - Admin
     - Password
4. Sau khi lưu (Tạo Site mới):
   - Lưu thông tin vào file JSON.
   - Hiển thị Site trong danh sách Trang chủ (index.html). Các Site thêm mới nhất sẽ được đảo thứ tự để luôn **hiển thị lên đầu danh sách**.
5. Khi nhấn vào Tên Site hoặc nút xem (icon ⚙️ ở chân thẻ):
   - Chuyển hướng đến trang chi tiết Site (`site_detail.html`).
6. Cấu trúc mỗi Trang con (Page) gồm:
   - Page Name
   - Child Folder (Folder - để trống nếu ở thư mục gốc)
   - Slug đường dẫn (Đóng vai trò là Tên File HTML lúc sinh code, ví dụ: `gioi-thieu` tạo thành `gioi-thieu.html`)
   - Link Figma Dev Mode
   - Layout (Chỉ có 2 loại tùy chọn: `sub-template` và `sub-template-tab`)
7. Sau khi lưu Trang con:
    - Lưu vào file JSON của Site tương ứng.
    - Trang mới được chèn tự động lên vị trí trên cùng của danh sách (không nằm dưới đáy).
8. Có nút Sửa để chỉnh sửa thông tin của từng Trang con:
    - Cho phép thay đổi Page Name, Child Folder, Slug, Link Figma, Layout.
    - Lưu thay đổi vào JSON và tự động di chuyển/đổi tên các file code đã sinh tương ứng trên đĩa cứng nếu đổi Child Folder hoặc Slug.
9. Có nút Xóa để xóa Trang con:
    - Cho phép xóa hoàn toàn Trang con khỏi cấu trúc JSON.
    - Tự động xóa các file HTML/CSS/JS đã sinh tương ứng của trang con đó và dọn dẹp thư mục con nếu thư mục bị trống hoàn toàn để giữ hệ thống sạch sẽ.
10. Giao diện chi tiết Site (site_detail.html) và Trang chủ (index.html):
    - Khung thông tin Site ở đầu trang phải dàn hàng ngang chiếm trọn màn hình (full-width). (Lưu ý: Cấu hình Gemini API Key và Figma Token đã được tách thành cài đặt toàn cục, lưu chung tại file `data/config.json` và chỉnh sửa ở màn hình **System Settings** riêng biệt qua nút bánh răng trên top navbar).
    - Phải có ô Tìm kiếm Trang (Search Page) đặt sát ở góc bên trái để lọc nhanh danh sách Trang con. Ở góc phải, có nút **"Manage Folders"** (màu viền xanh dương) bên cạnh nút **"Add Page"** (màu xanh dương).
    - Nút **"Manage Folders"** mở ra một Modal hợp nhất cho phép:
      - Tạo Thư mục mới.
      - Xem danh sách các thư mục con hiện có của Site.
      - Thay đổi vị trí (Reorder) của các thư mục con bằng các nút mũi tên Di chuyển lên (`▲`) và Di chuyển xuống (`▼`). Thứ tự mới sẽ tự động cập nhật lại nhãn lọc và hộp chọn dropdown.
      - Đổi tên (Rename) từng thư mục: Thay đổi metadata thư mục, tự động đổi đường dẫn lưu trữ của tất cả Trang con thuộc thư mục đó, và đổi tên thư mục vật lý tương ứng trên đĩa cứng.
      - Xóa (Delete) từng thư mục: Xóa thư mục khỏi danh sách, tự động di chuyển toàn bộ Trang con bên trong về **Thư mục gốc (Root)** để bảo toàn dữ liệu, và dọn dẹp thư mục vật lý.
    - Tất cả các Modal Popup (Thêm/Sửa Site, Thêm/Sửa Trang, Quản lý Thư mục) phải được chuẩn hóa đồng bộ 100%:
      - Tiêu đề modal (Header) sử dụng nền xám đậm (`bg-dark text-white`) với tiêu đề rút gọn tối giản: **"Add Site"**, **"Edit Site"**, **"Add Page"**, **"Edit Page"**, **"Manage Folders"**.
      - Nút lưu hành động chính (submit) luôn đặt tên là **"Save"** và sử dụng màu xanh dương (`btn-primary`).
      - Nút **"Close"** (màu xám `btn-secondary`) luôn được bố trí nằm ở phía bên trái của chân trang Modal (Modal Footer), nút **"Save"** nằm ở phía bên phải.
      - Toàn bộ các ô nhập dữ liệu (`input type="text"`, `select`, `textarea`) đều phải có cùng một kích thước chiều cao chuẩn (`form-control`), không pha trộn kích thước nhỏ (`form-control-sm`). Riêng ô nhập liệu Link Figma (`textarea`) phải thiết kế với chiều cao rộng rãi là **170px** để dễ hiển thị các liên kết dài.
      - Quy tắc CSS định dạng nút hành động (`.page-action-btn`, `.folder-action-btn`) tuyệt đối không dùng từ khóa `!important` cho thuộc tính `display: inline-flex;` để tránh xung đột làm ghi đè và ngăn cản việc ẩn phần tử bằng `display: none;` của inline style.
    - Trong biểu mẫu Thêm và Sửa Trang, trường **"Thư mục con (Folder)"** phải được hiển thị dưới dạng hộp chọn **Select box (Dropdown)** chứa danh sách các thư mục con đã được khởi tạo của Site đó để người dùng lựa chọn trực tiếp thay vì nhập liệu tự do.
    - Danh sách các Trang con được trình bày dưới dạng lưới ô (Grid Box layout - `col-md-6 col-lg-4`). Mỗi thẻ Trang con chứa:
      - Header: Page Name, biểu tượng file code, và nhãn hiển thị loại Layout ở góc bên phải.
      - Body: Child Folder, Tên file (Slug), trạng thái Figma Link, trạng thái Trang (Generated / Not Generated), và thông tin hướng dẫn.
      - Footer: Tích hợp các nút chức năng. Trong đó, các nút hành động icon-only ở góc phải (Deploy, Sửa, Xóa) phải được thiết kế đồng bộ kích thước vuông chuẩn **32x32px** (`page-action-btn`), căn giữa icon tuyệt đối.
11. Cơ chế hoạt động của các nút Preview và Deploy:
    - Nếu Trang con chưa được biên dịch thành công (trạng thái Not Generated), cả hai nút **Preview** và **Deploy** phải ở trạng thái **khóa màu xám (disabled)**.
    - Sau khi nhấn **Generate** và biên dịch thành công, hai nút bị khóa này sẽ lập tức được ẩn đi và kích hoạt hiển thị nút **Preview** (xanh lá) và **Deploy** (xanh dương) tương ứng bằng JavaScript.
    - Đặc biệt, khi mở màn hình Preview, Backend sẽ tự động phát hiện và chèn (inject) động tất cả các link CSS mặc định của Site vào phần `<head>` của trang HTML để đảm bảo luôn hiển thị đúng giao diện mà không phụ thuộc vào mã tĩnh trên đĩa cứng.
12. Cập nhật giao diện (Dark Mode & Đồng bộ Card):
    - Thêm nút bật/tắt Dark Mode trên thanh điều hướng (lưu trạng thái qua localStorage), code CSS/JS được tách riêng vào static/css/dark-mode.css và static/js/dark-mode.js.
    - Đồng bộ thiết kế của Site Card (Dashboard) và Page Card (Site Detail) với viền xanh (1.5px solid #00aeef) và bo góc 6px.
    - Bổ sung CSS hỗ trợ Dark Mode cho các thành phần tuỳ chỉnh (menu tree, modal bg-white, page card, viền input search).
    - Mặc định gán layout: 'sub-template' khi tạo Menu mới qua tính năng tạo nhanh (Inline Menu).
    - **Tree Checkboxes**: Không dùng checked mặc định; Dùng CSS custom với FontAwesome checkmark (\f00c) để tương thích Dark/Light mode; Nút Check All ở card-header cần bù trừ padding (margin-right: -4px) để thẳng hàng với Checkbox con.
    - **Trạng thái Nút Action**: Vô hiệu hóa và đổi màu (btn-secondary) khi không có checkbox nào được chọn.

# 4. Quy định về cấu trúc HTML / CSS khi sinh trang (Generated Pages)
- Toàn bộ quy chuẩn về cấu trúc HTML/CSS, heading hierarchy, rules bảng, danh sách, icon nút bấm và checklist kiểm tra chất lượng BẮT BUỘC tuân thủ tài liệu chuẩn duy nhất: `assets/ai_prompts/quality-checklist.md`.
