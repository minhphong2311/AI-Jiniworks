# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/generate.py
Blueprint xử lý chức năng Generate page từ Figma.
Bao gồm: Figma utilities, AI visual refinement, và async generation task management.
"""
import os
import json
import threading

from flask import Blueprint, request, jsonify
from .helpers import (
    load_data, save_data, get_config,
    parse_folder_slug, OUTPUT_DIR,
    get_css_guide_instruction,
    get_default_gemini_model,
    get_gemini_models_to_try
)

generate_bp = Blueprint('generate', __name__)

# Task state dictionary (task_id -> status dict)
GENERATE_TASKS = {}


# ---------------------------------------------------------------------------
# Figma utilities
# ---------------------------------------------------------------------------

def load_ai_templates():
    structure_template = ''
    form_template = ''
    try:
        import os
        base = os.path.dirname(os.path.dirname(__file__))
        structure_path = os.path.join(base, 'assets', 'ai_prompts', 'structure-template.html')
        form_path = os.path.join(base, 'assets', 'ai_prompts', 'form-template.html')
        
        if os.path.exists(structure_path):
            with open(structure_path, 'r', encoding='utf-8') as f:
                structure_template = f.read()
        if os.path.exists(form_path):
            with open(form_path, 'r', encoding='utf-8') as f:
                form_template = f.read()
    except Exception as e:
        print(f"Error loading templates: {e}")
    return structure_template, form_template



def get_unified_ai_rules(ai_hint="", css_links=None, conbox_hint="", menu_slug=""):
    structure_template, form_template = load_ai_templates()
    if css_links is not None:
        css_rules = get_css_guide_instruction(css_links)
    else:
        css_rules = get_css_guide_instruction()
        
    slug_placeholder = menu_slug if menu_slug else "{menu_slug}"
    rules = f'''
CRITICAL STRUCTURE RULES TO STRICTLY ENFORCE:
1. Do not use absolute positioning classes like `fg-*`. Use semantic Flex/Grid layout with margins and paddings.
2. CRITICAL STRUCTURE RULE: For normal pages, you MUST wrap the entire page content in `<div class="content-box">`. BUT for Form interfaces (any UI containing text inputs, textareas, selects, checkboxes, or registration fields), you MUST strictly follow `form-template.html` and NEVER use `.content-box` or `.con-box`.
3. For normal pages (inside `.content-box`), group related content into `<div class="con-box">` sections. The VERY LAST `<div class="con-box">` inside `.content-box` MUST have the class `no-pd`. {conbox_hint}
4. HEADING HIERARCHY RULE: Headings MUST strictly follow their wrappers: `.con-box > h4.h4-tit01`, `.con-box02 > h5.h5-tit01`, and `.con-box03 > h6.h6-tit01`. Do not use them outside of their corresponding wrapper.
5. CRITICAL CLASS NAMING: For normal pages, you MUST strictly use the exact class names from the structure template (e.g. `h4-tit01`, `h5-tit01`, `h6-tit01`, `con-p`). For Forms, you MUST strictly use the exact class names from form-template.html (e.g. `bn-write-common01`, `b-table-wrap`, `b-table-box`, `b-row-box`, `b-title-box`, `b-con-box`). For form elements, MUST use `b-input` (text), `b-select` (select), `b-input b-textarea` (textarea), `b-radio` (radio), `b-chk` (checkbox). DO NOT invent new classes.
6. CRITICAL IMAGE RULE: Regular images MUST be standard `<img>` tags (do NOT remove or truncate repeating elements in lists/cards). However, if an image is a small icon (like an arrow, plus, or more icon) inside a button (`<a>` or `<button>`), you MUST remove the `<img>` tag from HTML and implement it entirely via CSS (e.g., using `background-image` on the button or its `::after` pseudo-element). DO NOT leave button icons as `<img>` tags!
7. CRITICAL IMAGE PATH RULE: ALL image `src` paths MUST start with EXACTLY `./images/{slug_placeholder}/`. Do NOT invent folder names like `faculty` or `common`. For example, all images must be `./images/{slug_placeholder}/filename.png`.
8. NESTING RULE: Do NOT wrap `.con-box02` inside `.con-box` just for `.table-wrap`, `.mark-p`, or `.box-btn`. Put them directly inside `.con-box` alongside the `h4` heading. Do NOT use `.container-box` inside `.box-btn` or `.btn-box`; place the `<a>`/`<button>` tags directly inside it.
9. PADDING RULE: If there are multiple `<p class="con-p">` in a row, or if `<p class="con-p">` is immediately above a `.mark-p` or `.mark-p01`, the LAST `<p class="con-p">` MUST have the class `no-pd` (i.e. `<p class="con-p no-pd">`).
10. MARK-P SYMBOL RULE: You MUST ABSOLUTELY REMOVE the asterisk symbol `※` from the beginning of ANY text inside `<p class="mark-p">` and `<p class="mark-p01">`. Never output `※` inside these tags.
11. TABLE CAPTION RULE: For Table `<caption>`, you MUST include a `<strong>` tag before the `<span>`. The text inside `<strong>` MUST be exactly copied from the text of the heading tag (`h4`, `h5`, etc.) located immediately above the table (e.g., `<caption><strong>Heading Text</strong><span>...</span></caption>`).
12. LIST FORMATTING RULE: Do NOT use `<p>` tags with `<br>` to represent lists. If the text contains numbered items (e.g., 1., 2., 3.), you MUST convert it into an `<ol class="ol-type01">` with `<li>` tags. For bullet points (e.g., -, •), use `<ul class="ul-type-dot">` or `<ul class="ul-type-bar">` with `<li>` tags.
TEMPLATE RULES TO FOLLOW:
Structure template: 
```html
{structure_template}
```
Form template: 
```html
{form_template}
```

CSS RULES:
{css_rules}
'''
    if ai_hint:
        rules += f'''
USER AI HINT (CRITICAL INSTRUCTION): {ai_hint}
You MUST strictly follow this hint. IF the hint requires dynamic components (like Swiper, sliders, progress bars), you ARE FULLY ALLOWED to append `<script src='cdn...'>` or `<link>` CDN tags directly in the `html` string. HOWEVER, ALL inline custom Javascript initialization code MUST be placed exclusively in the `js` field, NOT inside `<script>` tags in the HTML.'''
        
    return rules


def parse_figma_url(url):
    try:
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        file_key = None
        if len(path_parts) >= 2:
            if path_parts[0] in ['design', 'file']:
                file_key = path_parts[1]

        queries = urlparse.parse_qs(parsed.query)
        node_id = queries.get('node-id', [None])[0]
        if node_id:
            node_id = node_id.replace('-', ':')
        return file_key, node_id
    except Exception:
        return None, None


def fetch_figma_node(file_key, node_id, token):
    # 1. Check local figma cache first
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'figma_cache.json')
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            cache_key = f"{file_key}:{node_id}"
            if cache_key in cache_data:
                print(f"[Figma] Loaded from cache: {cache_key}")
                return cache_data[cache_key]
        except Exception as e:
            print(f"[Figma] Cache error: {e}")

    # 2. Try network call
    if not token:
        print("[Figma] No token provided, skipping API call.")
        return None
    try:
        import requests
        headers = {'X-Figma-Token': token}
        url = f"https://api.figma.com/v1/files/{file_key}/nodes?ids={node_id}"
        print(f"[Figma] Fetching: {url}")
        r = requests.get(url, headers=headers, timeout=30)
        print(f"[Figma] Status code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # Save to cache
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                existing = {}
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                existing[f"{file_key}:{node_id}"] = data
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(existing, f, ensure_ascii=False)
            except Exception as ce:
                print(f"[Figma] Failed to save cache: {ce}")
            return data
        else:
            print(f"[Figma] API error: {r.status_code} - {r.text[:200]}")
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        print(f"[Figma] Request exception: {e}")
        return {"error": f"Exception: {str(e)}"}
    return None


def extract_used_image_refs(node, used_refs=None):
    if used_refs is None:
        used_refs = set()

    fills = node.get('fills', [])
    for fill in fills:
        if fill.get('type') == 'IMAGE' and 'imageRef' in fill:
            used_refs.add(fill['imageRef'])

    for child in node.get('children', []):
        extract_used_image_refs(child, used_refs)

    return used_refs


def fetch_figma_images(file_key, token):
    try:
        import requests
        headers = {'X-Figma-Token': token}
        url = f"https://api.figma.com/v1/files/{file_key}/images"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get('meta', {}).get('images', {})
    except Exception:
        pass
    return {}


def download_and_map_figma_images(image_map, target_dir, menu_slug, used_refs=None):
    if not image_map:
        return {}
    import urllib.request
    from concurrent.futures import ThreadPoolExecutor

    images_dir = os.path.join(target_dir, "images", menu_slug)
    os.makedirs(images_dir, exist_ok=True)

    map_file = os.path.join(images_dir, '.image_refs.json')
    ref_to_filename = {}
    if os.path.exists(map_file):
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                ref_to_filename = json.load(f)
        except Exception:
            pass

    max_idx = 0
    for fname in ref_to_filename.values():
        base = fname.rsplit('.', 1)[0]
        if '-' in base:
            idx_str = base.split('-')[-1]
            if idx_str.isdigit():
                max_idx = max(max_idx, int(idx_str))

    local_image_map = {}
    tasks = []

    for ref, url in image_map.items():
        if used_refs is not None and ref not in used_refs:
            continue
        if url:
            if ref in ref_to_filename:
                filename = ref_to_filename[ref]
            else:
                max_idx += 1
                filename = f"{menu_slug}-{max_idx:02d}.jpg"
                ref_to_filename[ref] = filename
            local_image_map[ref] = f"./images/{menu_slug}/{filename}"
            tasks.append((ref, url, os.path.join(images_dir, filename)))

    def _fetch_one(item):
        r, u, lp = item
        if not os.path.exists(lp):
            try:
                req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    with open(lp, 'wb') as f:
                        f.write(response.read())
            except Exception as e:
                print(f"Failed to download image {r}: {e}")

    if tasks:
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(_fetch_one, tasks))

    try:
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(ref_to_filename, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save image ref map: {e}")

    return local_image_map


def export_figma_icons(file_key, document, token, target_dir, menu_slug):
    """Export icon nodes from Figma as PNG files.
    Smart filtering ensures only real icons are exported, avoiding tiny layout shapes, lines, or table borders."""
    import requests
    import urllib.request
    import hashlib
    import re
    from concurrent.futures import ThreadPoolExecutor

    seen_ids = set()
    icon_nodes = []  # list of (node_id, clean_name)

    def has_text(x):
        return x.get('type') == 'TEXT' or any(has_text(c) for c in x.get('children', []))

    def is_real_icon(node):
        t = node.get('type', '')
        bb = node.get('absoluteBoundingBox', {})
        w, h = bb.get('width', 0), bb.get('height', 0)
        name = node.get('name', '').lower()

        # Loại bỏ các hình học CSS cơ bản và layout thuần túy
        if t in ('TEXT', 'DOCUMENT', 'CANVAS', 'PAGE', 'SECTION', 'LINE', 'RECTANGLE', 'ELLIPSE'):
            return False
        # Kích thước icon chuẩn từ 10px đến 80px
        if w < 10 or h < 10 or w > 80 or h > 80:
            return False
        # Loại bỏ các thanh divider / kẻ dọc quá dẹt
        ratio = max(w, h) / max(min(w, h), 0.1)
        if ratio > 2.5:
            return False
        if has_text(node):
            return False
        if any(f.get('type') == 'IMAGE' for f in node.get('fills', [])):
            return False

        # Icon chuẩn: Component, Instance, Vector, Boolean, hoặc Frame có tên biểu thị icon
        if t in ('INSTANCE', 'COMPONENT', 'COMPONENT_SET', 'VECTOR', 'BOOLEAN_OPERATION'):
            return True
        if any(k in name for k in ['icon', 'ic_', 'ico', 'svg', 'arrow', 'home', 'btn', 'logo', 'glyph']):
            return True
        # Nếu là Frame/Group, chỉ nhận nếu có vector con trực tiếp bên trong
        children = node.get('children', [])
        if children and any(c.get('type') in ('VECTOR', 'BOOLEAN_OPERATION') for c in children):
            return True
        return False

    MAX_ICONS = 30

    def find_icon_nodes(node):
        if len(icon_nodes) >= MAX_ICONS:
            return
        node_id = node.get('id', '')
        if node_id and node_id not in seen_ids:
            if is_real_icon(node):
                clean_name = "".join([c.lower() if c.isalnum() else '-' for c in node.get('name', '')])
                clean_name = re.sub(r'-+', '-', clean_name).strip('-')
                if not clean_name or clean_name in ['group', 'frame', 'vector', 'image', 'icon', 'rectangle', 'ellipse', 'star', 'line', 'polygon']:
                    clean_name = menu_slug
                seen_ids.add(node_id)
                icon_nodes.append((node_id, clean_name))
                return  # Đã nhận là 1 icon thì không bóc tách các sub-vectors li ti bên trong!

        for child in node.get('children', []):
            find_icon_nodes(child)

    find_icon_nodes(document)

    icon_map = {}
    if not icon_nodes:
        return icon_map

    print(f"[Figma] Exporting {len(icon_nodes)} real icon nodes as PNG...")
    headers = {'X-Figma-Token': token}
    images_dir = os.path.join(target_dir, "images", menu_slug)
    os.makedirs(images_dir, exist_ok=True)

    content_hash_to_filename = {}

    batch_size = 100
    for batch_start in range(0, len(icon_nodes), batch_size):
        batch = icon_nodes[batch_start:batch_start + batch_size]
        ids_str = ",".join(nid for nid, _ in batch)
        url = f"https://api.figma.com/v1/images/{file_key}?ids={ids_str}&format=png&scale=2"
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code != 200:
                print(f"[Figma] Icon export API error: {r.status_code} {r.text[:200]}")
                continue
            images_resp = r.json().get('images', {})
            
            download_items = []
            for node_id, clean_name in batch:
                img_url = images_resp.get(node_id)
                if img_url:
                    download_items.append((node_id, clean_name, img_url))

            def _download_icon(item):
                nid, cname, u = item
                try:
                    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = resp.read()
                    return (nid, cname, data)
                except Exception as e:
                    print(f"[Figma] Failed to download icon {cname}: {e}")
                    return (nid, cname, None)

            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(_download_icon, download_items))

            for nid, cname, img_bytes in results:
                if not img_bytes:
                    continue
                img_hash = hashlib.md5(img_bytes).hexdigest()
                if img_hash in content_hash_to_filename:
                    final_name = content_hash_to_filename[img_hash]
                else:
                    existing_count = sum(1 for fn in content_hash_to_filename.values() if fn.startswith(cname))
                    final_name = f"{cname}-{existing_count + 1:02d}.png"
                    local_path = os.path.join(images_dir, final_name)
                    with open(local_path, 'wb') as f:
                        f.write(img_bytes)
                    content_hash_to_filename[img_hash] = final_name
                    print(f"[Figma] Saved icon: {final_name}")
                icon_map[nid] = f"./images/{menu_slug}/{final_name}"
        except Exception as e:
            print(f"[Figma] Failed to export icons batch: {e}")

    return icon_map



def parse_figma_fill(fills, image_map=None):
    if not fills:
        return None, "transparent"

    for fill in reversed(fills):
        if not fill.get('visible', True):
            continue
        if fill.get('type') == 'IMAGE':
            ref = fill.get('imageRef')
            url = image_map.get(ref) if image_map else None
            if url:
                return "image", f"url('{url}')"
            return "image", f"url('http://localhost:3845/assets/{ref}.png')"

    for fill in reversed(fills):
        if not fill.get('visible', True):
            continue
        if fill.get('type') in ['GRADIENT_LINEAR', 'GRADIENT_RADIAL']:
            stops = fill.get('gradientStops', [])
            stop_strs = []
            for stop in stops:
                color = stop.get('color', {})
                r = int(color.get('r', 0) * 255)
                g = int(color.get('g', 0) * 255)
                b = int(color.get('b', 0) * 255)
                a = color.get('a', 1.0)
                pos = int(stop.get('position', 0) * 100)
                stop_strs.append(f"rgba({r}, {g}, {b}, {a}) {pos}%")
            if stop_strs:
                return "gradient", f"linear-gradient(90deg, {', '.join(stop_strs)})"

    for fill in reversed(fills):
        if not fill.get('visible', True):
            continue
        if fill.get('type') == 'SOLID':
            color = fill.get('color', {})
            r = int(color.get('r', 0) * 255)
            g = int(color.get('g', 0) * 255)
            b = int(color.get('b', 0) * 255)
            a = fill.get('opacity', color.get('a', 1.0))
            return "solid", f"rgba({r}, {g}, {b}, {a})"

    return None, "transparent"


def strip_inline_styles(html_content, css_content):
    """Move all inline style attributes from HTML into the CSS file."""
    import re
    extra_css_rules = []
    counter = [0]

    pattern = re.compile(
        r'(<\w+\s)'
        r'(?:[^>]*?\s)?'
        r'style=["\']([^"\']*)["\']'
        r'([^>]*)'
        r'(?=>)',
        re.DOTALL
    )

    def replacer(m):
        full = m.group(0)
        style_val = m.group(2).strip().rstrip(';')
        if not style_val:
            return full.replace(m.group(0), full[:full.index('style=')] + full[full.index('>', full.index('style=')):]).strip()

        counter[0] += 1
        new_class = f'is-{counter[0]}'
        extra_css_rules.append(f'.{new_class} {{ {style_val}; }}')

        tag_no_style = re.sub(r'\s*style=["\'][^"\']*["\']', '', full)
        class_m = re.search(r'class=["\']([^"\']*)["\']', tag_no_style)
        if class_m:
            new_tag = tag_no_style[:class_m.start()] + f'class="{class_m.group(1).strip()} {new_class}"' + tag_no_style[class_m.end():]
        else:
            new_tag = re.sub(r'^(<\w+)', rf'\1 class="{new_class}"', tag_no_style)
        return new_tag

    new_html = pattern.sub(replacer, html_content)

    if extra_css_rules:
        css_content = css_content + '\n' + '\n'.join(extra_css_rules)

    return new_html, css_content


def compile_figma_node_to_html_css(design_data, node_id, image_map=None):
    html_snippets = []
    css_rules = []

    nodes = design_data.get('nodes', {}) if isinstance(design_data, dict) else {}
    target_node = (
        nodes.get(node_id) or
        nodes.get(node_id.replace(':', '-')) or
        nodes.get(node_id.replace('-', ':')) or
        (list(nodes.values())[0] if isinstance(nodes, dict) and nodes else {})
    )
    if isinstance(target_node, dict):
        document = target_node.get('document', {})
    else:
        document = {}

    if not document and isinstance(design_data, dict) and 'document' in design_data:
        document = design_data['document']

    if not document:
        return None

    def clean_class_name(nid):
        return "fg-" + nid.replace(':', '-').replace(';', '-')

    def compile_node(node, parent=None, is_root=False):
        nid = node.get('id', '')
        ntype = node.get('type', '')
        name = node.get('name', '')
        class_name = clean_class_name(nid)

        styles = []

        box = node.get('absoluteBoundingBox', {})
        width = box.get('width')
        height = box.get('height')

        styles.append("box-sizing: border-box;")

        # Corner radius & borders
        if 'cornerRadius' in node:
            styles.append(f"border-radius: {node['cornerRadius']}px;")
        if node.get('strokes'):
            _, border_color = parse_figma_fill(node.get('strokes'), image_map)

            indiv_strokes = node.get('individualStrokeWeights')
            if indiv_strokes:
                top = indiv_strokes.get('top', 0)
                right = indiv_strokes.get('right', 0)
                bottom = indiv_strokes.get('bottom', 0)
                left = indiv_strokes.get('left', 0)
                if top > 0:
                    styles.append(f"border-top: {top}px solid {border_color};")
                if right > 0:
                    styles.append(f"border-right: {right}px solid {border_color};")
                if bottom > 0:
                    styles.append(f"border-bottom: {bottom}px solid {border_color};")
                if left > 0:
                    styles.append(f"border-left: {left}px solid {border_color};")
            elif 'strokeWeight' in node and node['strokeWeight'] > 0:
                styles.append(f"border: {node['strokeWeight']}px solid {border_color};")

        # Background color or fill (skip for TEXT)
        if ntype != 'TEXT':
            fill_type, fill_val = parse_figma_fill(node.get('fills'), image_map)
            if fill_type == 'image':
                styles.append(f"background-image: {fill_val};")
                styles.append("background-size: cover;")
                styles.append("background-position: center;")
            elif fill_type == 'gradient':
                styles.append(f"background: {fill_val};")
            elif fill_val != "transparent":
                styles.append(f"background-color: {fill_val};")

        if is_root:
            styles.append("margin: 0 auto;")
            styles.append("position: relative;")
            if width and height:
                styles.append(f"width: {width}px; height: {height}px;")
            else:
                styles.append("width: 100%; min-height: 100vh;")

        # Positioning & Layout
        parent_has_layout = False
        if parent:
            parent_has_layout = bool(parent.get('layoutMode') and parent.get('layoutMode') != 'NONE')

        is_absolute = False
        if not is_root:
            if not parent_has_layout or node.get('layoutPositioning') == 'ABSOLUTE':
                is_absolute = True

        if is_absolute:
            if parent:
                parent_box = parent.get('absoluteBoundingBox', {})
                px = parent_box.get('x', 0)
                py = parent_box.get('y', 0)
                cx = box.get('x', 0)
                cy = box.get('y', 0)
                styles.append("position: absolute;")
                styles.append(f"left: {cx - px}px;")
                styles.append(f"top: {cy - py}px;")

        # Flexbox child properties & Sizing
        if not is_absolute and parent_has_layout and not is_root:
            parent_mode = parent.get('layoutMode')
            hz_sizing = node.get('layoutSizingHorizontal')
            vt_sizing = node.get('layoutSizingVertical')

            if not hz_sizing:
                if parent_mode == 'HORIZONTAL' and node.get('layoutGrow') == 1:
                    hz_sizing = 'FILL'
                elif parent_mode == 'VERTICAL' and node.get('layoutAlign') == 'STRETCH':
                    hz_sizing = 'FILL'
                else:
                    hz_sizing = 'FIXED'

            if not vt_sizing:
                if parent_mode == 'VERTICAL' and node.get('layoutGrow') == 1:
                    vt_sizing = 'FILL'
                elif parent_mode == 'HORIZONTAL' and node.get('layoutAlign') == 'STRETCH':
                    vt_sizing = 'FILL'
                else:
                    vt_sizing = 'FIXED'

            if parent_mode == 'HORIZONTAL':
                if hz_sizing == 'FILL':
                    styles.append("flex-grow: 1;")
                if vt_sizing == 'FILL':
                    styles.append("align-self: stretch;")
            elif parent_mode == 'VERTICAL':
                if vt_sizing == 'FILL':
                    styles.append("flex-grow: 1;")
                if hz_sizing == 'FILL':
                    styles.append("align-self: stretch;")

            if hz_sizing == 'FIXED' and width is not None:
                styles.append(f"width: {width}px;")
            elif hz_sizing == 'HUG':
                styles.append("width: fit-content;")

            if vt_sizing == 'FIXED' and height is not None:
                styles.append(f"height: {height}px;")
            elif vt_sizing == 'HUG':
                styles.append("height: fit-content;")
        elif not is_root:
            if width is not None:
                styles.append(f"width: {width}px;")
            if height is not None:
                styles.append(f"height: {height}px;")

        if ntype == 'TEXT':
            char_text = node.get('characters', '')
            text_style = node.get('style', {})
            font_family = text_style.get('fontFamily', 'Pretendard')
            font_size = text_style.get('fontSize', 16)
            font_weight = text_style.get('fontWeight', 400)
            line_height = text_style.get('lineHeightPx')
            align_h = text_style.get('textAlignHorizontal', 'LEFT').lower()

            styles.append(f"font-family: '{font_family}', sans-serif;")
            styles.append(f"font-size: {font_size}px;")
            styles.append(f"font-weight: {font_weight};")
            if line_height:
                styles.append(f"line-height: {line_height}px;")
            if align_h in ['center', 'right', 'justify']:
                styles.append(f"text-align: {align_h};")

            _, text_color = parse_figma_fill(node.get('fills'), image_map)
            if text_color != "transparent":
                styles.append(f"color: {text_color};")

            css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")

            tag = "p"
            cls_name = "con-p"
            if font_size >= 28:
                tag = "h4"
                cls_name = "h4-tit01"
            elif font_size >= 22:
                tag = "h5"
                cls_name = "h5-tit01"
            elif font_size >= 18:
                tag = "h6"
                cls_name = "h6-tit01"

            import html
            safe_text = html.escape(char_text).replace('\n', '<br>')
            return f"<{tag} class='{cls_name} {class_name}'>{safe_text}</{tag}>\n"

        elif ntype in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE']:
            layout_mode = node.get('layoutMode', 'NONE')
            if layout_mode and layout_mode != 'NONE':
                styles.append("display: flex;")
                if layout_mode == 'VERTICAL':
                    styles.append("flex-direction: column;")
                else:
                    styles.append("flex-direction: row;")

                if node.get('layoutWrap') == 'WRAP':
                    styles.append("flex-wrap: wrap;")

                item_spacing = node.get('itemSpacing')
                if item_spacing:
                    styles.append(f"gap: {item_spacing}px;")

                pt = node.get('paddingTop', 0)
                pr = node.get('paddingRight', 0)
                pb = node.get('paddingBottom', 0)
                pl = node.get('paddingLeft', 0)
                if pt or pr or pb or pl:
                    styles.append(f"padding: {pt}px {pr}px {pb}px {pl}px;")

                align_items = node.get('counterAxisAlignItems')
                justify_content = node.get('primaryAxisAlignItems')

                align_map = {'MIN': 'flex-start', 'CENTER': 'center', 'MAX': 'flex-end'}
                justify_map = {'MIN': 'flex-start', 'CENTER': 'center', 'MAX': 'flex-end', 'SPACE_BETWEEN': 'space-between'}

                if align_items in align_map:
                    styles.append(f"align-items: {align_map[align_items]};")
                if justify_content in justify_map:
                    styles.append(f"justify-content: {justify_map[justify_content]};")
            else:
                if not is_absolute and parent_has_layout:
                    styles.append("position: relative;")
                elif is_root:
                    styles.append("position: relative;")

            # If this node is mapped to an image/icon, output an img tag
            if nid in (image_map or {}):
                img_src = image_map[nid]
                css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")
                return f"<img class='{class_name}' src='{img_src}' alt='{name}'>\n"

            css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")

            children_html = ""
            for child in node.get('children', []):
                children_html += compile_node(child, parent=node)

            wrapper_cls = class_name
            if is_root:
                wrapper_cls = f"content-box {class_name}"
            elif parent and parent.get('is_root'):
                wrapper_cls = f"con-box {class_name}"

            return f"<div class='{wrapper_cls}'>\n{children_html}</div>\n"

        else:
            styles.append("display: block;")
            if width and (is_absolute or not parent_has_layout or node.get('layoutAlign') != 'STRETCH'):
                styles.append(f"width: {width}px;")
            if height and (is_absolute or not parent_has_layout):
                styles.append(f"height: {height}px;")
            if ntype == 'ELLIPSE':
                styles.append("border-radius: 50%;")
            css_rules.append(f".{class_name} {{ { ' '.join(styles) } }}")
            return f"<div class='{class_name}'></div>\n"

    raw_html = compile_node(document, is_root=True)
    if 'content-box' not in raw_html:
        html_result = f'<div class="content-box">\n<div class="con-box">\n{raw_html}\n</div>\n</div>'
    else:
        html_result = raw_html

    default_responsive_css = """
.content-box { box-sizing: border-box; width: 100%; max-width: 1096px; margin: 0 auto; padding: 0 20px; position: relative; }
@media screen and (max-width: 1024px) {
    .content-box { padding: 0 20px; }
}
@media screen and (max-width: 768px) {
    .content-box { padding: 0 16px; }
}
"""
    css_result = "\n".join(css_rules) + "\n" + default_responsive_css
    return html_result, css_result


# ---------------------------------------------------------------------------
# AI refinement helpers
# ---------------------------------------------------------------------------

def apply_dynamic_css_feedback(css_content, feedback, figma_json=None):
    config = get_config()
    api_key = config.get('gemini_api_key', '').strip()

    if not api_key:
        print("No Gemini API key configured. Using fallback regex.")
        import re
        pattern = r'([.#\w\-]+)\s+([\w\-]+)\s*:\s*([^;]+)'
        matches = re.findall(pattern, feedback)
        for selector, prop, val in matches:
            selector = selector.strip()
            prop = prop.strip()
            val = val.strip().rstrip(';')

            escaped_selector = re.escape(selector)
            block_pattern = rf'({escaped_selector}\s*\{{[^}}]*\}})'
            block_match = re.search(block_pattern, css_content, re.IGNORECASE)
            if block_match:
                original_block = block_match.group(1)
                prop_pattern = rf'({re.escape(prop)}\s*:\s*[^;}}]+;?)'
                if re.search(prop_pattern, original_block, re.IGNORECASE):
                    new_block = re.sub(prop_pattern, f'{prop}: {val};', original_block, flags=re.IGNORECASE)
                    css_content = css_content.replace(original_block, new_block)
                else:
                    new_block = original_block.replace('}', f'\n    {prop}: {val};\n}}')
                    css_content = css_content.replace(original_block, new_block)
            else:
                css_content += f"\n{selector} {{\n    {prop}: {val};\n}}\n"
        return css_content

    # Use Gemini API
    try:
        from google import genai as _genai
        client = _genai.Client(api_key=api_key)

        figma_context = ""
        if figma_json:
            def simplify_node(node):
                if not isinstance(node, dict):
                    return node
                result = {
                    "n": node.get("name"),
                    "t": node.get("type")
                }
                for key in ['layoutMode', 'layoutSizingHorizontal', 'layoutSizingVertical', 'layoutAlign', 'layoutGrow', 'characters']:
                    if key in node:
                        result[key] = node[key]
                if 'absoluteBoundingBox' in node:
                    result['box'] = node['absoluteBoundingBox']
                if 'children' in node:
                    result['c'] = [simplify_node(c) for c in node['children']]
                return result

            simplified = simplify_node(figma_json.get("document", figma_json))
            json_str = json.dumps(simplified, ensure_ascii=False)
            if len(json_str) > 50000:
                json_str = json_str[:50000] + "...(truncated)"
            figma_context = f"\nHere is the original Figma JSON structure (simplified layout tree):\n```json\n{json_str}\n```\n"

        unified_rules = get_unified_ai_rules(feedback)
        prompt = f"""
You are an expert frontend developer.
The user has provided a natural language request to modify some CSS.
User Request: {feedback}

{figma_context}

{unified_rules}

Here is the current CSS:
```css
{css_content}
```

Return ONLY the full updated CSS code. Make sure you apply the requested changes intelligently.
If the user complains that it doesn't look like the design, rely on your frontend expertise to tweak margins, paddings, fonts, or colors to make it look professional and beautiful.
Do not wrap it in markdown block if it causes extra characters, but if you do, I will strip them. Just return valid CSS.
"""
        models_to_try = get_gemini_models_to_try(['gemini-3.1-flash-lite', 'gemini-2.0-flash-lite'])
        text = None
        for model in models_to_try:
            try:
                print(f"[Gemini] Trying CSS feedback with model {model}...")
                response = client.models.generate_content(model=model, contents=prompt)
                if response and response.text:
                    text = response.text.strip()
                    break
            except Exception as e:
                print(f"[Gemini] CSS feedback model {model} error: {e}")
                import time
                time.sleep(2)

        if not text:
            print("Gemini API call failed for all models.")
            return css_content

        if text.startswith('```css'):
            text = text[6:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]

        return text.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return css_content


def apply_structural_templates(html, css, js, api_key, menu_name, task_id=None, ai_hint=""):
    print(f"[{menu_name}] --- Structural Refinement Start ---")
    import os
    import json

    structure_template, form_template = load_ai_templates()

    unified_rules = get_unified_ai_rules(ai_hint, menu_slug=menu_name)
    prompt = f"""Bạn là một chuyên gia Frontend Developer.
Nhiệm vụ của bạn là tái cấu trúc lại đoạn HTML/CSS thô được sinh ra từ Figma (tọa độ absolute) thành một layout chuẩn semantic, responsive, sử dụng Flexbox/Grid, và phải TUYỆT ĐỐI tuân thủ cấu trúc của dự án.

Nội dung HTML thô hiện tại:
```html
{html}
```

Nội dung CSS thô hiện tại:
```css
{css}
```

{unified_rules}

Nhiệm vụ:
1. Áp dụng tất cả các quy tắc cấu trúc và CSS (CRITICAL STRUCTURE RULES) ở trên vào code thô hiện tại.
2. Sắp xếp lại các phần tử HTML sao cho có hệ thống phân cấp rõ ràng.
3. Xóa bỏ tuyệt đối các class `fg-*` mang tính position absolute, và thay bằng Flexbox/Grid chuẩn.
4. Trả về JSON chứa HTML và CSS mới.

Trả lời theo định dạng JSON sau (không thêm gì ngoài JSON, không bọc trong markdown):
{{
  "html": "toàn bộ nội dung HTML mới",
  "css": "toàn bộ nội dung CSS mới",
  "js": "toàn bộ nội dung JS mới (không chứa thẻ <script>)",
  "rename_map": [
    {{"old_name": "test-01.png", "new_name": "quick-link-01.png"}}
  ]
}}"""

    try:
        from google import genai as _genai
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.json')
        api_key_2 = ""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    api_key_2 = cfg.get('gemini_api_key_2', '').strip()
            except: pass
            
        client = _genai.Client(api_key=api_key)
        client_2 = _genai.Client(api_key=api_key_2) if api_key_2 else None
        
        models_to_try = get_gemini_models_to_try()
        text = None
        result = None
        for model in models_to_try:
            for attempt in range(2): # Try 2 times per model
                try:
                    print(f"[{menu_name}] Trying Structural Model {model} (Attempt {attempt+1})...")
                    try:
                        response = client.models.generate_content(model=model, contents=prompt)
                    except Exception as ce:
                        if client_2 and ('429' in str(ce) or '400' in str(ce) or 'invalid' in str(ce).lower() or 'quota' in str(ce).lower() or 'exhausted' in str(ce).lower() or 'limit' in str(ce).lower()):
                            print(f"[{menu_name}] Primary API Key limit reached! Switching to Fallback Key...")
                            client = client_2
                            client_2 = None
                            response = client.models.generate_content(model=model, contents=prompt)
                        else:
                            raise ce
                    
                    if task_id and GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled':
                        raise Exception("CANCELLED_BY_USER")
                    
                    if response and response.text:
                        raw_text = response.text.strip()
                        if '```json' in raw_text:
                            raw_text = raw_text.split('```json')[1].split('```')[0].strip()
                        elif raw_text.startswith('```'):
                            raw_text = raw_text.split('```')[1].split('```')[0].strip()
                        
                        try:
                            import json_repair
                            result = json_repair.loads(raw_text)
                            text = raw_text
                            break # Valid JSON, break attempt loop
                        except Exception as je:
                            print(f"[{menu_name}] JSON Decode Error on {model}: {je}")
                            import time
                            time.sleep(1)
                            continue # Try again
                except Exception as e:
                    if str(e) == "CANCELLED_BY_USER":
                        raise e
                    print(f"[{menu_name}] Model {model} error: {e}")
                    import time
                    time.sleep(1)
            
            if result:
                break # Valid result found, break model loop
                
        if result:
            
            new_html = result.get('html', html)
            new_css = result.get('css', css)
            new_js = result.get('js', js)
            rename_map = result.get('rename_map', [])
            print(f"[{menu_name}] Structural Refinement SUCCESS!")
            return new_html, new_css, new_js, rename_map

    except Exception as e:
        print(f"[{menu_name}] Structural Refinement Error: {e}")
        
    return html, css, js, []


def compare_and_fix_visuals(token, figma_link, html, css, js, css_links, menu_name, gemini_api_key, task_id=None, local_image_path=None, local_image_paths=None):
    import urllib.parse
    import requests
    import asyncio
    from playwright.async_api import async_playwright
    from google import genai
    import PIL.Image
    import threading

    # Thêm Semaphore để giới hạn chỉ 1 request Gemini được chạy tại 1 thời điểm
    if not hasattr(compare_and_fix_visuals, 'api_lock'):
        compare_and_fix_visuals.api_lock = threading.Semaphore(1)

    structure_template, form_template = load_ai_templates()
    quality_checklist = ''
    try:
        base = os.path.dirname(os.path.dirname(__file__))
        checklist_path = os.path.join(base, 'assets', 'ai_prompts', 'quality_checklist.txt')
        

        if os.path.exists(checklist_path):
            with open(checklist_path, 'r', encoding='utf-8') as f:
                quality_checklist = f.read()
    except Exception as e:
        print(f"Error loading templates in compare_and_fix_visuals: {e}")

    print(f"[{menu_name}] --- Visual Reflection Start ---")
    base_dir = os.path.dirname(os.path.dirname(__file__))
    scratch_dir = os.path.join(base_dir, 'scratch')
    os.makedirs(scratch_dir, exist_ok=True)

    target_img_path = os.path.join(scratch_dir, f'temp_target_{menu_name}.png')
    render_img_path = os.path.join(scratch_dir, f'temp_render_{menu_name}.png')
    temp_html_path = os.path.join(scratch_dir, f'temp_render_{menu_name}.html')

    img_paths_to_stitch = local_image_paths or ([local_image_path] if local_image_path else [])
    
    if img_paths_to_stitch:
        if len(img_paths_to_stitch) == 1:
            import shutil
            shutil.copy(img_paths_to_stitch[0], target_img_path)
        else:
            import PIL.Image
            images = []
            for p in img_paths_to_stitch:
                try:
                    images.append(PIL.Image.open(p))
                except Exception as e:
                    print(f"[{menu_name}] Error opening image {p}: {e}")
            
            if images:
                widths, heights = zip(*(i.size for i in images))
                total_width = max(widths)
                total_height = sum(heights)
                
                new_im = PIL.Image.new('RGB', (total_width, total_height), (255, 255, 255))
                y_offset = 0
                for im in images:
                    new_im.paste(im, (0, y_offset))
                    y_offset += im.size[1]
                    
                new_im.save(target_img_path)
            else:
                return html, css, js
    else:
        try:
            file_key, node_id = parse_figma_url(figma_link)
            if not file_key or not node_id:
                print(f"[{menu_name}] Error parsing figma link: {figma_link}")
                if task_id and task_id in GENERATE_TASKS:
                    GENERATE_TASKS[task_id]['message'] = "Cảnh báo: URL Figma không hợp lệ. Vẫn tiếp tục kiểm tra AI."
            else:
                url = f'https://api.figma.com/v1/images/{file_key}?ids={node_id}&format=png&scale=1'
                headers = {'X-Figma-Token': token}
                r = requests.get(url, headers=headers)
                if r.status_code != 200:
                    print(f"[{menu_name}] Error fetching Figma image: {r.status_code}")
                    if os.path.exists(target_img_path):
                        print(f"[{menu_name}] Using cached image {target_img_path}")
                else:
                    data = r.json()
                    if 'err' in data and data['err']:
                        print(f"[{menu_name}] Figma Image Error: {data['err']}")
                        if os.path.exists(target_img_path):
                            print(f"[{menu_name}] Using cached image {target_img_path}")
                    else:
                        img_url = data['images'].get(node_id)
                        if not img_url:
                            print(f"[{menu_name}] No image returned from Figma.")
                            if os.path.exists(target_img_path):
                                print(f"[{menu_name}] Using cached image {target_img_path}")
                        else:
                            with open(target_img_path, 'wb') as f:
                                f.write(requests.get(img_url).content)
        except Exception as e:
            print(f"[{menu_name}] Error fetching/parsing Figma image: {e}")
            if os.path.exists(target_img_path):
                print(f"[{menu_name}] Using cached image {target_img_path} after exception")

    target_pil = None
    try:
        if os.path.exists(target_img_path):
            target_pil = PIL.Image.open(target_img_path)
    except Exception as e:
        print(f"[{menu_name}] PIL Error: {e}")

    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.json')
    gemini_api_key_2 = ""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                gemini_api_key_2 = cfg.get('gemini_api_key_2', '').strip()
        except: pass

    client = genai.Client(api_key=gemini_api_key)
    client_2 = genai.Client(api_key=gemini_api_key_2) if gemini_api_key_2 else None
    MAX_ITERATIONS = 2
    for iteration in range(1, MAX_ITERATIONS + 1):
        if task_id and GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled':
            raise Exception("CANCELLED_BY_USER")
        if task_id and task_id in GENERATE_TASKS:
            GENERATE_TASKS[task_id]['message'] = f"AI Quality Check ({iteration}/{MAX_ITERATIONS})..."

        css_guide_tags = "".join([f'\n    <link rel="stylesheet" href="{link}">' for link in css_links])
        full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">{css_guide_tags}
    <link rel="stylesheet" href="style.css">
    <style>
        body {{ margin: 0; padding: 0; }}
        {css}
    </style>
</head>
<body>
    {html}
    <script>
        {js}
    </script>
</body>
</html>"""
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

        config = get_config()
        show_ui = bool(config.get('show_ui', True))
        headless_mode = not show_ui

        async def capture():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless_mode)
                page = await browser.new_page()
                file_url = 'file:///' + temp_html_path.replace('\\', '/')
                await page.goto(file_url)
                import asyncio as _asyncio
                await _asyncio.sleep(0.5)
                await page.screenshot(path=render_img_path, full_page=True)
                await browser.close()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(capture())
            loop.close()
        except Exception as e:
            print(f"[{menu_name}] Playwright Error: {e}")
            return html, css, js

        try:
            render_pil = PIL.Image.open(render_img_path)
        except Exception as e:
            print(f"[{menu_name}] PIL Error: {e}")
            return html, css, js

        print(f"[{menu_name}] Sending visual comparison to Gemini (Iteration {iteration})...")
        if target_pil:
            prompt_header = "Compare Image 1 (Figma design) vs Image 2 (HTML/CSS render). Find every visual difference."
        else:
            prompt_header = "Inspect this HTML/CSS render. Find every structural or visual issue."

        unified_rules = get_unified_ai_rules("", css_links, menu_slug=menu_name)

        prompt = f"""You are a strict Frontend QA Engineer. {prompt_header}

Your default assumption: the render is WRONG. Your job is to FIND differences, not confirm correctness.

Checklist (check every item):
{quality_checklist}

{unified_rules}

SPECIAL ATTENTION FOR DIAGRAMS/CHARTS:
- Connecting lines between boxes: use CSS ::before/::after pseudo-elements only.
- Background colors must match exactly.

Current HTML:
{html}

Current CSS:
{css}

Mandatory format:
ISSUES:
- [describe each visual/structural difference found, or write "None" if truly none]

STATUS: PERFECT
(only if ISSUES is "None" and you are 95%+ confident after checking all checklist items)

STATUS: NEEDS_FIX
```html
(corrected html)
```

```css
(corrected css)
```
"""

        try:
            if gemini_api_key == "DEMO_KEY":
                print(f"[{menu_name}] Using DEMO_KEY. Mocking AI response...")
                import time
                time.sleep(3)
                text = 'STATUS: NEEDS_FIX\n\n```html\n<div class="content-box"><div class="con-box"><h4 class="h4-tit01">Demo Title</h4><p class="con-p">Mock response.</p></div></div>\n```\n\n```css\n.content-box { padding: 20px; }\n```'
            else:
                with compare_and_fix_visuals.api_lock:
                    models_to_try = get_gemini_models_to_try(['gemini-2.0-flash-lite'])
                    text = None
                    last_error = None
                    for model in models_to_try:
                        for attempt in range(2):
                            try:
                                print(f"[{menu_name}] Trying Gemini model {model} (Attempt {attempt+1})...")
                                if task_id and task_id in GENERATE_TASKS:
                                    GENERATE_TASKS[task_id]['message'] = f"AI Quality Check ({iteration}/{MAX_ITERATIONS}) - Analyzing..."
                                contents_to_send = [prompt]
                                if target_pil:
                                    contents_to_send.append(target_pil)
                                contents_to_send.append(render_pil)
                                
                                try:
                                    response = client.models.generate_content(
                                        model=model,
                                        contents=contents_to_send
                                    )
                                except Exception as ce:
                                    if client_2 and ('429' in str(ce) or '400' in str(ce) or 'invalid' in str(ce).lower() or 'quota' in str(ce).lower() or 'exhausted' in str(ce).lower() or 'limit' in str(ce).lower()):
                                        print(f"[{menu_name}] Primary API Key limit reached! Switching to Fallback Key...")
                                        client = client_2
                                        client_2 = None
                                        response = client.models.generate_content(
                                            model=model,
                                            contents=contents_to_send
                                        )
                                    else:
                                        raise ce
                                if response and response.text:
                                    text = response.text.strip()
                                    break
                            except Exception as e:
                                last_error = e
                                print(f"[{menu_name}] Model {model} error: {e}")
                                import time
                                time.sleep(2)
                        if text:
                            break
                    if not text and last_error:
                        print(f"[{menu_name}] Warning: Gemini API call failed ({last_error}).")
                        if task_id and task_id in GENERATE_TASKS:
                            GENERATE_TASKS[task_id]['message'] = f"AI Quality Check ({iteration}/{MAX_ITERATIONS}) Failed. Fallback to semantic rules."
                            import time
                            time.sleep(2)
                        continue

            if text:
                status = "PERFECT" if "STATUS: PERFECT" in text.upper() else "NEEDS_FIX"

                if status == 'PERFECT':
                    if iteration == 1:
                        # Lightweight verify: chỉ gửi ảnh, không HTML/CSS → tiết kiệm token
                        print(f"[{menu_name}] AI claimed PERFECT on iter 1. Running lightweight verify...")
                        if task_id and task_id in GENERATE_TASKS:
                            GENERATE_TASKS[task_id]['message'] = f"AI Quality Check: Verifying PERFECT claim..."
                        try:
                            # Fix: guard models_to_try scope (undefined khi DEMO_KEY hoặc list rỗng)
                            _verify_model = (models_to_try[0] if 'models_to_try' in dir() and models_to_try
                                             else 'gemini-2.0-flash-lite')
                            # Fix: prompt phù hợp với số ảnh thực tế gửi đi
                            if target_pil:
                                _verify_prompt = (
                                    "Quick visual check: Compare these two images (Figma design vs HTML render).\n"
                                    "List any differences you can spot (be precise).\n"
                                    "DIFFERENCES: [list each one, or write \"None\"]\n"
                                    "VERDICT: MATCH (if no differences) or MISMATCH (if any difference found)"
                                )
                            else:
                                _verify_prompt = (
                                    "Quick visual check: Inspect this rendered HTML image for any severe visual bugs or flaws.\n"
                                    "List any issues you can spot.\n"
                                    "DIFFERENCES: [list each one, or write \"None\"]\n"
                                    "VERDICT: MATCH (if no issues found) or MISMATCH (if any issue found)"
                                )
                            _verify_contents = [_verify_prompt]
                            if target_pil:
                                _verify_contents.append(target_pil)
                            _verify_contents.append(render_pil)
                            with compare_and_fix_visuals.api_lock:
                                _vresp = client.models.generate_content(
                                    model=_verify_model,
                                    contents=_verify_contents
                                )
                            if _vresp and _vresp.text and 'VERDICT: MATCH' in _vresp.text.upper():
                                print(f"[{menu_name}] Lightweight verify CONFIRMED PERFECT! Early exit.")
                                break
                            else:
                                _diff_info = _vresp.text.strip()[:200] if _vresp and _vresp.text else 'unknown'
                                print(f"[{menu_name}] False PERFECT caught! Verify: {_diff_info}")
                        except Exception as _ve:
                            print(f"[{menu_name}] Lightweight verify error: {_ve}. Forcing double-check.")
                    else:
                        print(f"[{menu_name}] Visual match is PERFECT at iteration {iteration}!")
                        break

                import re
                html_match = re.search(r'```html\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
                if html_match:
                    html = html_match.group(1).strip()
                    
                css_match = re.search(r'```css\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
                if css_match:
                    css = css_match.group(1).strip()

                print(f"[{menu_name}] Visual correction applied (Iteration {iteration}).")

        except Exception as e:
            print(f"[{menu_name}] Gemini Vision Error: {e}")
            continue

    # CLEANUP TEMP FILES
    for p in [target_img_path, render_img_path, temp_html_path]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    return html, css, js


# ---------------------------------------------------------------------------
# Async generation runner
# ---------------------------------------------------------------------------

def run_generate_async(task_id, site_id, menu_param, target_dir, figma_token, config, menu, site, feedback):
    def check_cancel_and_update(msg):
        if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled':
            raise Exception("CANCELLED_BY_USER")
        GENERATE_TASKS[task_id] = {"status": "running", "message": msg}

    import shutil
    try:
        check_cancel_and_update("Parsing Figma link...")

        folder, menu_slug = parse_folder_slug(menu_param)
        figma_link = menu.get('figma_link', '').strip()
        image_paths = menu.get('image_paths', [])
        if not image_paths and menu.get('image_path'):
            image_paths = [menu.get('image_path').strip()]
        ai_hint = menu.get('ai_hint', '').strip()
        
        html_result = ""
        css_result = ""
        gemini_api_key = config.get('gemini_api_key', '').strip()

        if figma_link:
            file_key, node_id = parse_figma_url(figma_link)
            if not file_key or not node_id:
                raise Exception("Invalid Figma link format.")

            if not figma_token:
                raise Exception("Figma token is missing in settings.")

            check_cancel_and_update("Fetching Figma design...")
            design_data = fetch_figma_node(file_key, node_id, figma_token)
            if not design_data:
                raise Exception("Could not fetch design from Figma API (Network or Token error).")
            if 'error' in design_data:
                raise Exception(f"Figma API Error: {design_data['error']}")
            if 'nodes' not in design_data or node_id not in design_data['nodes']:
                err_msg = design_data.get('err', 'Unknown error')
                raise Exception(f"Could not fetch design from Figma API. Reason: {err_msg}")

            check_cancel_and_update("Downloading assets...")
            document = design_data['nodes'][node_id]['document']
            used_refs = extract_used_image_refs(document)
            image_map = fetch_figma_images(file_key, figma_token)
            local_image_map = download_and_map_figma_images(image_map, target_dir, menu_slug, used_refs)

            # Export icons and merge into local_image_map
            icon_map = export_figma_icons(file_key, document, figma_token, target_dir, menu_slug)
            if icon_map:
                local_image_map.update(icon_map)

            check_cancel_and_update("Compiling HTML/CSS...")
            compile_result = compile_figma_node_to_html_css(design_data, node_id, local_image_map)
            if not compile_result:
                raise Exception("Failed to compile HTML/CSS.")
            html_result, css_result = compile_result

            if gemini_api_key:
                check_cancel_and_update("Applying structural templates...")
                html_result, css_result, js_result, rename_map = apply_structural_templates(
                    html_result, css_result, "", gemini_api_key, menu_slug, task_id, ai_hint
                )
                
                # Physically rename image files if AI requested it
                if rename_map:
                    images_dir = os.path.join(target_dir, "images", menu_slug)
                    if os.path.exists(images_dir):
                        for mapping in rename_map:
                            raw_old = mapping.get('old_name')
                            raw_new = mapping.get('new_name')
                            if raw_old and raw_new:
                                old_name = os.path.basename(raw_old)
                                new_name = os.path.basename(raw_new)
                                if old_name != new_name:
                                    old_path = os.path.join(images_dir, old_name)
                                    new_path = os.path.join(images_dir, new_name)
                                    if os.path.exists(old_path) and not os.path.exists(new_path):
                                        try:
                                            os.rename(old_path, new_path)
                                            print(f"[{menu_slug}] Renamed image {old_name} -> {new_name}")
                                        except Exception as rename_err:
                                            print(f"[{menu_slug}] Failed to rename image {old_name}: {rename_err}")

                check_cancel_and_update("Refining visuals with AI...")
                html_result, css_result, js_result = compare_and_fix_visuals(
                    figma_token, figma_link, html_result, css_result, js_result,
                    [f"{menu_slug}.css"], menu_slug, gemini_api_key, task_id
                )

                if feedback:
                    check_cancel_and_update("Applying feedback...")
                    css_result = apply_dynamic_css_feedback(css_result, feedback)

        elif image_paths:
            if not gemini_api_key:
                raise Exception("Gemini API Key is required for Image-to-HTML generation.")
                
            check_cancel_and_update("Processing uploaded images...")
            from google import genai
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'config.json')
            gemini_api_key_2 = ""
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                        gemini_api_key_2 = cfg.get('gemini_api_key_2', '').strip()
                except: pass
                
            client = genai.Client(api_key=gemini_api_key)
            client_2 = genai.Client(api_key=gemini_api_key_2) if gemini_api_key_2 else None
            
            root_path = os.path.dirname(os.path.dirname(__file__))
            images_dir = os.path.join(target_dir, "images", menu_slug)
            os.makedirs(images_dir, exist_ok=True)
            
            gemini_files = []
            valid_image_paths = []
            
            for idx, path in enumerate(image_paths):
                if not path: continue
                abs_image_path = path if os.path.isabs(path) else os.path.join(root_path, path)
                if not os.path.exists(abs_image_path):
                    continue
                    
                valid_image_paths.append(abs_image_path)
                ext = os.path.splitext(abs_image_path)[1]
                dest_image_name = f"source_image_{idx}{ext}"
                dest_image_path = os.path.join(images_dir, dest_image_name)
                shutil.copy(abs_image_path, dest_image_path)
                
                # Robust upload with fallback and retry
                import time
                import re
                max_up_retries = 3
                uploaded_file = None
                for up_attempt in range(max_up_retries):
                    try:
                        uploaded_file = client.files.upload(file=abs_image_path)
                        break
                    except Exception as up_e:
                        err_str = str(up_e)
                        if client_2 and ('429' in err_str or '400' in err_str or 'invalid' in err_str.lower() or 'quota' in err_str.lower() or 'exhausted' in err_str.lower() or 'limit' in err_str.lower()):
                            print(f"[{menu_slug}] Primary API Key limit reached during Image Upload! Switching to Fallback Key...")
                            check_cancel_and_update("Upload quota reached. Switching to Fallback API Key...")
                            client = client_2
                            client_2 = None
                            
                            # Re-upload previously successful images with the new key
                            gemini_files = []
                            for prev_path in valid_image_paths[:-1]:
                                try:
                                    gemini_files.append(client.files.upload(file=prev_path))
                                except: pass
                                
                            try:
                                uploaded_file = client.files.upload(file=abs_image_path)
                                break
                            except Exception as fallback_e:
                                err_str = str(fallback_e)
                        
                        if '429' in err_str and 'RESOURCE_EXHAUSTED' in err_str and up_attempt < max_up_retries - 1:
                            match = re.search(r'retry in (\d+\.\d+|\d+)s', err_str)
                            wait_time = float(match.group(1)) + 1 if match else 20.0
                            print(f"[{menu_slug}] Upload Rate limit hit. Waiting {wait_time}s before retry...")
                            if wait_time > 65:
                                raise Exception("API limit exceeded. Please try again later or use a different API Key.")
                            for remaining in range(int(wait_time), 0, -1):
                                check_cancel_and_update(f"Rate limit hit. Waiting {remaining}s...")
                                time.sleep(1)
                        else:
                            if up_attempt == max_up_retries - 1:
                                raise Exception(f"Upload API Error after retries: {err_str}")
                            raise
                gemini_files.append(uploaded_file)
                
            if not gemini_files:
                raise Exception("No valid image files found on server.")
            
            GENERATE_TASKS[task_id] = {"status": "running", "message": "Generating HTML/CSS from Images..."}
            
            structure_template, form_template = load_ai_templates()
            
            num_images = len(gemini_files)
            conbox_hint = f"The user provided {num_images} image(s). This EXACTLY MEANS there are {num_images} main sections in the design. You MUST create exactly {num_images} `<div class=\"con-box\">` elements inside `.content-box`, each corresponding chronologically to one of the images provided." if num_images > 0 else ""
            
            unified_rules = get_unified_ai_rules(ai_hint, None, conbox_hint, menu_slug=menu_slug)
            
            prompt = f"""You are an expert Frontend Developer. 
Your task is to convert the provided screenshot(s) into pixel-perfect, responsive HTML and CSS.

To ensure extreme accuracy, you MUST follow this Chain-of-Thought pipeline before writing any code:
1. Vision analysis: Describe the overall visual theme, colors, and design style.
2. Layout analysis: Break down the structural layout (e.g., headers, 3-column grids, complex flowcharts, nested boxes).
3. UI Fidelity & Metrics: Explicitly state the exact background colors (Hex codes), font weights, border radius, and estimate paddings/margins. DO NOT use generic colors.
4. OCR / read text: Extract ALL text exactly as it appears in the image, ensuring you don't miss small details.
5. Component identification: Identify all specific UI components like buttons, connecting arrows, lines, and boxes.

CRITICAL RULE ABOUT IMAGES & ICONS (ABSOLUTELY NO HALLUCINATIONS):
- The server DOES NOT have any pre-cropped icon or image files! There are NO image files available except `source_image_0.jpg` if provided.
- DO NOT invent, guess, or hallucinate image paths like `<img src="./images/.../some_icon.png">` or `<img src="./images/.../sdg_icon.png">`.
- ANY colored boxes, SDG badges, icons, arrows, number badges, or logos MUST be built using PURE HTML & CSS (e.g. background-color, border, border-radius, SVG data URI, or CSS ::before / ::after). NEVER put an <img> tag for an icon or box!
- Only use an <img> tag if you are referencing an actual uploaded image `source_image_0.jpg`.

{unified_rules}

Return ONLY a valid JSON object matching this schema without markdown formatting:
{{
  "vision_analysis": "...",
  "layout_analysis": "...",
  "ui_metrics": "...",
  "ocr_text": "...",
  "components": ["...", "..."],
  "html": "full HTML content inside body",
  "css": "full CSS content, one rule per line",
  "js": "any custom Javascript code without <script> tags, or empty string"
}}
"""
            contents = gemini_files + [prompt]
            import time
            import re
            models_to_try = get_gemini_models_to_try()
            max_retries = 3
            response = None
            current_key_name = "Primary Key"
            
            for model in models_to_try:
                for attempt in range(max_retries):
                    try:
                        print(f"[{menu_slug}] Generating Image-to-HTML using {model} (Attempt {attempt+1})...")
                        check_cancel_and_update(f"Generating Image-to-HTML ({current_key_name})...")
                        response = client.models.generate_content(
                            model=model,
                            contents=contents
                        )
                        break
                    except Exception as ce:
                        err_str = str(ce)
                        if client_2 and ('429' in err_str or '400' in err_str or 'invalid' in err_str.lower() or 'quota' in err_str.lower() or 'exhausted' in err_str.lower() or 'limit' in err_str.lower()):
                            print(f"[{menu_slug}] Primary API Key limit reached in Image-to-HTML! Switching to Fallback Key...")
                            check_cancel_and_update("Rate limit hit! Switching to Fallback API Key...")
                            client = client_2
                            client_2 = None
                            
                            gemini_files = []
                            for path in valid_image_paths:
                                try:
                                    uploaded = client.files.upload(file=path)
                                    gemini_files.append(uploaded)
                                except Exception as up_err:
                                    print(f"[{menu_slug}] Fallback upload error: {up_err}")
                            if gemini_files:
                                contents = gemini_files + [prompt]
                                
                            current_key_name = "Fallback Key"
                            try:
                                check_cancel_and_update(f"Generating Image-to-HTML ({current_key_name})...")
                                response = client.models.generate_content(
                                    model=model,
                                    contents=contents
                                )
                                break
                            except Exception as fallback_e:
                                err_str = str(fallback_e)
                        
                        if '429' in err_str and 'RESOURCE_EXHAUSTED' in err_str:
                            if attempt < max_retries - 1:
                                match = re.search(r'retry in (\d+\.\d+|\d+)s', err_str)
                                wait_time = float(match.group(1)) + 1 if match else 20.0
                                if wait_time > 65:
                                    print(f"[{menu_slug}] API limit wait too long ({wait_time}s). Trying next model...")
                                    break # Bỏ qua retry, thử model tiếp theo
                                print(f"[{menu_slug}] Rate limit hit on {model}. Waiting {wait_time}s before retry...")
                                for remaining in range(int(wait_time), 0, -1):
                                    check_cancel_and_update(f"Rate limit hit. Waiting {remaining}s...")
                                    time.sleep(1)
                            else:
                                print(f"[{menu_slug}] AI Error on {model} after retries: {err_str}")
                                break # Thử model tiếp theo
                        else:
                            print(f"[{menu_slug}] Other API Error on {model}: {err_str}")
                            break # Nếu lỗi khác (không phải 429), chuyển sang model tiếp theo
                if response and response.text:
                    break
            
            if not response or not response.text:
                raise Exception("All AI models failed or exceeded quota. Please check your API Keys.")
            
            text = response.text.strip()
            if '```json' in text: text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'): text = text.split('```')[1].split('```')[0].strip()
            
            import json_repair
            result = json_repair.loads(text)
            html_result = result.get('html', '')
            css_result = result.get('css', '')
            js_result = result.get('js', '')

            # Create a thumbnail from the first image
            thumb_path = os.path.join(target_dir, "thumb.jpg")
            if not os.path.exists(thumb_path):
                shutil.copy(valid_image_paths[0], thumb_path)

            check_cancel_and_update("Refining visuals with AI...")
            # For compare_and_fix_visuals, we pass all valid image paths to be stitched vertically
            html_result, css_result, js_result = compare_and_fix_visuals(
                "", "", html_result, css_result, js_result,
                [f"{menu_slug}.css"], menu_slug, gemini_api_key, task_id, local_image_paths=valid_image_paths
            )

            if feedback:
                check_cancel_and_update("Applying feedback...")
                css_result = apply_dynamic_css_feedback(css_result, feedback)
        else:
            raise Exception("No Figma link or uploaded image found for this page.")

        check_cancel_and_update("Saving generated files...")
        # Reconcile image references: đảm bảo mọi thẻ img hoặc CSS url khớp chính xác phần mở rộng file thực tế trên đĩa
        images_dir = os.path.join(target_dir, "images", menu_slug)
        if os.path.exists(images_dir):
            existing_files = os.listdir(images_dir)
            for f in existing_files:
                stem, ext = os.path.splitext(f)
                if ext.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.svg']:
                    for alt_ext in ['.png', '.jpg', '.jpeg', '.webp']:
                        wrong_ref = f"{stem}{alt_ext}"
                        if wrong_ref != f:
                            html_result = html_result.replace(wrong_ref, f)
                            css_result = css_result.replace(wrong_ref, f)

            # Xử lý triệt để thẻ <img> ma (ghost images hoàn toàn không có file trên đĩa)
            import re
            img_src_pattern = re.compile(r'<img\s+([^>]*?)src=["\']([^"\']*?/images/' + re.escape(menu_slug) + r'/([^"\']+))["\']([^>]*?)>', re.IGNORECASE)
            def _clean_missing_img(match):
                full_tag = match.group(0)
                file_name = match.group(3)
                if not os.path.exists(os.path.join(images_dir, file_name)):
                    alt_match = re.search(r'alt=["\']([^"\']*)["\']', full_tag, re.IGNORECASE)
                    alt_text = alt_match.group(1) if alt_match else ""
                    print(f"[{menu_slug}] Cleaned ghost image reference: {file_name} (alt: '{alt_text}')")
                    if alt_text:
                        return f'<span class="img-badge-text">{alt_text}</span>'
                    return ''
                return full_tag

            html_result = img_src_pattern.sub(_clean_missing_img, html_result)

        # Write files
        html_path = os.path.join(target_dir, f"{menu_slug}.html")
        css_path = os.path.join(target_dir, f"{menu_slug}.css")
        js_path = os.path.join(target_dir, f"{menu_slug}.js")

        base_style_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'layout', 'style.css')
        if os.path.exists(base_style_src):
            site_root_dir = os.path.join(OUTPUT_DIR, site_id)
            os.makedirs(site_root_dir, exist_ok=True)
            shutil.copy(base_style_src, os.path.join(site_root_dir, "style.css"))

        style_href = "../style.css" if folder else "style.css"
        js_script = f'    <script src="{menu_slug}.js"></script>\n' if js_result else ""

        final_html = (
            f'<!DOCTYPE html>\n<html lang="vi">\n<head>\n'
            f'    <meta charset="UTF-8">\n'
            f'    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'    <title>{menu.get("name", menu_slug)}</title>\n'
            f'    <link rel="stylesheet" href="{style_href}">\n'
            f'    <link rel="stylesheet" href="{menu_slug}.css">\n'
            f'</head>\n<body>\n    {html_result}\n'
            f'{js_script}'
            f'</body>\n</html>'
        )

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(final_html)
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(css_result)
        if js_result:
            with open(js_path, "w", encoding="utf-8") as f:
                f.write(js_result)
        elif os.path.exists(js_path):
            os.remove(js_path)

        sites = load_data()
        updated_site = next((s for s in sites if s['id'] == site_id), None)
        if updated_site:
            updated_menu = next(
                (m for m in updated_site['menus']
                 if m.get('folder', '') == folder and m['slug'] == menu_slug),
                None
            )
            if updated_menu:
                updated_menu['generated'] = True
                save_data(sites)

        if GENERATE_TASKS.get(task_id, {}).get('status') == 'cancelled':
            return
            
        GENERATE_TASKS[task_id] = {
            "status": "success",
            "message": f'Successfully generated page "{menu["name"]}"!'
        }
    except Exception as e:
        if str(e) == "CANCELLED_BY_USER":
            return
        import traceback
        traceback.print_exc()
        if GENERATE_TASKS.get(task_id, {}).get('status') != 'cancelled':
            GENERATE_TASKS[task_id] = {"status": "error", "message": f'Generation error: {str(e)}'}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@generate_bp.route('/site/<site_id>/generate/<menu_param>', methods=['POST'])
def generate_files(site_id, menu_param):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    if not site:
        return jsonify({'success': False, 'message': 'Site not found!'}), 404

    folder, menu_slug = parse_folder_slug(menu_param)
    menu = next(
        (m for m in site['menus'] if (m.get('folder') or '') == folder and m.get('slug') == menu_slug),
        None
    )
    if not menu:
        return jsonify({'success': False, 'message': 'Page not found!'}), 404

    if not folder:
        folder = menu_slug

    target_dir = os.path.join(OUTPUT_DIR, site_id, folder)
    os.makedirs(target_dir, exist_ok=True)

    config = get_config()
    figma_token = config.get('figma_token', '').strip()
    feedback = request.args.get('feedback', '').strip()

    task_id = f"gen--{site_id}--{folder}--{menu_slug}"

    if GENERATE_TASKS.get(task_id, {}).get('status') == 'running':
        return jsonify({'success': True, 'task_id': task_id, 'message': 'Page is currently generating!', 'already_running': True})

    # Clear old deploy task to prevent stale "Successfully deployed" status
    original_folder, _ = parse_folder_slug(menu_param)
    deploy_task_id = f"{site_id}--{original_folder}--{menu_slug}"
    from routes.deploy import DEPLOY_TASKS
    
    # Check if deploying is running
    if DEPLOY_TASKS.get(deploy_task_id, {}).get('status') == 'running':
        return jsonify({'success': False, 'message': 'Cannot generate while page is being deployed!'})
        
    if deploy_task_id in DEPLOY_TASKS:
        del DEPLOY_TASKS[deploy_task_id]

    GENERATE_TASKS[task_id] = {"status": "running", "message": "Starting generation..."}

    thread = threading.Thread(
        target=run_generate_async,
        args=(task_id, site_id, menu_param, target_dir, figma_token, config, menu, site, feedback)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'task_id': task_id, 'message': 'Started generation process.'})


@generate_bp.route('/api/generate_status', methods=['GET'])
def api_generate_status():
    return jsonify(GENERATE_TASKS)


@generate_bp.route('/api/generate_cancel/<task_id>', methods=['POST'])
def api_generate_cancel(task_id):
    if task_id in GENERATE_TASKS and GENERATE_TASKS[task_id]['status'] == 'running':
        GENERATE_TASKS[task_id] = {"status": "cancelled", "message": "Generation cancelled by user."}
        return jsonify({'success': True, 'message': 'Cancellation requested!'})
    return jsonify({'success': False, 'message': 'Task does not exist or already finished.'})
