import json
import os
import pytest
from routes.helpers import (
    get_default_gemini_model,
    get_gemini_models_to_try,
    get_config,
    save_config
)

def test_default_gemini_model_fallback(mock_env):
    cfg = get_config()
    cfg.pop('gemini_model', None)
    save_config(cfg)
    # Default when not configured should be gemini-3.8-flash
    assert get_default_gemini_model() == 'gemini-3.8-flash'

def test_configured_gemini_model(mock_env):
    cfg = get_config()
    cfg['gemini_model'] = 'gemini-custom-model'
    save_config(cfg)
    assert get_default_gemini_model() == 'gemini-custom-model'

def test_multiple_models_comma_separated(mock_env):
    cfg = get_config()
    cfg['gemini_model'] = 'gemini-3.8-flash, gemini-3.6-flash, gemini-custom'
    save_config(cfg)
    # Default is the first model
    assert get_default_gemini_model() == 'gemini-3.8-flash'
    # List has user models in exact order first
    models = get_gemini_models_to_try()
    assert models[0] == 'gemini-3.8-flash'
    assert models[1] == 'gemini-3.6-flash'
    assert models[2] == 'gemini-custom'

def test_gemini_models_to_try_priority_and_deduplication(mock_env):
    cfg = get_config()
    cfg['gemini_model'] = 'gemini-3.8-flash'
    save_config(cfg)
    
    models = get_gemini_models_to_try(['gemini-2.0-flash', 'gemini-special'])
    # Configured primary should be first
    assert models[0] == 'gemini-3.8-flash'
    # Extra models should be present
    assert 'gemini-special' in models
    assert 'gemini-3.6-flash' in models
    assert 'gemini-3.5-flash' in models
    # No duplicates
    assert len(models) == len(set(models))

def test_api_config_gemini_model(client, mock_env):
    # Test GET config returns gemini_model
    res = client.get('/api/config')
    assert res.status_code == 200
    data = res.get_json()
    assert 'gemini_model' in data

    # Test POST config updates gemini_model
    payload = {
        'gemini_model': 'gemini-3.8-flash',
        'gemini_api_key': 'TEST_KEY'
    }
    res_post = client.post(
        '/api/config',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res_post.status_code == 200
    assert res_post.get_json().get('success') is True

    # Verify updated in get_config
    cfg = get_config()
    assert cfg.get('gemini_model') == 'gemini-3.8-flash'

def test_preview_raw_no_folder(client, mock_env):
    output_dir = mock_env["output_dir"]
    site_dir = os.path.join(output_dir, "testsite01")
    os.makedirs(site_dir, exist_ok=True)
    
    html_file = os.path.join(site_dir, "root_page.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html><head><link rel="stylesheet" href="root_page.css"></head><body><h1>Root Page</h1><script src="root_page.js"></script></body></html>')
        
    res = client.get('/preview/raw/testsite01/root_page.html')
    assert res.status_code == 200
    content = res.get_data(as_text=True)
    assert "Root Page" in content
    # Verify cache-busting timestamp was injected for both css and js
    assert 'href="root_page.css?t=' in content
    assert 'src="root_page.js?t=' in content

def test_chat_ai_fallback_on_primary_error(client, mock_env, monkeypatch):
    from unittest.mock import MagicMock
    cfg = get_config()
    cfg['gemini_api_key'] = 'INVALID_PRIMARY_KEY'
    cfg['gemini_api_key_2'] = 'FALLBACK_KEY'
    save_config(cfg)

    # Mock google.genai.Client
    import google.genai as genai_module
    
    mock_primary = MagicMock()
    mock_primary.models.generate_content.side_effect = Exception("400 INVALID_ARGUMENT: API key not valid.")
    
    mock_fallback = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "needs_clarification": False,
        "question": "",
        "thinking": "testing",
        "explanation": "Test updated",
        "html": "<div>Updated</div>",
        "css": ".test{}",
        "js": ""
    })
    mock_fallback.models.generate_content.return_value = mock_resp

    call_count = 0
    def mock_client_factory(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_primary
        return mock_fallback

    monkeypatch.setattr(genai_module, "Client", mock_client_factory)

    # Set up test page files
    output_dir = mock_env["output_dir"]
    site_dir = os.path.join(output_dir, "testsite01")
    os.makedirs(site_dir, exist_ok=True)
    with open(os.path.join(site_dir, "about-us.html"), "w", encoding="utf-8") as f:
        f.write("<div>Original</div>")
    with open(os.path.join(site_dir, "about-us.css"), "w", encoding="utf-8") as f:
        f.write(".orig{}")

    # Send chat request
    payload = {
        "site_id": "testsite01",
        "menu_param": "about-us",
        "message": "thêm liên kết điện thoại và email"
    }
    res = client.post("/api/chat", data=json.dumps(payload), content_type="application/json")
    
    # Must succeed because fallback client took over, and no UnboundLocalError occurs
    assert res.status_code == 200
    res_data = res.get_json()
    assert res_data.get("success") is True
    assert res_data.get("reply") == "Test updated"

