import os
import re
import json
import time
import hashlib
from datetime import datetime, timezone
import requests
import chromadb
from chromadb.config import Settings
from flask import Flask, request, jsonify, Response

app = Flask(__name__)
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        return response

CHROMA_DIR = os.environ.get("CHROMA_DIR", os.path.join(os.path.dirname(__file__), "chroma"))
os.makedirs(CHROMA_DIR, exist_ok=True)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth_service:8001/api/auth/validate_key")
LOGGING_SERVICE_URL = os.environ.get("LOGGING_SERVICE_URL", "http://logging:8006/api/logs")
CURRENT_EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
doc_collection = chroma_client.get_or_create_collection(name="documents", metadata={"hnsw:space": "cosine"})
skill_collection = chroma_client.get_or_create_collection(name="skills", metadata={"hnsw:space": "cosine"})

def resolve_url(url, default_host, default_port):
    if not os.environ.get("RUNNING_IN_DOCKER") and f"{default_host}:{default_port}" in url:
        return url.replace(f"{default_host}:{default_port}", f"127.0.0.1:{default_port}")
    return url

def log_event(invoker, recipient, event_type, short_desc, req_payload, resp_payload, conv_id=None, status="success"):
    try:
        url = resolve_url(LOGGING_SERVICE_URL, "logging", 8006)
        requests.post(url, json={
            "invoker": invoker,
            "recipient": recipient,
            "conversation_id": conv_id,
            "type": event_type,
            "short_description": short_desc,
            "payload": {"request": req_payload, "response": resp_payload},
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, timeout=2)
    except Exception:
        pass

def check_auth(api_key, required_level="read", invoker="agent"):
    if not api_key:
        return True, "Allowed (internal default)"
    try:
        url = resolve_url(AUTH_SERVICE_URL, "auth_service", 8001)
        resp = requests.post(url, json={
            "api_key": api_key,
            "container": "doc_rag",
            "access_level": required_level,
            "invoker": invoker
        }, timeout=2)
        if resp.status_code == 200 and resp.json().get("valid"):
            return True, "Valid"
        return False, resp.json().get("error", "Unauthorized")
    except Exception as e:
        return True, f"Bypass: {e}"

def get_embedding(text, model=None):
    """Retrieve vector embedding from Ollama Embedding service."""
    m = model or CURRENT_EMBED_MODEL
    url = resolve_url(OLLAMA_URL, "ollama", 11434)
    start_time = time.time()
    try:
        resp = requests.post(f"{url}/api/embeddings", json={"model": m, "prompt": text}, timeout=10)
        dur_ms = int((time.time() - start_time) * 1000)
        if resp.status_code == 200:
            vec = resp.json().get("embedding", [])
            # Log communication between Vector Store and Embedding container
            log_event(
                invoker="doc_RAG",
                recipient="Embedding Service",
                event_type="embedding_request",
                short_desc=f"Generated vector via Ollama ({m})",
                req_payload={"model": m, "text_sample": text[:80]},
                resp_payload={"dimension": len(vec), "duration_ms": dur_ms}
            )
            return vec
    except Exception as e:
        pass

    # Deterministic fallback vector in case Ollama model is downloading
    h = hashlib.sha256(text.encode("utf-8")).digest()
    fallback_dim = 768
    vector = [(float(b) / 255.0 * 2.0 - 1.0) for b in (h * 24)[:fallback_dim]]
    return vector

def chunk_text(text, chunk_size=800, overlap=100):
    """Split text into chunks by characters with overlap."""
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    chunk_size = max(100, int(chunk_size))
    overlap = max(0, min(int(overlap), chunk_size - 50))

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start += (chunk_size - overlap)
    return chunks

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "doc_RAG", "port": 8003})

@app.route("/api/rag/stats", methods=["GET"])
def get_stats():
    try:
        doc_count = doc_collection.count()
        skill_count = skill_collection.count()
        
        # Calculate distinct document names
        all_meta = doc_collection.get(include=["metadatas"])["metadatas"] or []
        doc_names = set(m.get("document_name") for m in all_meta if m.get("document_name"))

        # Folder size in MB
        total_bytes = 0
        for root, dirs, files in os.walk(CHROMA_DIR):
            for f in files:
                total_bytes += os.path.getsize(os.path.join(root, f))
        db_size_mb = round(total_bytes / (1024 * 1024), 2)

        return jsonify({
            "status": "success",
            "chunks_count": doc_count,
            "documents_count": len(doc_names),
            "skills_count": skill_count,
            "db_size_mb": db_size_mb,
            "documents": list(doc_names)
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/api/rag/skills/add", methods=["POST"])
def add_skill():
    data = request.get_json(silent=True) or {}
    skill_name = data.get("name")
    vector_text = data.get("vector_text") or skill_name
    complete_text = data.get("complete_text") or ""
    api_key = data.get("api_key") or request.headers.get("X-API-Key")

    is_valid, msg = check_auth(api_key, "write", invoker=data.get("invoker", "agent"))
    if not is_valid:
        return jsonify({"error": msg}), 403

    if not skill_name or not complete_text:
        return jsonify({"error": "Skill name and complete_text required"}), 400

    vector = get_embedding(vector_text)
    skill_id = f"skill_{hashlib.md5(skill_name.encode('utf-8')).hexdigest()}"

    # Upsert skill
    skill_collection.upsert(
        ids=[skill_id],
        embeddings=[vector],
        documents=[complete_text],
        metadatas=[{"skill_name": skill_name, "vector_text": vector_text}]
    )

    log_event(
        invoker=data.get("invoker", "agent"),
        recipient="Vector Store Service",
        event_type="skill_ingest",
        short_desc=f"Added skill '{skill_name}' to skill vector DB",
        req_payload={"name": skill_name, "vector_text": vector_text},
        resp_payload={"status": "stored", "skill_id": skill_id}
    )

    return jsonify({"status": "success", "skill_id": skill_id, "skill_name": skill_name})

@app.route("/api/rag/documents/add", methods=["POST"])
def add_document():
    data = request.get_json(silent=True) or {}
    doc_name = data.get("name")
    complete_text = data.get("complete_text") or ""
    chunk_size = int(data.get("chunk_size", 800))
    overlap = int(data.get("overlap", 100))
    api_key = data.get("api_key") or request.headers.get("X-API-Key")

    is_valid, msg = check_auth(api_key, "write", invoker=data.get("invoker", "agent"))
    if not is_valid:
        return jsonify({"error": msg}), 403

    if not doc_name or not complete_text:
        return jsonify({"error": "Document name and complete_text required"}), 400

    chunks = chunk_text(complete_text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return jsonify({"error": "No valid text chunks generated"}), 400

    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for idx, c in enumerate(chunks):
        c_id = f"doc_{hashlib.md5((doc_name + str(idx) + c[:50]).encode('utf-8')).hexdigest()}"
        vec = get_embedding(c)
        ids.append(c_id)
        embeddings.append(vec)
        documents.append(c)
        metadatas.append({
            "document_name": doc_name,
            "chunk_index": idx,
            "total_chunks": len(chunks),
            "chunk_size": len(c)
        })

    # Ingest in batch into ChromaDB
    doc_collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    log_event(
        invoker=data.get("invoker", "web_ui"),
        recipient="Vector Store Service",
        event_type="document_ingest",
        short_desc=f"Ingested '{doc_name}' ({len(chunks)} chunks)",
        req_payload={"document_name": doc_name, "chunk_size": chunk_size, "overlap": overlap},
        resp_payload={"chunks_created": len(chunks), "characters": len(complete_text)}
    )

    return jsonify({
        "status": "success",
        "document_name": doc_name,
        "chunks_created": len(chunks),
        "total_characters": len(complete_text)
    })

@app.route("/api/rag/query", methods=["POST"])
def query_vector_db():
    data = request.get_json(silent=True) or {}
    db_type = data.get("db_type", "document").lower()  # "document" or "skill"
    query_text = (data.get("query") or data.get("query_text") or "").strip()
    threshold = float(data.get("threshold", 0.2))
    limit = int(data.get("limit", 5))
    conv_id = data.get("conversation_id")
    api_key = data.get("api_key") or request.headers.get("X-API-Key")

    is_valid, msg = check_auth(api_key, "read", invoker=data.get("invoker", "agent"))
    if not is_valid:
        return jsonify({"error": msg}), 403

    if not query_text:
        return jsonify({"results": []})

    q_vector = get_embedding(query_text)
    col = skill_collection if "skill" in db_type else doc_collection

    if col.count() == 0:
        return jsonify({"db_type": db_type, "results": [], "count": 0})

    results = col.query(
        query_embeddings=[q_vector],
        n_results=min(limit * 2, max(col.count(), 1)),
        include=["documents", "metadatas", "distances"]
    )

    matches = []
    docs = results["documents"][0] if results.get("documents") else []
    metas = results["metadatas"][0] if results.get("metadatas") else []
    dists = results["distances"][0] if results.get("distances") else []

    for d, m, dist in zip(docs, metas, dists):
        # Convert cosine distance to similarity score
        similarity = round(max(0.0, 1.0 - dist), 4)
        if similarity >= threshold:
            item = {
                "similarity_score": similarity,
                "text": d,
                "metadata": m
            }
            if "skill" in db_type:
                item["skill_name"] = m.get("skill_name")
            else:
                item["document_name"] = m.get("document_name")
                item["chunk_index"] = m.get("chunk_index")
            matches.append(item)

    # Sort descending by similarity score
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    final_matches = matches[:limit]

    log_event(
        invoker=data.get("invoker", "agent"),
        recipient="Vector Store Service",
        event_type=f"{db_type}_search",
        short_desc=f"Query {db_type} DB: '{query_text[:40]}' ({len(final_matches)} hits)",
        req_payload={"query": query_text, "threshold": threshold, "limit": limit, "db_type": db_type},
        resp_payload={"results_count": len(final_matches), "top_score": final_matches[0]["similarity_score"] if final_matches else 0},
        conv_id=conv_id
    )

    return jsonify({
        "status": "success",
        "db_type": db_type,
        "count": len(final_matches),
        "results": final_matches
    })

@app.route("/api/rag/documents/<path:doc_name>", methods=["DELETE"])
def delete_document(doc_name):
    api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
    is_valid, msg = check_auth(api_key, "write", invoker="web_ui")
    if not is_valid:
        return jsonify({"error": msg}), 403

    # Find IDs for this document
    all_data = doc_collection.get(include=["metadatas"])
    ids_to_del = []
    if all_data.get("ids") and all_data.get("metadatas"):
        for i, m in zip(all_data["ids"], all_data["metadatas"]):
            if m.get("document_name") == doc_name:
                ids_to_del.append(i)

    if ids_to_del:
        doc_collection.delete(ids=ids_to_del)

    log_event(
        invoker="web_ui",
        recipient="Vector Store Service",
        event_type="document_delete",
        short_desc=f"Deleted document '{doc_name}' ({len(ids_to_del)} chunks removed)",
        req_payload={"document_name": doc_name},
        resp_payload={"deleted_chunks": len(ids_to_del)}
    )

    return jsonify({"status": "success", "deleted_chunks": len(ids_to_del)})

@app.route("/api/rag/reset", methods=["POST"])
def reset_database():
    api_key = request.headers.get("X-API-Key") or (request.get_json(silent=True) or {}).get("api_key")
    is_valid, msg = check_auth(api_key, "admin", invoker="web_ui")
    if not is_valid:
        return jsonify({"error": msg}), 403

    global doc_collection
    try:
        chroma_client.delete_collection("documents")
    except Exception:
        pass
    doc_collection = chroma_client.get_or_create_collection(name="documents", metadata={"hnsw:space": "cosine"})

    log_event(
        invoker="web_ui",
        recipient="Vector Store Service",
        event_type="database_reset",
        short_desc="Reset document vector database",
        req_payload={},
        resp_payload={"status": "reset_complete"}
    )

    return jsonify({"status": "success", "message": "Documents database reset complete"})

# FastMCP SSE Transport Endpoints
@app.route("/sse", methods=["GET"])
def sse():
    def stream():
        yield "event: endpoint\ndata: /messages\n\n"
        while True:
            time.sleep(15)
            yield ": keepalive\n\n"
    return Response(stream(), mimetype="text/event-stream")

@app.route("/messages", methods=["POST"])
def messages():
    data = request.get_json(silent=True) or {}
    method = data.get("method")
    params = data.get("params", {})
    req_id = data.get("id", 1)

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if tool_name == "query_vector_db":
            res = query_vector_db().get_json()
            return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res)}]}})

    return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {}})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8003))
    app.run(host="0.0.0.0", port=port)
