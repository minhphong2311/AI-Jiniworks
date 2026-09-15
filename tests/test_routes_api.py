# tests/test_routes_api.py
import json
import pytest

def test_get_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"AI Jiniworks" in response.data
    assert b"ABCMS" not in response.data

def test_get_settings(client):
    response = client.get("/settings")
    assert response.status_code == 200
    assert b"Settings" in response.data

def test_generate_slug_api(client):
    payload = {"text": "Khoa Cong Nghe Thong Tin"}
    response = client.post(
        "/api/generate-slug",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "slug" in data
    assert len(data["slug"]) > 0

def test_get_site_menus_api(client):
    response = client.get("/api/site/testsite01/menus")
    assert response.status_code == 200
    data = response.get_json()
    assert "menus" in data
    assert len(data["menus"]) == 3
    assert data["menus"][0]["slug"] == "about-us"

def test_get_site_menus_not_found(client):
    response = client.get("/api/site/nonexistent_site/menus")
    assert response.status_code == 404

def test_save_site_menus_api(client):
    new_menus = [
        {
            "id": "menu-root-1",
            "name": "Giới thiệu mới",
            "slug": "about-us-new",
            "parent_id": None,
            "order": 0,
            "folder": "about-us-new"
        }
    ]
    response = client.post(
        "/api/site/testsite01/menus/save",
        data=json.dumps(new_menus),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("success") is True

    # Verify updated menus
    check_res = client.get("/api/site/testsite01/menus")
    check_data = check_res.get_json()
    assert len(check_data["menus"]) == 1
    assert check_data["menus"][0]["slug"] == "about-us-new"

def test_save_and_get_code_api(client):
    payload = {
        "site_id": "testsite01",
        "folder": "about-us",
        "slug": "history",
        "html": "<div class=\"history-content\">History detail</div>",
        "css": ".history-content { color: red; }",
        "js": "console.log('history');"
    }
    save_res = client.post(
        "/api/save-code",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert save_res.status_code == 200
    assert save_res.get_json().get("success") is True

    # Retrieve saved code
    get_res = client.get("/api/get-code?site_id=testsite01&folder=about-us&slug=history")
    assert get_res.status_code == 200
    code_data = get_res.get_json()
    assert code_data["success"] is True
    assert "History detail" in code_data["html"]
    assert ".history-content" in code_data["css"]
    assert "console.log('history');" in code_data["js"]


def test_generate_already_running(client):
    from routes.generate import GENERATE_TASKS
    task_id = "gen--testsite01--about-us--history"
    GENERATE_TASKS[task_id] = {"status": "running", "message": "Analyzing..."}
    try:
        response = client.post("/site/testsite01/generate/about-us--history")
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("success") is True
        assert data.get("already_running") is True
        assert data.get("task_id") == task_id
    finally:
        GENERATE_TASKS.pop(task_id, None)


def test_load_ai_templates():
    from routes.generate import load_ai_templates
    templates = load_ai_templates()
    assert len(templates) == 2
    structure_template, form_template = templates
    assert isinstance(structure_template, str)
    assert isinstance(form_template, str)
