# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/helpers.py
Shared utilities dùng chung cho toàn bộ app.
"""
import os
import json
import uuid
import time

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sites.json')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.json')


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            sites = json.load(f)
            # Migration to hierarchical menus
            needs_save = False
            for site in sites:
                if 'menus' in site:
                    for idx, menu in enumerate(site['menus']):
                        if 'id' not in menu:
                            menu['id'] = str(uuid.uuid4())
                            needs_save = True
                        if 'parent_id' not in menu:
                            menu['parent_id'] = None
                            needs_save = True
                        if 'order' not in menu:
                            menu['order'] = idx
                            needs_save = True

            if needs_save:
                with open(DATA_FILE, 'w', encoding='utf-8') as f_out:
                    json.dump(sites, f_out, ensure_ascii=False, indent=4)

            return sites
    except Exception:
        return []


def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def get_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def get_default_gemini_model():
    cfg = get_config()
    raw = cfg.get('gemini_model', '').strip()
    if not raw:
        return 'gemini-3.8-flash'
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    return parts[0] if parts else 'gemini-3.8-flash'


def get_gemini_models_to_try(extra_models=None):
    cfg = get_config()
    raw = cfg.get('gemini_model', '').strip()
    user_models = [p.strip() for p in raw.split(',') if p.strip()] if raw else []

    candidates = []
    if user_models:
        candidates.extend(user_models)
    else:
        candidates.append('gemini-3.6-flash')

    if extra_models:
        if isinstance(extra_models, list):
            candidates.extend(extra_models)
        elif isinstance(extra_models, str):
            candidates.append(extra_models)

    candidates.extend([
        'gemini-3.6-flash',
        'gemini-3.1-flash-lite',
        'gemini-3.5-flash-lite',
        'gemini-3.5-flash',
        'gemini-3.8-flash',
        'gemini-flash-latest'
    ])

    seen = set()
    result = []
    for m in candidates:
        if m and m not in seen:
            seen.add(m)
            result.append(m)
    return result


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def make_unique_slug(slug, existing_slugs):
    new_slug = slug
    counter = 2
    while new_slug in existing_slugs:
        new_slug = f"{slug}-{counter}"
        counter += 1
    return new_slug


def generate_slug_for_text(text):
    if not text:
        return ''
    
    config = get_config()
    slug_method = config.get('slug_method', 'google')
    
    try:
        from slugify import slugify
        
        if slug_method == 'google':
            from deep_translator import GoogleTranslator
            # Dịch ngôn ngữ đầu vào (Hàn/Việt...) sang tiếng Anh bằng deep-translator
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            
            # Google Translate web endpoint đôi khi trả về trang lỗi 500 nếu bị rate limit
            if translated and ('500 server error' in translated.lower() or 'that\'s an error' in translated.lower() or 'that’s an error' in translated.lower()):
                print("Google Translate bị lỗi 500, tự động fallback về bỏ dấu.")
                slug = slugify(text)
            else:
                slug = slugify(translated)
            
        elif slug_method == 'gemini':
            # Dùng Gemini API
            api_key = config.get('gemini_api_key', '').strip()
            if not api_key:
                slug = slugify(text)  # Fallback
            else:
                from google import genai
                import re
                client = genai.Client(api_key=api_key)
                prompt = f'''Translate this EXACTLY to a short URL slug (lowercase english words, hyphen separated).
Output ONLY the slug, nothing else. No explanations, no markdown, no punctuation.
Examples:
- 부동산AI융합학과 -> real-estate-ai
- 회사 소개 -> about-us
- 학과/학생활동 -> student-activities
Input: {text}
Output:'''
                slug = None
                for model in get_gemini_models_to_try():
                    try:
                        response = client.models.generate_content(model=model, contents=prompt)
                        if response and response.text:
                            slug_raw = response.text.strip().lower()
                            slug_raw = slug_raw.split('\n')[0].strip()
                            slug = re.sub(r'[^a-z0-9\-]+', '', slug_raw)
                            if slug:
                                break
                    except Exception as ge:
                        print(f"[Gemini Slug] Model {model} failed: {ge}")
                        continue
                if not slug:
                    slug = slugify(text)
                
        else: # 'none'
            # Chỉ loại bỏ dấu, không dịch (ví dụ: Giới Thiệu -> gioi-thieu)
            slug = slugify(text)
        
        if not slug:
            import urllib.parse
            return urllib.parse.quote(text).lower()
        return slug
    except Exception as e:
        print('Error auto generating slug:', e)
        import urllib.parse
        return urllib.parse.quote(text).lower()


# ---------------------------------------------------------------------------
# URL / path helpers
# ---------------------------------------------------------------------------

def parse_folder_slug(param):
    """Parse a menu_param string into (folder, slug) tuple.

    Format: 'folder--slug' or just 'slug'
    """
    if '--' in param:
        parts = param.split('--', 1)
        return parts[0], parts[1]
    return "", param


# ---------------------------------------------------------------------------
# File cleanup
# ---------------------------------------------------------------------------

def delete_menu_files(site_id, menu_param):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, 'output', site_id)
    if not os.path.exists(output_dir):
        output_dir = os.path.join(base_dir, 'output')

    files_to_delete = [
        f'temp_render_{menu_param}.html',
        f'temp_render_{menu_param}.png',
        f'temp_target_{menu_param}.png'
    ]
    for f in files_to_delete:
        path1 = os.path.join(output_dir, f)
        if os.path.exists(path1):
            try:
                os.remove(path1)
                print(f"Deleted {path1}")
            except Exception as e:
                print(f"Failed to delete {path1}: {e}")

        path2 = os.path.join(base_dir, 'output', site_id, f)
        if os.path.exists(path2):
            try:
                os.remove(path2)
                print(f"Deleted {path2}")
            except Exception:
                pass

    # Also delete generated code files (.html, .css, .js)
    folder, slug = parse_folder_slug(menu_param)

    if folder:
        target_dir = os.path.join(base_dir, 'output', site_id, folder)
    else:
        target_dir = os.path.join(base_dir, 'output', site_id)

    code_files = [f'{slug}.html', f'{slug}.css', f'{slug}.js']
    for f in code_files:
        p = os.path.join(target_dir, f)
        if os.path.exists(p):
            try:
                os.remove(p)
                print(f"Deleted {p}")
            except Exception:
                pass

    # If this menu itself was a root folder, delete its folder directory
    folder_dir = os.path.join(base_dir, 'output', site_id, slug)
    if os.path.isdir(folder_dir):
        import shutil
        try:
            shutil.rmtree(folder_dir)
            print(f"Deleted folder {folder_dir}")
        except Exception as e:
            print(f"Failed to delete folder {folder_dir}: {e}")


# ---------------------------------------------------------------------------
# Menu tree helpers
# ---------------------------------------------------------------------------

def assign_folders_from_roots(menus):
    """Assign the 'folder' field for every menu based on its root ancestor's slug.

    Root menus (parent_id is None) will be treated as folders.
    All descendants of a root menu will inherit that root's slug as their folder.
    """
    # Build id → menu map
    menu_map = {m['id']: m for m in menus if 'id' in m}

    # Find root menus (no parent)
    def get_root_slug(menu_id):
        m = menu_map.get(menu_id)
        if not m:
            return ''
        if not m.get('parent_id'):
            return m.get('slug', '')
        return get_root_slug(m['parent_id'])

    for m in menus:
        m['folder'] = get_root_slug(m['id'])


# ---------------------------------------------------------------------------
# CSS Guide helpers
# ---------------------------------------------------------------------------
def get_css_guide_instruction(css_links=None):
    css_links_str = ""
    if css_links:
        css_links_str = (
            f"0. Dự án sử dụng CSS chuẩn tại: " + ", ".join(css_links) +
            ".\nTUYỆT ĐỐI TUÂN THỦ khoảng cách (margin, padding) đã định nghĩa trong guide. Không thêm margin/padding dư thừa làm sai lệch giao diện gốc (ví dụ: nếu guide dùng padding-bottom, đừng thêm margin-bottom).\n"
        )
    
    return (
        "\n\nĐẶC BIỆT LƯU Ý VỀ CẤU TRÚC VÀ FORMAT CSS:\n"
        + css_links_str +
        "1. BẮT BUỘC FORMAT CSS (RẤT QUAN TRỌNG): Mỗi rule CSS (selector + thuộc tính) phải nằm trọn trên 1 dòng riêng biệt (Single-line CSS) và phải có XUỐNG DÒNG (\\n) giữa các rule khác nhau.\n"
        "Tuyệt đối KHÔNG gộp toàn bộ file thành 1 dòng, KHÔNG xuống dòng bên trong dấu ngoặc nhọn {}. KHÔNG TẠO DẤU CÁCH (space) dư thừa giữa các thuộc tính. Viết `.class{prop:val;}` thay vì `.class { prop: val; }`.\n"
        "ĐỐI VỚI THẺ @media (CỰC KỲ QUAN TRỌNG - NẾU LÀM SAI SẼ BỊ HỦY KẾT QUẢ):\n"
        "- TUYỆT ĐỐI KHÔNG ĐƯỢC VIẾT GỘP toàn bộ nội dung của @media lên cùng 1 dòng!\n"
        "- BẮT BUỘC phải XUỐNG DÒNG ngay sau dấu `{` mở của @media.\n"
        "- Mỗi rule CSS bên trong @media BẮT BUỘC phải nằm trên 1 dòng riêng biệt và kết thúc bằng `\\n`.\n"
        "- BẮT BUỘC phải XUỐNG DÒNG trước dấu `}` đóng của @media.\n"
        "VD mẫu CHUẨN MỰC BẮT BUỘC LÀM THEO:\n"
        ".area-box{}\n"
        ".area-box .area-inner{}\n"
        "@media(max-width: 1024px){\n"
        "    .area-box{}\n"
        "    .area-box .area-inner{}\n"
        "    .area-box .txt01{font-family: 'Pretendard';font-weight: 700;font-size: 32px;color: #262626;}\n"
        "}\n"
        "2. THỨ TỰ THUỘC TÍNH TEXT (NHƯ FIGMA): BẮT BUỘC sắp xếp các thuộc tính text theo đúng thứ tự sau: font-family, font-weight, font-size, line-height, color.\n"
        "VD: `.txt01{font-family: 'Pretendard';font-weight: 700;font-size: 32px;line-height: 120%;color: #262626;}`\n"
        "3. SỬ DỤNG ẢNH PNG CHO ICON - TUYỆT ĐỐI KHÔNG DÙNG SVG: BẮT BUỘC sử dụng thẻ <img> với định dạng PNG (vd: <img src=\"./images/menu_slug/icon_name.png\" alt=\"icon\">) cho tất cả các icon thay vì sử dụng thẻ span hay font icon. TUYỆT ĐỐI KHÔNG sử dụng thẻ <svg> trực tiếp trong HTML hoặc mã data:image/svg+xml trong CSS. Đối với các icon nhỏ nằm trong các thẻ a, button, KHÔNG dùng thẻ img và KHÔNG dùng svg, mà dùng file ảnh .png qua css background-image hoặc vẽ bằng CSS thuần / pseudo-element (::before, ::after, border, transform). TUYỆT ĐỐI KHÔNG chèn ký tự mũi tên (↗, →, v.v.) vào text HTML của nút bấm. Ưu tiên tái sử dụng ::before có sẵn của .btn-link; nếu dùng ::after thì phải tắt ::before (content:none), không bao giờ để 2 icon xuất hiện cùng lúc.\n"
        "4. RESPONSIVE DESIGN LÀ BẮT BUỘC: Mọi giao diện sinh ra phải hỗ trợ Responsive (co giãn tốt trên Mobile, Tablet, PC).\n"
        "5. ĐƯỜNG NỐI SƠ ĐỒ TỔ CHỨC: Đối với sơ đồ cây/tổ chức (có đường nối ngang/dọc), BẮT BUỘC dùng CSS pseudo-elements (::before, ::after) để vẽ đường kẻ. Không dùng <div> trống làm đường kẻ.\n"
        "6. JAVASCRIPT: Code Javascript (nếu có) BẮT BUỘC phải được format bình thường với đầy đủ xuống dòng (newline) và thụt lề (indentation). TUYỆT ĐỐI KHÔNG được ép Javascript thành 1 dòng (minify).\n"
        "7. ĐỔI TÊN HÌNH ẢNH: Đặt tên file ảnh có ý nghĩa (ví dụ `quick-link-01.png`), không dùng `icon`, `img`, `pic`. Trả về `rename_map` nếu có.\n"
        "8. QUY TẮC CSS SCOPING (KẾ THỪA CLASS CHA): BẮT BUỘC phải gắn kèm class cha (parent scoping) khi viết CSS cho các phần tử con để tránh xung đột CSS toàn cục. Ngoại trừ các thẻ chung của hệ thống như `.content-box` và `.con-box` (không được dùng làm class cha kế thừa), với các component cụ thể (ví dụ: khối cha ngoài cùng là `.org-chart`), thì các class con bên trong BẮT BUỘC phải viết là `.org-chart .org-top{}` thay vì chỉ viết `.org-top{}`.\n"
        "9. QUY TẮC THẺ <a> (LINK ACCESSIBILITY): TẤT CẢ các thẻ <a> đều BẮT BUỘC phải có thuộc tính `title`. Đặc biệt: nếu là số điện thoại (href=\"tel:...\") thì gán `title=\"전화걸기\"`; nếu là email (href=\"mailto:...\") thì gán `title=\"메일보내기\"`; với các thẻ a thông thường khác thì đặt title mô tả nội dung của link.\n"
        "10. QUY TẮC SỬ DỤNG HEADING: Tiêu đề trực tiếp của `.con-box` BẮT BUỘC LUÔN là `h4.h4-tit01` (tuyệt đối KHÔNG dùng `h5` hay `h6` làm tiêu đề trực tiếp của `.con-box`). Thẻ `h5.h5-tit01` dùng trong `.con-box02` hoặc bên trong component con (`.bg-box`, `.notice-box`, `.info-wrap`). Thẻ `h6.h6-tit01` dùng trong `.con-box03` hoặc component con. KHÔNG bọc thẻ wrapper thừa (`.con-box02`/`.con-box03`) nếu component con đã chứa `h5`/`h6`.\n"
        "11. KHÔNG SỬ DỤNG THẺ STRONG/B/EM/I: Tuyệt đối KHÔNG sử dụng các thẻ như `<strong>`, `<b>`, `<em>`, `<i>` để định dạng văn bản (ví dụ không dùng `<strong class=\"prof-name\">`). Thay vào đó, hãy sử dụng các thẻ ngữ nghĩa như `<p>`, `<span>`, hoặc `<div>` kết hợp với Class phù hợp (như `.prof-name`) và điều chỉnh `font-weight` trong CSS.\n"
        "12. HẠN CHẾ SỬ DỤNG CLASS CON-P: Class `.con-p` CHỈ được dùng cho các đoạn văn bản dài (paragraph). Đối với các nội dung rất ngắn như tên người, chức vụ (ví dụ: \"주임교수\"), nhãn (label), hoặc ngày tháng, TUYỆT ĐỐI KHÔNG dùng class `.con-p`. Hãy tự đặt một class phù hợp với ngữ cảnh (như `.prof-position`, `.date`, `.label`, v.v.).\n"
        "13. QUY TẮC SỬ DỤNG THẺ P VÀ SPAN (SEMANTIC HTML): TUYỆT ĐỐI KHÔNG lạm dụng thẻ `<span>`. Thẻ `<span>` CHỈ được dùng cho các đoạn text nhỏ nằm ngang hàng (inline) bên trong một thẻ text khác. Đối với các khối văn bản (dù chỉ có 1 dòng hoặc vài chữ như đoạn mô tả, địa chỉ, lời dẫn), BẮT BUỘC phải dùng thẻ `<p>` (hoặc `<div>` nếu là khối bọc ngoài). Thiết kế HTML phải chuẩn ngữ nghĩa khối (block) và nội tuyến (inline).\n"
    )
