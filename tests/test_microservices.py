import sys
import os
import json
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

    # List users
    users_res = client.get("/api/users")
    assert users_res.status_code == 200
    users = users_res.get_json()["users"]
    assert any(u["email"] == "admin" for u in users)

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

    # Employee search tool
    emp_res = client.post("/api/tools/call", json={
        "tool": "person_search.query_person_registry",
        "arguments": {"keyword": "Dubois", "field": "name"},
        "conversation_id": "test_conv"
    })
    assert emp_res.status_code == 200
    emp_data = emp_res.get_json()["result"]
    assert emp_data["count"] >= 1
    assert "Lucas Dubois" in [r["name"] for r in emp_data["results"]]

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

    # Stats
    stats_res = client.get("/api/rag/stats")
    assert stats_res.status_code == 200
    assert "total_chunks" in stats_res.get_json()

    # List skills
    skills_res = client.get("/api/rag/skills")
    assert skills_res.status_code == 200
    assert "skills" in skills_res.get_json()

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
