import sys
import os
import json
import time
import pytest

import importlib.util

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_service(name, rel_path):
    path = os.path.join(BASE_DIR, rel_path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# 1. Test Logging Service
def test_logging_service():
    logging_srv = load_service("test_logging_module", "logging/server.py")
    client = logging_srv.app.test_client()

    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["port"] == 8006

    # Ingest log
    ingest_res = client.post("/api/logs", json={
        "type": "test_event",
        "invoker": "unit_test",
        "recipient": "logging",
        "conversation_id": "test_conv_123",
        "payload": {"data": "test_payload", "api_key": "secret_key_123"},
        "short_description": "Unit test log"
    })
    assert ingest_res.status_code == 201

    # Query logs
    q_res = client.post("/api/logs/query", json={"conversation_id": "test_conv_123"})
    assert q_res.status_code == 200
    logs = q_res.get_json().get("logs", [])
    assert len(logs) >= 1
    # Verify API key was redacted
    assert logs[0]["payload"]["api_key"] == "****"

    # Stats
    stats_res = client.get("/api/logs/stats")
    assert stats_res.status_code == 200
    assert stats_res.get_json()["total_logs"] >= 1

# 2. Test Auth Service
def test_auth_service():
    import auth_service.server as auth_srv
    client = auth_srv.app.test_client()

    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["port"] == 8001

    # Login with seed admin credentials
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200
    data = login_res.get_json()
    assert data["status"] == "success"
    assert data["user"]["role"] == "Admin"

    # Bad login
    bad_res = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert bad_res.status_code == 401
    assert "Invalid username or password" in bad_res.get_json()["error"]

    # Register new user (initially Locked per specification)
    uname = f"testuser_{int(time.time() * 1000)}"
    reg_res = client.post("/api/auth/register", json={"username": uname, "password": "password123"})
    assert reg_res.status_code == 201

    # Attempt login with locked account -> must fail with 403 and Locked error
    locked_login = client.post("/api/auth/login", json={"username": uname, "password": "password123"})
    assert locked_login.status_code == 403
    assert "Account is Locked" in locked_login.get_json()["error"]

    # List users to find user id
    users_res = client.get("/api/users")
    assert users_res.status_code == 200
    users = users_res.get_json()["users"]
    new_user = next((u for u in users if u["email"] == uname), None)
    assert new_user is not None
    assert new_user["status"] == "Locked"

    # Unlock user via status endpoint
    unlock_res = client.put(f"/api/users/{new_user['id']}/status", json={"status": "Active"})
    assert unlock_res.status_code == 200

    # Successful login after unlocking
    unlocked_login = client.post("/api/auth/login", json={"username": uname, "password": "password123"})
    assert unlocked_login.status_code == 200
    assert unlocked_login.get_json()["status"] == "success"

    # Generate API key
    key_res = client.post("/api/keys", json={
        "key_name": "Test Key",
        "creator_email": "admin",
        "containers": ["tools", "doc_rag"],
        "access_levels": ["Read", "Write"]
    })
    assert key_res.status_code == 201
    key_data = key_res.get_json()
    raw_key = key_data["api_key"]
    assert raw_key.startswith("key-")

    # Validate API key
    val_res = client.post("/api/auth/validate_key", json={
        "api_key": raw_key,
        "container": "tools",
        "access_level": "read"
    })
    assert val_res.status_code == 200
    assert val_res.get_json()["valid"] is True

# 3. Test Tools Service
def test_tools_service():
    import tools.server as tools_srv
    client = tools_srv.app.test_client()

    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["port"] == 8005

    # List tools
    tools_list = client.get("/api/tools/list").get_json()["tools"]
    assert len(tools_list) >= 3

    # Employee search tool (single keyword backward compatibility)
    emp_res = client.post("/api/tools/call", json={
        "tool": "person_search.query_person_registry",
        "arguments": {"keyword": "Dubois", "field": "name"},
        "conversation_id": "test_conv"
    })
    assert emp_res.status_code == 200
    emp_data = emp_res.get_json()["result"]
    assert emp_data["count"] >= 1
    assert "Lucas Dubois" in [r["name"] for r in emp_data["results"]]

    # Employee search tool (list of search texts)
    emp_multi_res = client.post("/api/tools/call", json={
        "tool": "person_search.query_person_registry",
        "arguments": {"keywords": ["Dubois", "Berlin"], "field": "all"},
        "conversation_id": "test_conv"
    })
    assert emp_multi_res.status_code == 200
    emp_multi_data = emp_multi_res.get_json()["result"]
    assert emp_multi_data["count"] >= 2
    matched_names = [r["name"] for r in emp_multi_data["results"]]
    assert "Lucas Dubois" in matched_names
    assert "Elena Rostova" in matched_names

    # Stock search tool (gainers)
    stock_res = client.post("/api/tools/call", json={
        "tool": "stock_search.query_stocks",
        "arguments": {"action": "gainers", "limit": 3},
        "conversation_id": "test_conv"
    })
    assert stock_res.status_code == 200
    stock_data = stock_res.get_json()["result"]
    assert stock_data["status"] == "success"
    assert len(stock_data["results"]) <= 3

# 4. Test Doc RAG Service
def test_doc_rag_service():
    pytest.importorskip("chromadb")
    doc_rag_srv = load_service("test_doc_rag_module", "doc_RAG/server.py")
    client = doc_rag_srv.app.test_client()

    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["port"] == 8003

    # 1. List / Stats
    stats_res = client.get("/api/rag/list")
    assert stats_res.status_code == 200
    stats_data = stats_res.get_json()
    assert "count_documents" in stats_data
    assert "count_skills" in stats_data
    assert "db_size_mb" in stats_data

    # 2. Add New Document
    add_doc_res = client.post("/api/rag/add", json={
        "user_id": "test_admin",
        "type": "document",
        "name": "spec_test_doc",
        "text": "Antigravity Agent system with ChromaDB and FastMCP architecture.",
        "chunk_size": 200,
        "overlap": 20
    })
    assert add_doc_res.status_code == 200
    assert add_doc_res.get_json()["status"] == "success"

    # 3. Add New Skill
    add_skill_res = client.post("/api/rag/add", json={
        "user_id": "test_admin",
        "type": "skill",
        "name": "spec_test_skill",
        "text": "A skill to analyze system logs and telemetry.",
        "vector_text": "analyze system logs and telemetry"
    })
    assert add_skill_res.status_code == 200
    assert add_skill_res.get_json()["status"] == "success"

    # 4. Query Documents
    query_res = client.post("/api/rag/query", json={
        "user_id": "test_user",
        "conversation_id": "conv_test_123",
        "type": "document",
        "query": "ChromaDB FastMCP",
        "k": 3,
        "threshold": 0.1
    })
    assert query_res.status_code == 200
    q_data = query_res.get_json()
    assert q_data["status"] == "success"

    # 5. Delete Document
    del_res = client.post("/api/rag/delete", json={
        "user_id": "test_admin",
        "type": "document",
        "name": "spec_test_doc"
    })
    assert del_res.status_code == 200
    assert del_res.get_json()["status"] == "success"

# 5. Test Agents Service
def test_agents_service():
    agents_srv = load_service("test_agents_module", "agents/server.py")
    client = agents_srv.app.test_client()

    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["port"] == 8002

    # Models list
    models_res = client.get("/api/agents/models")
    assert models_res.status_code == 200
    assert len(models_res.get_json().get("models", [])) >= 1

    # Skills list
    skills_res = client.get("/api/agents/skills")
    assert skills_res.status_code == 200

# 6. Test Web UI
def test_web_ui_routes():
    web_app = load_service("test_web_ui_module", "web_ui/app.py")
    client = web_app.app.test_client()

    # Index page
    res = client.get("/")
    assert res.status_code == 200
    assert b"Agent With RAG" in res.data
    assert b"page-chat" in res.data
    assert b"page-containers" in res.data
    assert b"page-auth" in res.data
    assert b"loginModal" in res.data

# 7. Test Person Information Skill & Employee Search Modularity
def test_person_information_skill_modular():
    person_search_mod = load_service(
        "test_person_search_module",
        "agents/skills/person-information-skill/scripts/person_search.py"
    )
    query_person_registry = person_search_mod.query_person_registry
    normalize_search_terms = person_search_mod.normalize_search_terms
    filter_person_records = person_search_mod.filter_person_records

    from tools.scripts.employee_search import search_employees, normalize_search_terms as norm_emp, filter_records

    # Test normalization
    assert normalize_search_terms([" Lucas ", "  PARIS "]) == ["lucas", "paris"]
    assert normalize_search_terms(" Dubois ") == ["dubois"]
    assert normalize_search_terms([]) == []

    # Test skill query with list of search texts
    res = query_person_registry(keywords=["Lucas Dubois", "Berlin"])
    assert res["status"] == "success"
    assert res["total_matches"] == 2
    names = [r["name"] for r in res["results"]]
    assert "Lucas Dubois" in names
    assert "Elena Rostova" in names

    # Test deduplication when multiple terms match the same entry
    res_dedup = query_person_registry(keywords=["Lucas Dubois", "Paris", "France", "Chief AI Architect"])
    assert res_dedup["status"] == "success"
    lucas_matches = [r for r in res_dedup["results"] if r["name"] == "Lucas Dubois"]
    assert len(lucas_matches) == 1, "Lucas Dubois should only appear once despite matching all 4 terms"

    # Test modular search_employees from tools
    emp_matches = search_employees(keywords=["Paris", "Tokyo"])
    assert len(emp_matches) >= 2
    emp_names = [e["name"] for e in emp_matches]
    assert "Lucas Dubois" in emp_names
    assert "Kenji Takahashi" in emp_names

