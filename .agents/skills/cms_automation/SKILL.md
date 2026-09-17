---
name: cms_automation
description: Kích hoạt khi cần tự động hóa Playwright, viết script Deploy Toàn bộ (Menus, Folders, Ảnh), Deploy Pages, tự động upload tài nguyên hình ảnh lên hệ thống CMS JiniWorks.
---
# CMS Automation Rules (Playwright & JiniWorks)

## HTML Injection in Page Editor
Khi viết automation cho màn hình Edit Page có sử dụng CodeMirror/Froala tích hợp Angular (CMS JiniWorks):
- **ƯU TIÊN** dùng kết hợp JavaScript (`CodeMirror.setValue` và `scope.editor.item.contentText = html;`) để chèn mã nhằm đảm bảo tốc độ và đồng bộ dữ liệu vào Angular Model.
- **Quy trình chuẩn**:
  1. Click nút `< / >` (`button[data-cmd="html"]`) để mở Code View của Froala.
  2. Bơm code bằng JS: Tìm `.CodeMirror` và gọi `cm.CodeMirror.setValue(html);` HOẶC tìm `textarea.fr-code` để set `value` và dispatch event `input`.
  3. Bơm code vào Angular scope: Tìm Element có scope chứa `editor.item`, gọi `$apply()` để set `s.editor.item.contentText = html;`.
  4. Click nút `< / >` một lần nữa để Editor đồng bộ code trở lại view trực quan.

## Save & Đóng Form Edit Page
- Khi Save Editor, ưu tiên quét các nút ẩn của Angular trước: `button[ng-click="editor.save()"]` hoặc `button[ng-click="pg.save()"]` vì các nút này trực tiếp lưu nội dung Editor.
- Sau khi có thông báo SweetAlert (`button.confirm`), phải nhấn `confirm`.
- **Đóng Form Edit Page**: Ưu tiên duyệt DOM tìm Scope chứa hàm `s.editor.goBack()` của Angular và gọi nó để thoát khỏi màn hình HTML Editor một cách an toàn nhất. Nếu không thấy mới fallback bấm các nút UI (`이전으로`, `목록으로`, `닫기`, `List`). Hãy chú ý đóng mọi popup SweetAlert trước khi bấm Back để tránh bị block.
- **Mở HTML Editor**: Khi tìm nút để vào HTML Editor (thường là biểu tượng `.zmdi-brush`, hoặc `ng-click="goEditor"`), bắt buộc phải dọn dẹp (đóng) mọi modal `Edit Page Info` (như Modal thông tin trang có nút `닫기`) đang mở đè lên màn hình trước. TUYỆT ĐỐI không bấm nhầm vào nút `ng-click="edit"` vì nó sẽ mở lại modal Sửa thông tin thay vì mở Trình chỉnh sửa HTML.
- **Tối ưu hóa Reload (Page Manager)**: TUYỆT ĐỐI KHÔNG sử dụng `about:blank` hard-reload khi vòng lặp chuyển qua lại giữa các Folder/Page trong Page Manager. Nếu cần chuyển Folder, chỉ việc bấm thẳng vào thẻ `<a>` của thư mục đó trên cây jsTree cột trái (`folder_anchor`). Chỉ ép tải lại toàn bộ trang nếu phát hiện UI bị lỗi/văng khỏi List View.

## Browser Emulation & Stability
- **Playwright Viewport**: ALWAYS set `no_viewport=True` in `browser.new_context()` instead of specifying a fixed resolution.
- **AngularJS SPA Blank Screen Recovery**: 
  - ALWAYS add an Auto-Recovery Retry Loop when navigating hash routes.
  - Navigate to `about:blank` then to the target URL, wait for `domcontentloaded`.
  - Check for a key UI element (like `#folderTree.config`).
- **Menu Selection by Tree Path (Trong form Tạo Trang)**: Giao diện jsTree của CMS JiniWorks luôn tự động nối mã ID vào tên menu (vd: `link01 - 2188`). Do đó, **BẮT BUỘC ƯU TIÊN** dò tìm menu bằng `cms_menu_id` (lấy từ dữ liệu trả về ở bước Tạo Menu). Nếu fallback về tìm theo tên path, phải dùng thuật toán **Suffix Matching** (cắt đuôi ` - id` và so khớp mảng ngược từ dưới lên) để bỏ qua các cấp Root dư thừa không có trong dữ liệu gốc.

## Quy trình Deploy Toàn bộ lên CMS (Menus, Folders, Ảnh)
- Hoạt động dưới dạng Background Task qua API `run_full_deploy`.
- Trước khi deploy, sắp xếp menu từ nông đến sâu bằng **Topological Sort** (Tính toán Depth).
- Sử dụng API `getMenuMap` để lấy toàn bộ danh sách menu thực tế (không dùng `getTreeList`).
- So sánh trùng lặp đồng thời cả **Tên Menu** (`menuNm`) và **Mã Menu Cha** (`parentMenuCd`).
- Khóa màn hình bằng popup SweetAlert2, hiển thị Progress Bar. Backend poll `/api/deploy_status` mỗi 2s. Trạng thái tải được gọi là "Deploying...".
- **Tự động tạo cấu trúc Folder (Page Manager)**: TUYỆT ĐỐI KHÔNG dùng API `pageService.addFolder` vì API này đã bị vô hiệu hóa trên CMS. Bắt buộc dùng UI Automation giả lập thao tác người dùng: Click chuột phải vào thư mục gốc (jstree-anchor đầu tiên) -> Chọn "Thêm thư mục" -> Điền tên form -> Lưu.
- **Tối ưu hóa (Batching Folder Creation):** Việc tạo thư mục phải được gộp lại (Batching). Playwright thực hiện lặp lại vòng lặp (chuột phải -> Add -> Điền -> Save) để tạo toàn bộ thư mục bị thiếu MÀ KHÔNG ĐƯỢC TẢI LẠI TRANG. Chỉ Reload lại giao diện ĐÚNG 1 LẦN DUY NHẤT ở cuối quy trình để xác minh tất cả thư mục.

## Quy trình Deploy Trang tĩnh (Pages)
- Khi tạo trang, CMS phải lưu vào đúng **Thư mục con (Folder)**. Gán đúng ID của `Folder_anchor` trên Modal jstree.
- **Tự động tạo Folder nếu thiếu**: Trước khi chọn thư mục, phải kiểm tra xem thư mục đó đã tồn tại trên CMS chưa. Nếu chưa có, phải tự động chạy quy trình tạo Folder qua UI (như mô tả ở trên).
- **Duplicate Warning**: Tự động nhấn nút Đóng (`닫기`) bằng phím Escape hoặc selector nếu có cảnh báo trùng lặp.
- **Grid View**: Luôn kiểm tra và tự động nhấn nút chuyển sang List View (biểu tượng `fa-list`) trước khi tìm nút Edit/Brush.

## Tự động Upload Hình ảnh (Res-Img Manager)
- Trước khi lưu Editor CMS, tự động quét ảnh (`output/<site_id>/<folder>/images/<slug>/`) hoặc khi chạy quy trình Deploy Toàn bộ (`assets/img/content/img-ready.png`).
- Điều hướng đến `#!/res-img`.
- **Trích xuất `res_org` động:** CMS có thể dùng nhiều res_org khác nhau (như `kookmin`, `gtec` v.v.). Không được fix cứng. Phải dùng Playwright soi cây DOM lấy ID của thư mục gốc dạng `/_res/<res_org>/<site_id>/img/_anchor`.
- Tạo thư mục con `content` nếu chưa có (Click phải -> `추가`).
- **Nghiêm ngặt sử dụng các Selectors chuẩn Angular khi Upload:**
  - Nút tải lên: `button[ng-click="img.upload()"]`.
  - Nguồn tải file: `input[type="file"][flow-btn]`.
  - Tuyệt đối không dùng các selector phỏng đoán giao diện dễ hỏng hóc.
- Tự động thay thế đường dẫn cục bộ trong HTML thành: `/_res/<res_org>/<site_id>/img/content/<filename>`.
