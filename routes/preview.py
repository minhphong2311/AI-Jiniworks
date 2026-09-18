# Author: sawyer88
# Email: phongnguyen@andvina.com

"""
routes/preview.py
Blueprint xử lý chức năng Preview trang đã generate.
"""
import os
import time

from flask import Blueprint, render_template, make_response, send_from_directory, request, jsonify
from .helpers import load_data, parse_folder_slug, OUTPUT_DIR

preview_bp = Blueprint('preview', __name__)

@preview_bp.route('/api/get-code', methods=['GET'])
def get_code():
    site_id = request.args.get('site_id')
    folder = request.args.get('folder', '')
    slug = request.args.get('slug')
    
    if folder:
        dir_path = os.path.join(OUTPUT_DIR, site_id, folder)
    else:
        dir_path = os.path.join(OUTPUT_DIR, site_id)
        
    html_path = os.path.join(dir_path, f'{slug}.html')
    css_path = os.path.join(dir_path, f'{slug}.css')
    js_path = os.path.join(dir_path, f'{slug}.js')

    html = ""
    css = ""
    js = ""

    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
            import re
            match = re.search(r'<body[^>]*>(.*)</body>', html, re.IGNORECASE | re.DOTALL)
            if match:
                html = match.group(1).strip()
                html = re.sub(r'\n?\s*<script\s+src=["\'](?!http)[^"\']*\.js["\']\s*></script>', '', html, flags=re.IGNORECASE).strip()
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            js = f.read()

    return jsonify({"success": True, "html": html, "css": css, "js": js})

@preview_bp.route('/api/save-code', methods=['POST'])
def save_code():
    data = request.json
    site_id = data.get('site_id')
    folder = data.get('folder', '')
    slug = data.get('slug')
    
    if folder:
        dir_path = os.path.join(OUTPUT_DIR, site_id, folder)
    else:
        dir_path = os.path.join(OUTPUT_DIR, site_id)
    os.makedirs(dir_path, exist_ok=True)
        
    html_path = os.path.join(dir_path, f'{slug}.html')
    css_path = os.path.join(dir_path, f'{slug}.css')
    js_path = os.path.join(dir_path, f'{slug}.js')

    if 'html' in data:
        new_html = data['html']
        if '<html' not in new_html.lower() and '<!doctype html>' not in new_html.lower():
            style_href = "../style.css" if folder else "style.css"
            new_html = (
                f'<!DOCTYPE html>\n<html lang="vi">\n<head>\n'
                f'    <meta charset="UTF-8">\n'
                f'    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                f'    <title>{slug}</title>\n'
                f'    <link rel="stylesheet" href="{style_href}">\n'
                f'    <link rel="stylesheet" href="{slug}.css">\n'
                f'</head>\n<body>\n{new_html}\n'
                f'    <script src="{slug}.js"></script>\n'
                f'</body>\n</html>'
            )
        if os.path.exists(html_path):
            import shutil
            shutil.copyfile(html_path, html_path + '.bak')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(new_html)
            
    if 'css' in data:
        if os.path.exists(css_path):
            import shutil
            shutil.copyfile(css_path, css_path + '.bak')
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(data['css'])
            
    if 'js' in data:
        if os.path.exists(js_path):
            import shutil
            shutil.copyfile(js_path, js_path + '.bak')
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(data['js'])
            
    return jsonify({"success": True})

def render_preview_index(site_id, folder, menu_slug):
    sites = load_data()
    site = next((s for s in sites if s['id'] == site_id), None)
    menu_name = menu_slug
    figma_link = ''
    image_paths = []
    
    if site:
        menu = next(
            (m for m in site.get('menus', [])
             if m.get('folder', '') == folder and m['slug'] == menu_slug),
            None
        )
        if menu:
            menu_name = menu['name']
            figma_link = menu.get('figma_link', '')
            image_paths = menu.get('image_paths', [])
            if not image_paths and menu.get('image_path'):
                image_paths = [menu.get('image_path')]
            
    menu_param = f"{folder}--{menu_slug}" if folder else menu_slug
    return render_template(
        'preview_frame.html',
        site_id=site_id,
        menu_param=menu_param,
        folder=folder,
        menu_slug=menu_slug,
        menu_name=menu_name,
        site_name=site['name'] if site else site_id,
        figma_link=figma_link,
        image_paths=image_paths
    )


@preview_bp.route('/preview/<site_id>/<folder>/<slug>.do')
def preview_index(site_id, folder, slug):
    return render_preview_index(site_id, folder, slug)


@preview_bp.route('/preview/<site_id>/<slug>.do')
def preview_index_no_folder(site_id, slug):
    return render_preview_index(site_id, "", slug)


@preview_bp.route('/preview/raw/<site_id>/<folder>/<slug>.html')
def preview_raw(site_id, folder, slug):
    if folder:
        dir_path = os.path.join(OUTPUT_DIR, site_id, folder)
    else:
        dir_path = os.path.join(OUTPUT_DIR, site_id)
    html_path = os.path.join(dir_path, f'{slug}.html')

    if not os.path.exists(html_path):
        return "File not found", 404

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    t = int(time.time() * 1000)
    html_content = html_content.replace(
        f'href="{slug}.css"',
        f'href="{slug}.css?t={t}"'
    ).replace(
        f'src="{slug}.js"',
        f'src="{slug}.js?t={t}"'
    )

    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@preview_bp.route('/preview/raw/<site_id>/<slug>.html')
def preview_raw_no_folder(site_id, slug):
    return preview_raw(site_id, "", slug)


@preview_bp.route('/preview/raw/<site_id>/<folder>/<path:filename>')
def preview_asset_folder(site_id, folder, filename):
    dir_path = os.path.join(OUTPUT_DIR, site_id, folder)
    file_path = os.path.join(dir_path, filename)
    if os.path.exists(file_path):
        return send_from_directory(dir_path, filename)

    # Fallback thử các extension ảnh phổ biến nếu lệch đuôi (vd: gọi .png nhưng thực tế là .jpg)
    name_no_ext, ext = os.path.splitext(filename)
    if ext.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.svg']:
        for alt_ext in ['.jpg', '.png', '.jpeg', '.webp', '.svg']:
            alt_filename = name_no_ext + alt_ext
            if os.path.exists(os.path.join(dir_path, alt_filename)):
                return send_from_directory(dir_path, alt_filename)

    site_root = os.path.join(OUTPUT_DIR, site_id)
    if os.path.exists(os.path.join(site_root, filename)):
        return send_from_directory(site_root, filename)

    if ext.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.svg']:
        for alt_ext in ['.jpg', '.png', '.jpeg', '.webp', '.svg']:
            alt_filename = name_no_ext + alt_ext
            if os.path.exists(os.path.join(site_root, alt_filename)):
                return send_from_directory(site_root, alt_filename)

    return send_from_directory(site_root, filename)


@preview_bp.route('/preview/raw/<site_id>/<path:filename>')
def preview_asset_no_folder(site_id, filename):
    site_root = os.path.join(OUTPUT_DIR, site_id)
    if os.path.exists(os.path.join(site_root, filename)):
        return send_from_directory(site_root, filename)

    name_no_ext, ext = os.path.splitext(filename)
    if ext.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.svg']:
        for alt_ext in ['.jpg', '.png', '.jpeg', '.webp', '.svg']:
            alt_filename = name_no_ext + alt_ext
            if os.path.exists(os.path.join(site_root, alt_filename)):
                return send_from_directory(site_root, alt_filename)

    return send_from_directory(site_root, filename)
