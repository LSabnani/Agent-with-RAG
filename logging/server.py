import os
import json
import time
import re
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify

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

LOG_DIR = os.environ.get("LOG_DIR", os.path.join(os.path.dirname(__file__), "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "log.json")

def redact_api_keys(data):
    """Recursively redact API keys from data."""
    if isinstance(data, str):
        # Redact common key patterns
        redacted = re.sub(r'(AIzaSy[0-9A-Za-z-_]{33})', '****', data)
        redacted = re.sub(r'(sk-[0-9A-Za-z-_]{20,})', '****', redacted)
        redacted = re.sub(r'(key-[0-9a-fA-F]{32})', '****', redacted)
        return redacted
    elif isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if any(term in k.lower() for term in ["api_key", "apikey", "secret", "password"]):
                new_dict[k] = "****"
            else:
                new_dict[k] = redact_api_keys(v)
        return new_dict
    elif isinstance(data, list):
        return [redact_api_keys(item) for item in data]
    return data

def extract_metadata_from_payload(payload):
    dur = 0
    model = ""
    in_tok = 0
    out_tok = 0
    if isinstance(payload, dict):
        resp = payload.get("response", {})
        req = payload.get("request", {})

        # duration
        if isinstance(resp, dict) and resp.get("duration_ms"):
            dur = resp.get("duration_ms", 0)
        elif payload.get("duration_ms"):
            dur = payload.get("duration_ms", 0)
        elif payload.get("elapsed_ms"):
            dur = payload.get("elapsed_ms", 0)
        elif payload.get("latency_ms"):
            dur = payload.get("latency_ms", 0)

        # model
        if isinstance(req, dict) and req.get("model_used"):
            model = req.get("model_used")
        elif isinstance(req, dict) and req.get("model"):
            model = req.get("model")
        elif payload.get("model"):
            model = payload.get("model")
        elif payload.get("model_used"):
            model = payload.get("model_used")

        # tokens
        tok = payload.get("token_usage") or (isinstance(resp, dict) and resp.get("token_usage")) or {}
        if isinstance(tok, dict):
            in_tok = tok.get("prompt_tokens", 0) or tok.get("input_tokens", 0)
            out_tok = tok.get("completion_tokens", 0) or tok.get("output_tokens", 0)
        if not in_tok and payload.get("input_tokens"):
            in_tok = payload.get("input_tokens", 0)
        if not out_tok and payload.get("output_tokens"):
            out_tok = payload.get("output_tokens", 0)

    try:
        dur = int(dur or 0)
    except Exception:
        dur = 0
    try:
        in_tok = int(in_tok or 0)
    except Exception:
        in_tok = 0
    try:
        out_tok = int(out_tok or 0)
    except Exception:
        out_tok = 0

    return dur, str(model or ""), in_tok, out_tok

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            logs = json.loads(content)
            for l in logs:
                if not l.get("duration_ms") or not l.get("model") or not l.get("input_tokens") or not l.get("output_tokens"):
                    dur, m, in_t, out_t = extract_metadata_from_payload(l.get("payload"))
                    if not l.get("duration_ms") and dur:
                        l["duration_ms"] = dur
                    if not l.get("model") and m:
                        l["model"] = m
                    if not l.get("input_tokens") and in_t:
                        l["input_tokens"] = in_t
                    if not l.get("output_tokens") and out_t:
                        l["output_tokens"] = out_t
            return logs
    except Exception as e:
        print(f"Error reading log file: {e}")
        return []

def save_logs(logs):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "logging", "port": 8006})

@app.route("/api/logs", methods=["POST"])
def ingest_log():
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "No log payload provided"}), 400

    payload = redact_api_keys(data.get("payload", {}))
    p_dur, p_model, p_in_tok, p_out_tok = extract_metadata_from_payload(payload)

    duration_ms = data.get("duration_ms") or p_dur or 0
    model = data.get("model") or p_model or ""
    input_tokens = data.get("input_tokens") or p_in_tok or 0
    output_tokens = data.get("output_tokens") or p_out_tok or 0

    log_entry = {
        "id": f"log_{int(time.time() * 1000)}_{os.urandom(2).hex()}",
        "timestamp": data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "type": data.get("type", "generic"),
        "invoker": data.get("invoker", "unknown"),
        "recipient": data.get("recipient", "unknown"),
        "conversation_id": data.get("conversation_id"),
        "short_description": data.get("short_description", ""),
        "payload": payload,
        "status": data.get("status", "success"),
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model": model,
        "is_error": bool(data.get("is_error", False))
    }

    logs = load_logs()
    logs.append(log_entry)
    save_logs(logs)

    return jsonify({"status": "success", "log_id": log_entry["id"]}), 201

@app.route("/api/logs/query", methods=["POST", "GET"])
def query_logs():
    criteria = request.get_json(silent=True) if request.method == "POST" else request.args.to_dict()
    criteria = criteria or {}

    logs = load_logs()
    filtered = []

    entity = criteria.get("entity")
    conv_id = criteria.get("conversation_id")
    event_type = criteria.get("type")
    start_date = criteria.get("start_date")
    end_date = criteria.get("end_date")
    model = criteria.get("model")

    for l in logs:
        if entity and (l.get("invoker") != entity and l.get("recipient") != entity):
            continue
        if conv_id and l.get("conversation_id") != conv_id:
            continue
        if event_type and l.get("type") != event_type:
            continue
        if model and l.get("model") != model:
            continue
        if start_date and l.get("timestamp") < start_date:
            continue
        if end_date and l.get("timestamp") > end_date:
            continue
        filtered.append(l)

    limit = int(criteria.get("limit", len(filtered)))
    return jsonify({"count": len(filtered[:limit]), "logs": filtered[:limit]})

@app.route("/api/logs/stats", methods=["GET"])
def get_stats():
    logs = load_logs()
    file_size_bytes = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0

    per_entity = {}
    for l in logs:
        inv = l.get("invoker", "unknown")
        rec = l.get("recipient", "unknown")
        per_entity[inv] = per_entity.get(inv, 0) + 1
        if rec != "unknown" and rec != inv:
            per_entity[rec] = per_entity.get(rec, 0) + 1

    return jsonify({
        "total_logs": len(logs),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 3),
        "per_entity": per_entity
    })

@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    save_logs([])
    return jsonify({"status": "cleared", "total_logs": 0})

@app.route("/api/conversations", methods=["GET"])
@app.route("/api/logs", methods=["GET"])
def list_conversations():
    logs = load_logs()
    conversations = {}

    for l in logs:
        cid = l.get("conversation_id")
        if not cid:
            continue
        if cid not in conversations:
            conversations[cid] = {
                "conversation_id": cid,
                "first_seen": l.get("timestamp"),
                "last_seen": l.get("timestamp"),
                "timestamp": l.get("timestamp"),
                "user_query": "",
                "agent_response": "",
                "agent_type": "Custom Agent",
                "events_count": 0,
                "event_count": 0,
                "model": l.get("model", "")
            }
        conv = conversations[cid]
        conv["events_count"] += 1
        conv["event_count"] = conv["events_count"]
        conv["last_seen"] = max(conv["last_seen"], l.get("timestamp") or "")
        conv["timestamp"] = conv["last_seen"]
        if l.get("model") and not conv["model"]:
            conv["model"] = l.get("model")

        # Extract user query or agent response if logged
        if l.get("type") in ["chat_request", "user_query"]:
            payload = l.get("payload", {})
            if isinstance(payload, dict):
                conv["user_query"] = payload.get("message") or payload.get("query") or conv["user_query"]
                conv["agent_type"] = payload.get("agent_type") or conv["agent_type"]
        elif l.get("type") in ["chat_response", "agent_response"]:
            payload = l.get("payload", {})
            if isinstance(payload, dict):
                conv["agent_response"] = payload.get("response") or conv["agent_response"]

    result = list(conversations.values())
    result.sort(key=lambda x: x["last_seen"], reverse=True)

    # Compute statistics for Log Viewer Header Pill
    total_prompts = sum(1 for l in logs if l.get("type") in ["chat_request", "prompt", "llm_request", "user_query"])
    total_model_calls = sum(1 for l in logs if l.get("type") in ["llm_invocation", "llm_response", "llm_request"] or l.get("recipient") in ["LLM", "Custom LLM"] or l.get("invoker") in ["LLM", "Custom LLM"])
    total_ollama_embeds = sum(1 for l in logs if l.get("type") == "embedding_query" or l.get("recipient") in ["Embedding", "Embedding Service"])
    latencies = [l.get("duration_ms", 0) for l in logs if (l.get("duration_ms") or 0) > 0 and l.get("type") in ["llm_response", "chat_response", "embedding_query"]]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

    statistics = {
        "total_user_prompts": total_prompts,
        "total_model_calls": total_model_calls,
        "total_ollama_embeds": total_ollama_embeds,
        "avg_latency_ms": avg_latency
    }

    return jsonify({
        "conversations": result,
        "statistics": statistics
    })

@app.route("/api/conversations/<conversation_id>/events", methods=["GET"])
def conversation_events(conversation_id):
    logs = load_logs()
    events = [l for l in logs if l.get("conversation_id") == conversation_id]
    events.sort(key=lambda x: x.get("timestamp", ""))
    enriched = []
    for l in events:
        e = dict(l)
        e["event_type"] = l.get("type", "generic")
        e["target"] = l.get("recipient", "unknown")
        e["local_time"] = l.get("timestamp", "")
        e["elapsed_ms"] = l.get("duration_ms", 0)
        enriched.append(e)
    return jsonify({"conversation_id": conversation_id, "events": enriched})

@app.route("/api/logs/telemetry", methods=["GET"])
def get_telemetry():
    model_filter = request.args.get("model")
    raw_interval = (request.args.get("interval") or "15m").strip().lower()
    raw_range = (request.args.get("range") or request.args.get("time_range") or "1d").strip().lower()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Normalize interval
    if "1 min" in raw_interval or "1m" in raw_interval:
        bucket_seconds = 60
    elif "15 min" in raw_interval or "15m" in raw_interval:
        bucket_seconds = 900
    elif "1 hr" in raw_interval or "1h" in raw_interval or "hour" in raw_interval:
        bucket_seconds = 3600
    elif "1 day" in raw_interval or "1d" in raw_interval or "day" in raw_interval:
        bucket_seconds = 86400
    else:
        bucket_seconds = 900

    logs = load_logs()

    # Determine time bounds
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)
    if "last hr" in raw_range or "1h" in raw_range or "hour" in raw_range:
        cutoff = now - timedelta(hours=1)
    elif "1 day" in raw_range or "1d" in raw_range or "day" in raw_range:
        cutoff = now - timedelta(days=1)
    elif "week" in raw_range or "7d" in raw_range:
        cutoff = now - timedelta(days=7)
    elif "month" in raw_range or "30d" in raw_range:
        cutoff = now - timedelta(days=30)
    elif "custom" in raw_range and start_date:
        try:
            cutoff = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except Exception:
            pass

    # Filter logs
    relevant = []
    models_used = set()
    total_prompts = 0
    total_responses = 0
    total_errors = 0
    total_input_tokens = 0
    total_output_tokens = 0
    latencies = []

    for l in logs:
        m = l.get("model")
        if m:
            models_used.add(m)
        if model_filter and model_filter != "All Models" and m != model_filter:
            continue

        ts_str = l.get("timestamp")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts < cutoff:
                continue
            if end_date and ts > datetime.fromisoformat(end_date.replace("Z", "+00:00")):
                continue
        except Exception:
            pass

        relevant.append(l)

        # Counting
        l_type = l.get("type", "")
        if l_type in ["chat_request", "prompt", "llm_request", "user_query"]:
            total_prompts += 1
        elif l_type in ["chat_response", "llm_response", "agent_response"]:
            total_responses += 1

        if l.get("is_error") or l.get("status") in ["error", "failure"]:
            total_errors += 1

        in_tok = l.get("input_tokens", 0)
        out_tok = l.get("output_tokens", 0)
        total_input_tokens += in_tok
        total_output_tokens += out_tok

        dur = l.get("duration_ms", 0)
        if dur > 0 and (l_type in ["llm_response", "chat_response", "embedding_query"] or l.get("recipient") in ["LLM", "Custom LLM"] or l.get("invoker") in ["LLM", "Custom LLM"]):
            latencies.append(dur)

    # Calculate throughput / token velocity timeline points aggregated into buckets
    buckets = {}
    for l in relevant:
        try:
            ts = datetime.fromisoformat(l.get("timestamp").replace("Z", "+00:00"))
            epoch = int(ts.timestamp())
            b_epoch = epoch - (epoch % bucket_seconds)
            b_key = datetime.fromtimestamp(b_epoch, timezone.utc).strftime("%H:%M" if bucket_seconds < 86400 else "%m-%d")

            if b_key not in buckets:
                buckets[b_key] = {"prompts": 0, "responses": 0, "errors": 0, "input_tokens": 0, "output_tokens": 0}

            lt = l.get("type", "")
            if lt in ["chat_request", "prompt", "llm_request", "user_query"]:
                buckets[b_key]["prompts"] += 1
            elif lt in ["chat_response", "llm_response", "agent_response"]:
                buckets[b_key]["responses"] += 1
            if l.get("is_error") or l.get("status") in ["error", "failure"]:
                buckets[b_key]["errors"] += 1

            buckets[b_key]["input_tokens"] += (l.get("input_tokens") or 0)
            buckets[b_key]["output_tokens"] += (l.get("output_tokens") or 0)
        except Exception:
            continue

    timeline = [{"time": k, **v} for k, v in sorted(buckets.items())]

    charts = {
        "labels": [b["time"] for b in timeline],
        "prompts": [b["prompts"] for b in timeline],
        "responses": [b["responses"] for b in timeline],
        "errors": [b["errors"] for b in timeline],
        "input_tokens": [b["input_tokens"] for b in timeline],
        "output_tokens": [b["output_tokens"] for b in timeline]
    }

    summary = {
        "total_prompts": total_prompts,
        "total_responses": total_responses,
        "total_errors": total_errors,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens
    }

    # Metrics: TTFT, ITL, TPS, TPOT
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0
    tps = round(total_output_tokens / (sum(latencies) / 1000), 2) if (latencies and sum(latencies) > 0) else 0
    tpot = round((sum(latencies) / total_output_tokens), 2) if total_output_tokens > 0 else 0
    ttft = round(avg_latency * 0.35, 1)  # Estimated TTFT based on avg latency
    itl = round(tpot * 0.8, 1)

    performance = {
        "avg_latency_ms": round(avg_latency, 1),
        "ttft_ms": ttft,
        "itl_ms": itl,
        "tps": tps,
        "tpot_ms": tpot
    }

    return jsonify({
        "used_models": sorted(list(models_used)),
        "models_used": sorted(list(models_used)),
        "summary": summary,
        "total_prompts": total_prompts,
        "total_responses": total_responses,
        "total_errors": total_errors,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "performance": performance,
        "metrics": performance,
        "charts": charts,
        "timeline": timeline
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8006))
    app.run(host="0.0.0.0", port=port)
