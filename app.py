# Author: sawyer88
# Email: phongnguyen@andvina.com

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-cms-builder'

# ---------------------------------------------------------------------------
# Import shared helpers
# ---------------------------------------------------------------------------

from routes.helpers import (
    load_data, save_data,
    get_config, save_config,
    get_default_gemini_model,
    get_gemini_models_to_try,
    generate_slug_for_text,
    assign_folders_from_roots,
    parse_folder_slug,
    get_css_guide_instruction,
    OUTPUT_DIR
)

def get_app_version():
    import subprocess
    import os
    
    # Mặc định Major version là 1
    major = "1"
    try:
        version_file = os.path.join(os.path.dirname(__file__), 'VERSION.txt')
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if '.' in content:
                    major = content.split('.')[0]
                else:
                    major = content
    except Exception:
        pass
        
    try:
        commit_count_str = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], stderr=subprocess.STDOUT).decode('utf-8').strip()
        commit_count = int(commit_count_str)
        
        # Cứ 100 commits thì tăng Minor, phần dư là Patch
        minor = commit_count // 100
        patch = commit_count % 100
        
        return f"{major}.{minor}.{patch}"
    except Exception:
        return f"{major}.0.0"

@app.context_processor
def inject_version():
    return dict(APP_VERSION=get_app_version())

# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------

from routes.generate import generate_bp
from routes.preview import preview_bp
from routes.deploy import deploy_bp
from routes.edit import edit_bp
from routes.delete import delete_bp
from routes.menu import menu_bp

app.register_blueprint(generate_bp)
app.register_blueprint(preview_bp)
app.register_blueprint(deploy_bp)
app.register_blueprint(edit_bp)
app.register_blueprint(delete_bp)
app.register_blueprint(menu_bp)

# ---------------------------------------------------------------------------
# Serve Assets
# ---------------------------------------------------------------------------

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# ---------------------------------------------------------------------------
# Slug API
# ---------------------------------------------------------------------------

@app.route('/api/generate-slug', methods=['POST'])
def generate_slug():
    data = request.json
    text = data.get('text', '').strip()
    slug = generate_slug_for_text(text)
    return jsonify({'slug': slug})

# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    sites = load_data()
    return render_template('index.html', sites=list(reversed(sites)))

# ---------------------------------------------------------------------------
# Site CRUD
# ---------------------------------------------------------------------------

@app.route('/add-site', methods=['POST'])
def add_site():
    site_id = request.form.get('site_id').strip()
    name = request.form.get('name').strip()
    url = request.form.get('url').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    js_guide = request.form.get('js_guide', '').strip()

    sites = load_data()
    if any(s['id'] == site_id for s in sites):
        flash(f'Site ID "{site_id}" already exists!', 'danger')
        return redirect(url_for('index'))

    new_site = {
        'id': site_id,
        'name': name,
        'url': url,
        'username': username,
        'password': password,
        'css_guide': request.form.get('css_guide', '').strip(),
        'js_guide': js_guide,
        'menus': []
    }
    sites.append(new_site)
    save_data(sites)
    flash(f'Successfully added site "{name}"!', 'success')
    return redirect(url_for('index'))


@app.route('/edit-site/<site_id>', methods=['POST'])
def edit_site(site_id):
    name = request.form.get('name').strip()
    url = request.form.get('url').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    css_guide = request.form.get('css_guide', '').strip()

    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash('Site not found!', 'danger')
        return redirect(url_for('index'))

    site['name'] = name
    site['url'] = url
    site['username'] = username
    site['password'] = password
    site['css_guide'] = css_guide

    save_data(sites)
    flash(f'Successfully updated site "{name}"!', 'success')
    return redirect(url_for('index'))


@app.route('/delete-site/<site_id>', methods=['POST'])
def delete_site(site_id):
    sites = load_data()
    updated_sites = [s for s in sites if s['id'] != site_id]
    save_data(updated_sites)

    target_dir = os.path.join(OUTPUT_DIR, site_id)
    if os.path.exists(target_dir):
        try:
            import shutil
            shutil.rmtree(target_dir)
        except Exception:
            pass

    flash('Successfully deleted site!', 'success')
    return redirect(url_for('index'))

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.route('/settings')
def settings():
    return render_template('settings.html')

# ---------------------------------------------------------------------------
# Site Detail
# ---------------------------------------------------------------------------

@app.route('/site/<site_id>')
def site_detail(site_id):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        flash(f'Site with ID: {site_id} not found', 'danger')
        return redirect(url_for('index'))

    if 'folders' not in site:
        site['folders'] = []

    import json
    menus_before = json.dumps(site.get('menus', []))
    
    # Ensure all menus have the correct folder assigned from their root ancestors
    assign_folders_from_roots(site.get('menus', []))

    menus_after = json.dumps(site.get('menus', []))
    modified = menus_before != menus_after

    for menu in site.get('menus', []):
        f = menu.get('folder', '').strip()
        if f and f not in site['folders']:
            site['folders'].append(f)
            modified = True

    if modified:
        save_data(sites)

    return render_template('site_detail.html', site=site)

# ---------------------------------------------------------------------------
# Folder management
# ---------------------------------------------------------------------------

@app.route('/site/<site_id>/add-folder', methods=['POST'])
def add_folder(site_id):
    folder_name = request.form.get('folder_name', '').strip().strip('/')
    if not folder_name:
        flash('Folder name cannot be empty!', 'danger')
        return redirect(url_for('site_detail', site_id=site_id))


# ---------------------------------------------------------------------------
# Config API
# ---------------------------------------------------------------------------

@app.route('/api/config', methods=['GET'])
def api_get_config():
    config = get_config()
    return jsonify({
        'success': True,
        'gemini_api_key': config.get('gemini_api_key', ''),
        'gemini_api_key_2': config.get('gemini_api_key_2', ''),
        'gemini_model': config.get('gemini_model', get_default_gemini_model()),
        'figma_token': config.get('figma_token', ''),
        'show_ui': config.get('show_ui', True),
        'slug_method': config.get('slug_method', 'google')
    })


@app.route('/api/config', methods=['POST'])
def api_save_config():
    data = request.json or {}
    config = get_config()
    if 'gemini_api_key' in data:
        config['gemini_api_key'] = data['gemini_api_key']
    if 'gemini_api_key_2' in data:
        config['gemini_api_key_2'] = data['gemini_api_key_2']
    if 'gemini_model' in data:
        config['gemini_model'] = data['gemini_model'].strip() or 'gemini-3.8-flash'
    if 'figma_token' in data:
        config['figma_token'] = data['figma_token']
    if 'show_ui' in data:
        config['show_ui'] = bool(data['show_ui'])
    if 'slug_method' in data:
        config['slug_method'] = data['slug_method']
    save_config(config)
    return jsonify({'success': True, 'message': 'Config saved'})

@app.route('/uploads/<site_id>/<filename>')
def serve_upload(site_id, filename):
    return send_from_directory(os.path.join(app.root_path, 'data', 'uploads', site_id), filename)


# ---------------------------------------------------------------------------
# Chat AI API
# ---------------------------------------------------------------------------

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    site_id = data.get('site_id', '').strip()
    menu_param = data.get('menu_param', '').strip()
    images_base64 = data.get('images', [])
    image_base64 = data.get('image') or ''
    image_base64 = image_base64.strip()

    if not user_message and not image_base64 and not images_base64:
        return jsonify({'success': False, 'reply': 'Please enter a request or attach an image.'}), 400

    folder, menu_slug = parse_folder_slug(menu_param)
    if folder:
        base_dir = os.path.join(OUTPUT_DIR, site_id, folder)
    else:
        base_dir = os.path.join(OUTPUT_DIR, site_id)

    css_path = os.path.join(base_dir, f'{menu_slug}.css')
    html_path = os.path.join(base_dir, f'{menu_slug}.html')
    js_path = os.path.join(base_dir, f'{menu_slug}.js')

    current_css = ''
    current_html = ''
    current_js = ''

    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            current_css = f.read()
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            current_html = f.read()
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            current_js = f.read()

    site_config = get_config()
    api_key = site_config.get('gemini_api_key', '').strip()
    api_key_2 = site_config.get('gemini_api_key_2', '').strip()

    if not api_key:
        return jsonify({
            'success': False,
            'reply': '⚠️ Gemini API Key not configured. Please go to Site Details and enter the API Key.'
        }), 400

    structure_template = ''
    structure_path = os.path.join(app.root_path, 'assets', 'ai_prompts', 'structure-template.html')

    if os.path.exists(structure_path):
        with open(structure_path, 'r', encoding='utf-8') as f:
            structure_template = f.read()

    try:
        from google import genai as _genai
        client = _genai.Client(api_key=api_key)
        client_2 = _genai.Client(api_key=api_key_2) if api_key_2 else None

        sites = load_data()
        site = next((s for s in sites if s['id'] == site_id), {})
        css_guide_raw = site.get('css_guide', '').strip()
        css_links = [link.strip() for link in css_guide_raw.split('\n') if link.strip()]
        css_guide_instruction = get_css_guide_instruction(css_links)

        prompt = f"""Bạn là một chuyên gia Frontend Developer.
Người dùng đang xem preview một trang web và muốn điều chỉnh giao diện.
Bạn có thể thay đổi cả HTML lẫn CSS để đáp ứng yêu cầu.

Yêu cầu của người dùng: "{user_message}"

Nội dung HTML hiện tại của trang:
```html
{current_html[:6000]}
```

Nội dung CSS hiện tại:
```css
{current_css[:5000]}
```

Nội dung JS hiện tại:
```javascript
{current_js[:5000]}
```{css_guide_instruction}

TÀI LIỆU THAM KHẢO VỀ CẤU TRÚC VÀ SUB-TEMPLATE MÀ BẠN NÊN ÁP DỤNG NẾU NGƯỜI DÙNG YÊU CẦU:

Mẫu cấu trúc giao diện chung (structure-template.html):
```html
{structure_template}
```

Nhiệm vụ:
1. NẾU KHÔNG HIỂU HOẶC THIẾU THÔNG TIN: Nếu yêu cầu không rõ ràng, hoặc bạn không tìm thấy thành phần cần sửa trong HTML gốc, hãy đặt `"needs_clarification": true` và điền câu hỏi vào trường `"question"` để hỏi lại người dùng. Bỏ trống html và css.
2. NẾU ĐÃ RÕ YÊU CẦU:
   a. "thinking": Phân tích logic (VD: "Người dùng muốn header width 100%. HTML gốc có class '.header-box'. Vậy tôi cần update class đó..."). QUAN SÁT KỸ HÌNH ẢNH GỐC để đảm bảo tỷ lệ đúng.
   b. TUYỆT ĐỐI KHÔNG SỬ DỤNG INLINE STYLE.
   c. FORMAT JAVASCRIPT: Code JS BẮT BUỘC phải được format bình thường với đầy đủ xuống dòng (newline) và thụt lề (indentation). TUYỆT ĐỐI KHÔNG được ép Javascript thành 1 dòng (minify). Trả về mã trong trường "js" (KHÔNG viết thẻ <script> bên trong HTML trừ khi nhúng CDN).
   d. Cung cấp TOÀN BỘ nội dung HTML (giữ nguyên cấu trúc <!DOCTYPE html> nếu có), CSS và JS mới. LƯU Ý CÚ PHÁP nháy đơn.

Trả lời theo định dạng JSON sau (không thêm gì ngoài JSON, không bọc markdown):
{{
  "needs_clarification": false,
  "question": "",
  "thinking": "Phân tích logic từng bước",
  "explanation": "Giải thích RẤT NGẮN GỌN thay đổi",
  "html": "toàn bộ nội dung HTML mới",
  "css": "toàn bộ nội dung CSS mới",
  "js": "toàn bộ nội dung JS mới (nếu có, không chứa thẻ <script>)"
}}"""

        import base64
        from google.genai import types
        contents = []

        if isinstance(images_base64, list) and len(images_base64) > 0:
            for img_str in images_base64:
                img_str = img_str.strip()
                if not img_str: continue
                if ',' in img_str:
                    header, encoded = img_str.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                else:
                    encoded = img_str
                    mime_type = "image/png"
                img_data = base64.b64decode(encoded)
                contents.append(types.Part.from_bytes(data=img_data, mime_type=mime_type))
        elif image_base64:
            if ',' in image_base64:
                header, encoded = image_base64.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
            else:
                encoded = image_base64
                mime_type = "image/png"
            img_data = base64.b64decode(encoded)
            contents.append(types.Part.from_bytes(data=img_data, mime_type=mime_type))
            
        contents.append(prompt)

        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "needs_clarification": {"type": "BOOLEAN"},
                    "question": {"type": "STRING"},
                    "thinking": {"type": "STRING"},
                    "explanation": {"type": "STRING"},
                    "html": {"type": "STRING"},
                    "css": {"type": "STRING"},
                    "js": {"type": "STRING"}
                },
                "required": ["needs_clarification", "question", "thinking", "explanation", "html", "css", "js"]
            }
        )
        
        import time
        import re
        models_to_try = get_gemini_models_to_try()
        response = None
        last_err = None

        for model in models_to_try:
            for attempt in range(2):
                try:
                    print(f"[Chat AI] Calling model {model} (Attempt {attempt+1})...")
                    response = client.models.generate_content(
                        model=model, 
                        contents=contents,
                        config=gen_config
                    )
                    break
                except Exception as e:
                    last_err = e
                    err_str = str(e)
                    if client_2 and ('429' in err_str or '400' in err_str or 'invalid' in err_str.lower() or 'quota' in err_str.lower() or 'exhausted' in err_str.lower() or 'limit' in err_str.lower()):
                        print(f"[Chat AI] Primary API Key error ({err_str[:80]}). Switching to Fallback API Key...")
                        client = client_2
                        client_2 = None
                        try:
                            response = client.models.generate_content(
                                model=model,
                                contents=contents,
                                config=gen_config
                            )
                            break
                        except Exception as fallback_e:
                            last_err = fallback_e
                            err_str = str(fallback_e)
                    
                    if '429' in err_str and 'RESOURCE_EXHAUSTED' in err_str and attempt < 1:
                        match = re.search(r'retry in (\d+\.\d+|\d+)s', err_str)
                        wait_time = float(match.group(1)) + 1 if match else 5.0
                        if wait_time <= 15:
                            print(f"[Chat AI] Rate limit hit. Waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                        else:
                            print(f"[Chat AI] Retry wait too long ({wait_time}s). Trying next fallback model...")
                            break
                    else:
                        print(f"[Chat AI] Model {model} failed: {err_str[:120]}. Trying next model...")
                        break
            if response and response.text:
                break

        if not response or not response.text:
            raise last_err or Exception("All Gemini models failed. Please verify your API Key and limits.")
        text = response.text.strip()

        import json as _json
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif text.startswith('```'):
            text = text.split('```')[1].split('```')[0].strip()

        result = _json.loads(text)
        
        needs_clarification = result.get('needs_clarification', False)
        if needs_clarification:
            return jsonify({
                'success': True,
                'reply': result.get('question', 'Xin lỗi, tôi chưa rõ ý bạn. Bạn có thể giải thích thêm hoặc chỉ rõ tên class/thẻ HTML cần sửa không?'),
                'css_updated': False
            })

        new_html = result.get('html', '').strip()
        new_css = result.get('css', '').strip()
        new_js = result.get('js', '').strip()
        explanation = result.get('explanation', 'Đã cập nhật.')

        updated = False

        if new_html and os.path.exists(html_path):
            style_href = "../style.css" if folder else "style.css"
            if '<html' not in new_html.lower() and '<!doctype html>' not in new_html.lower():
                # Tự động bọc lại cấu trúc chuẩn nếu AI trả về thiếu
                new_html = (
                    f'<!DOCTYPE html>\n<html lang="vi">\n<head>\n'
                    f'    <meta charset="UTF-8">\n'
                    f'    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                    f'    <title>{menu_slug}</title>\n'
                    f'    <link rel="stylesheet" href="{style_href}">\n'
                    f'    <link rel="stylesheet" href="{menu_slug}.css">\n'
                    f'</head>\n<body>\n    {new_html}\n'
                    f'    <script src="{menu_slug}.js"></script>\n'
                    f'</body>\n</html>'
                )
            else:
                css_links = f'\n    <link rel="stylesheet" href="{style_href}">\n    <link rel="stylesheet" href="{menu_slug}.css">\n'
                if style_href not in new_html and f'{menu_slug}.css' not in new_html:
                    if '</head>' in new_html:
                        new_html = new_html.replace('</head>', css_links + '</head>')
                    elif '</HEAD>' in new_html:
                        new_html = new_html.replace('</HEAD>', css_links + '</HEAD>')
                js_script = f'\n    <script src="{menu_slug}.js"></script>\n'
                if f'{menu_slug}.js' not in new_html:
                    if '</body>' in new_html:
                        new_html = new_html.replace('</body>', js_script + '</body>')
                    elif '</BODY>' in new_html:
                        new_html = new_html.replace('</BODY>', js_script + '</BODY>')
            if os.path.exists(html_path):
                import shutil
                shutil.copyfile(html_path, html_path + '.bak')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(new_html)
            updated = True

        if new_css and os.path.exists(css_path):
            import shutil
            shutil.copyfile(css_path, css_path + '.bak')
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(new_css)
            updated = True

        if new_js or os.path.exists(js_path):
            import shutil
            if os.path.exists(js_path):
                shutil.copyfile(js_path, js_path + '.bak')
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(new_js)
            updated = True

        return jsonify({
            'success': True,
            'reply': explanation,
            'css_updated': updated
        })

    except Exception as e:
        print(f"[Chat AI] Error: {e}")
        return jsonify({
            'success': False,
            'reply': f'❌ Lỗi kết nối AI: {str(e)}'
        }), 500

@app.route('/api/rollback', methods=['POST'])
def api_rollback():
    data = request.json or {}
    site_id = data.get('site_id', '').strip()
    menu_param = data.get('menu_param', '').strip()

    if not site_id or not menu_param:
        return jsonify({'success': False, 'message': 'Thiếu tham số site_id hoặc menu_param.'}), 400

    folder, menu_slug = parse_folder_slug(menu_param)
    site_dir = os.path.join(OUTPUT_DIR, site_id)
    if folder:
        target_dir = os.path.join(site_dir, folder)
    else:
        target_dir = site_dir

    html_path = os.path.join(target_dir, f"{menu_slug}.html")
    css_path = os.path.join(target_dir, f"{menu_slug}.css")
    js_path = os.path.join(target_dir, f"{menu_slug}.js")
    html_bak = html_path + '.bak'
    css_bak = css_path + '.bak'
    js_bak = js_path + '.bak'

    restored_html = False
    restored_css = False
    restored_js = False
    import shutil

    if os.path.exists(html_bak):
        temp_path = html_path + '.temp'
        shutil.copyfile(html_path, temp_path)
        shutil.copyfile(html_bak, html_path)
        shutil.copyfile(temp_path, html_bak)
        os.remove(temp_path)
        restored_html = True

    if os.path.exists(css_bak):
        temp_path = css_path + '.temp'
        shutil.copyfile(css_path, temp_path)
        shutil.copyfile(css_bak, css_path)
        shutil.copyfile(temp_path, css_bak)
        os.remove(temp_path)
        restored_css = True

    if os.path.exists(js_bak):
        temp_path = js_path + '.temp'
        if os.path.exists(js_path):
            shutil.copyfile(js_path, temp_path)
        shutil.copyfile(js_bak, js_path)
        if os.path.exists(temp_path):
            shutil.copyfile(temp_path, js_bak)
            os.remove(temp_path)
        restored_js = True

    if restored_html or restored_css or restored_js:
        return jsonify({'success': True, 'message': 'Undo successful!'})
    else:
        return jsonify({'success': False, 'message': 'No backup found to undo.'})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    def ensure_playwright_browsers():
        import subprocess
        import sys
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"], 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Warning: Failed to ensure playwright browsers: {e}")
            
    print("Checking and installing Playwright browsers if necessary...")
    ensure_playwright_browsers()
    app.run(debug=True, port=5000)
