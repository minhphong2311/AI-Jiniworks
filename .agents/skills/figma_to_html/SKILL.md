---
name: figma_to_html
description: Kích hoạt khi cần tự động sinh mã HTML/CSS từ thiết kế Figma, phân tích ảnh, trích xuất dữ liệu, hoặc sửa lỗi giao diện qua hệ thống AI Feedback.
---
# Figma to HTML Automation & AI Feedback Engine

## Import Menu from Image
- Uses Gemini 3.5 Flash to extract hierarchical menus.
- Instructs AI to use sequential integers (1, 2, 3...) for IDs and parent_ids to strictly maintain the hierarchy, instead of long UUIDs which AI often forgets or mismatches.
- Python code replaces these integer IDs with actual UUIDs post-processing.
- Requires `from google import genai` and `genai.Client(api_key=...)` (New SDK).

## Image-to-HTML & AI Hint (User Guidance & Dynamic JS)
- Hỗ trợ tải lên **Nhiều hình ảnh (Multiple Images)** cùng lúc. Hệ thống sẽ truyền toàn bộ các ảnh này vào Gemini Vision theo đúng trình tự. Mỗi ảnh được ngầm định tương ứng với một khối chức năng chính và AI sẽ tự động tạo ra một thẻ `<div class="con-box">` riêng biệt cho mỗi ảnh, xếp chồng theo thứ tự thời gian để tạo thành một trang dài (Long-page design).
- Users can guide the AI using the `ai_hint` field from the UI.
- When generating from Image, the system enforces a strict 4-step Chain-of-Thought in Gemini JSON (`vision_analysis`, `layout_analysis`, `ocr_text`, `components`, plus `html`, `css`).
- If `ai_hint` explicitly requests dynamic components (like Swiper, sliders, progress bars), the AI is fully permitted to insert `<script src="cdn">` and `<link>` tags, along with inline JS initialization at the end of the `html` string.
- This relaxation of rules applies to both the Image-to-HTML process and the Structural Refinement step for Figma-to-HTML, unlocking dynamic Javascript capabilities while maintaining HTML/CSS integrity.

## Quy trình Biên dịch (Dynamic Compilation)
- Sinh mã nguồn HTML/CSS/JS theo cấu trúc `output/<site_id>/<folder>/<slug>.<ext>`.
- Quá trình tạo phải được thực hiện bất đồng bộ (AJAX) và hiển thị trạng thái chờ build ("Analyzing...", "Generating...").
- Nếu Trang chưa được cấu hình Link Figma, nút "Generate" phải ở trạng thái disabled.
- Hệ thống luôn thực hiện biên dịch động trực tiếp từ cấu trúc thiết kế Figma:
  - Trích xuất dữ liệu JSON của Node ID từ Figma API và tải xuống bản đồ hình ảnh (Image Fills Mapping) bằng Personal Access Token (lưu bảo mật chung tại file `data/config.json`) để giải quyết toàn bộ các ảnh và màu nền gradient thực tế.
  - Chạy bộ dịch `compile_figma_node_to_html_css` hỗ trợ đầy đủ các thuộc tính Layout Sizing phức tạp của Figma (`HUG`, `FILL`, `FIXED`, `STRETCH`) để biên dịch trực tiếp ra mã nguồn HTML/CSS tĩnh tự động co giãn tương ứng.
  - Hoàn toàn KHÔNG sử dụng các mẫu giao diện ngoại tuyến được viết sẵn (Offline Fallback Templates).
  - Hỗ trợ lưu cache cấu trúc thiết kế trong tệp tin `data/figma_cache.json` để phục vụ biên dịch ngoại tuyến tức thời nếu Token bị trống hoặc lỗi kết nối.

## Vòng lặp Phản chiếu Thị giác Gemini (Visual Reflection Loop - 100% Figma Match)
- Tự động chụp ảnh màn hình giao diện sinh ra bằng Playwright và gửi kèm ảnh thiết kế Figma cho Gemini Vision (`gemini-3.6-flash` với cơ chế retry tự động). 
- AI kiểm tra và sửa lỗi trực tiếp theo **Checklist 7 bước** (`assets/ai_prompts/quality-checklist.md`):
  1. Layout (bố cục, kích thước, vị trí, căn lề, màu sắc).
  2. Typography (font-family, font-size, font-weight, line-height, letter-spacing, màu chữ, khoảng cách đoạn).
  3. HTML & Class (thẻ HTML chuẩn, Typography Class và HTML Template `.con-box → h4`, `.con-box02 → h5`, `.con-box03 → h6`).
  4. Hình ảnh (export đầy đủ, định dạng .jpg/.png, kích thước, đường dẫn).
  5. Responsive (Desktop, Tablet, Mobile, không vỡ layout).
  6. Chức năng (link, button, hover).
  7. So sánh 100% với Figma: Chỉnh sửa lại HTML/CSS cho tới khi khớp hoàn toàn thiết kế.
- **Quản lý File Tạm (Temp Files Cleanup):** Mọi file sinh ra trong quá trình kiểm tra (như `temp_render_...png`, `temp_target_...png`, v.v.) BẮT BUỘC phải lưu vào thư mục `scratch/` và tự động XÓA SẠCH ngay sau khi hoàn tất. Không được xả rác ra thư mục output gốc.

## Semantic Image Renaming (Đổi tên ảnh ngữ nghĩa)
- Các ảnh được tự động cắt từ Figma thường có tên vô nghĩa (như `test-01.png`). Hệ thống phải có bước dùng AI quét cấu trúc HTML và tự động đổi tên file ảnh vật lý (`os.rename`) thành các tên mô tả ý nghĩa chức năng.
- **Cấm ngặt nghèo:** Tuyệt đối không dùng các từ như `icon`, `image`, `img`, `pic` trong tên file ảnh (Vd: `quick-link-admission.png` là đúng, `quick-link-icon.png` là sai).

## Kiểm soát Tiến trình Nền (Cancellation Checkpoints)
- Các tác vụ Generate dài hạn chạy ngầm bắt buộc phải có các trạm kiểm tra (checkpoint) giữa những tác vụ nặng (Tải Figma, Compile, AI Feedback...). Nếu người dùng ấn Cancel, phải lập tức quăng `Exception("CANCELLED_BY_USER")` để giết chết toàn bộ tiến trình và giữ nguyên trạng thái là Cancelled, tuyệt đối không được tiếp tục chạy rồi ghi đè thành Success.

## Split-Screen Preview & AI Feedback Engine
- Giao diện xem Preview kết hợp với Phản hồi Thiết kế:
  - Khi bấm Preview, trang quản trị hiển thị giao diện chia đôi tích hợp thanh top navbar quản trị chung. Nút Preview chuyển hướng trực tiếp trên tab hiện tại.
  - Lưu ý kiến trúc: Màn hình Preview (`preview_frame.html`) hoạt động hoàn toàn độc lập, **không** kế thừa từ `base.html` để tối ưu hóa không gian. Việc hỗ trợ chế độ tối (Dark Mode) phải được liên kết thủ công (`dark-mode.js`/`css`) cùng các đoạn mã ghi đè (Overrides) CSS tùy chỉnh riêng cho Chatbox và Toolbar.
  - Bên trái hiển thị Iframe của trang giao diện thực tế (raw HTML) max-width 1920px.
  - Bên phải hiển thị một Chatbox giao tiếp với Design Critic Agent.
  - Chatbox hiển thị tin nhắn dạng **plain text** (tự động escape HTML entities). Lịch sử lưu vào `localStorage`.
  - Hỗ trợ tính năng Inline Editing (như ChatGPT) giúp người dùng dễ dàng chỉnh sửa lại prompt cũ (nút Edit) để gửi lại, và thao tác Copy nhanh bằng icon ẩn hiện khi hover.
- Bộ máy điều chỉnh HTML/CSS động:
  - Tích hợp **Google Gemini AI** (model: `gemini-3.1-flash-lite`, thư viện: `google-genai`).
  - Backend đọc nội dung **HTML và CSS** hiện tại, gửi kèm yêu cầu. AI cũng được truyền vào nội dung của các template chuẩn từ thư mục `assets/ai_prompts/` và danh sách các thư viện CSS chuẩn của Site.
  - AI trả về toàn bộ HTML và CSS đã được cập nhật dưới dạng JSON. Backend ghi đè trực tiếp vào file tương ứng, Iframe Preview tự động reload.
