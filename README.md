# Agent With RAG (Enterprise Autonomous Architecture)

An enterprise multi-container web application and autonomous AI Agent platform with dynamic Retrieval-Augmented Generation (RAG), FastMCP tool orchestration, ChromaDB vector storage, Ollama local embedding, and comprehensive telemetry/audit logging.

---

## 1. What This System Does

* **Autonomous Multi-Turn Reasoning:** Executes goal-oriented conversational workflows using either a **Custom Agent** (with tool execution loops up to a configurable turn limit) or a **Google ADK Agent** (via Google AI Studio GenAI SDK).
* **Dynamic Skill & Tool Invocation:** Intercepts structured JSON tool calls from LLMs and invokes procedural FastMCP tools (employee registry search, stock market analysis, weather/time lookup, document retrieval).
* **Dual-Collection Vector Store (`doc_RAG`):** Powered by ChromaDB and local Ollama embeddings (`nomic-embed-text`, `bge-m3`) across two isolated collections:
  * `skill`: Semantic discovery and prompt augmentation for procedural skills.
  * `document`: High-precision chunked semantic document retrieval.
* **Granular Authentication & RBAC (`auth_service`):** SQLite-backed credential and API key management with role-based access control (`Admin`, `Editor`, `User`), token expiration, and inter-container permission scoping.
* **Real-Time Container Topology (`Container Mgr`):** Visual interactive system architecture diagram with live CPU/RAM metrics, health status, and administrative container lifecycle operations (`Start`, `Stop`, `Restart`, `Shutdown All`).
* **Comprehensive Telemetry & Audit Logs (`logging`):** Centralized append-only JSON logging capturing full raw payloads, latency distributions (TTFT, ITL, TPS, TPOT), and user conversation histories.

---

## 2. Architecture & Container Port Assignments

The platform runs as 7 decoupled microservices orchestrated via Docker Compose:

| Service | Directory | TCP Port | Protocol | Purpose |
|---|---|---|---|---|
| **Web UI** | `web_ui/` | **8000** | HTTP / Flask | 6-Page responsive web interface & Docker orchestrator |
| **Auth Service** | `auth_service/` | **8001** | HTTP REST | SQLite authentication, user accounts, and API keys |
| **Agents** | `agents/` | **8002** | FastMCP (async HTTP) | Custom & Google ADK Agent multi-turn reasoning loops |
| **Doc & Skills RAG** | `doc_RAG/` | **8003** | FastMCP (async HTTP) | ChromaDB dual collections & chunking pipeline |
| **Ollama Embeddings** | `ollama` | **11434** | REST API | Official Ollama daemon generating dense vector embeddings |
| **Tools** | `tools/` | **8005** | FastMCP (async HTTP) | Employee CSV registry, stock market, and weather tools |
| **Logging** | `logging/` | **8006** | HTTP REST | Centralized audit logs, conversation history, and telemetry |

---

## 3. Installation & Prerequisites

### Prerequisites
* **Docker & Docker Compose:** Docker Engine 24+ and Docker Compose v2.
* **Ollama (Optional for Host Mode):** If running outside Docker, Ollama listening on `127.0.0.1:11434`.
* **Google Gemini API Key:** Required for Gemini model synthesis via Google AI Studio.

### Setup Environment
1. Copy or edit `.env` in the repository root:
   ```bash
   cp .env.example .env
   ```
2. Configure your parameters in `.env`:
   ```ini
   PORT=8000
   GEMINI_API_KEY=your_google_ai_studio_api_key_here
   GEMINI_MODEL=gemma-4-26b-a4b-it
   FLASK_SECRET_KEY=change_this_to_a_secure_random_key
   ```

---

## 4. How to Start All Services

### Using Docker Compose (Recommended Production Mode)
Run the following command from the repository root:
```bash
docker compose up -d --build
```
This automatically builds all 6 custom Python microservices, pulls the official Ollama container, configures isolated network bridges, and mounts host persistence volumes.

### Local Development / Native Mode (Without Docker)
You can also launch each microservice directly in Python:
```bash
# Terminal 1: Logging Container
cd logging && python3 server.py

# Terminal 2: Auth Service
cd auth_service && python3 server.py

# Terminal 3: Tools FastMCP Server
cd tools && python3 server.py

# Terminal 4: Doc & Skills RAG Server
cd doc_RAG && python3 server.py

# Terminal 5: Agents FastMCP Server
cd agents && python3 server.py

# Terminal 6: Web UI
cd web_ui && python3 app.py
```

Access the Web Console at: **`http://localhost:8000`**

---

## 5. How to Shutdown All Services

* **Via the Web UI (Any Page):** Click the light red **🛑 Shutdown** button in the top right header, type `Shutdown the services`, and confirm.
* **Via Container Mgr (Admin Only):** Navigate to the **Container Mgr** tab, click **Shutdown All**, type `Shutdown System`, and confirm.
* **Via Terminal (Docker Compose):**
  ```bash
  docker compose down
  ```

---

## 6. User Guide: Exploring the 6 Console Pages

### Initial Login
1. On opening `http://localhost:8000`, a sign-in modal prompts for credentials.
2. Default initial seed credentials:
   * **Username:** `admin`
   * **Password:** `admin123`
3. Click **Ok** to authenticate and load the main console.

### 🗣️ Page 1: Chat & Knowledge Mgnt
* **Model Selection:** Choose from active Google AI Studio models or select **Custom Model** to specify an OpenAI-compatible endpoint.
* **Hyperparameters:** Tune `Temperature` (0.0–2.0) and `Max Tokens`.
* **Agent Selector:** Toggle between **Custom Agent** and **Google ADK Agent**.
* **Skill Selector:**
  * `Vector Store Selects` (Default): Uses ChromaDB skill matching with configurable `Skill Threshold`.
  * `LLM Selects`: Supplies all skill definitions to the model for cognitive selection.
  * Direct Skill: Forces execution of a designated skill.
* **Inspection Bubbles:** Click **Show Logs** on any completed agent response to expand step-by-step component execution bubbles (Agent, Skills, Tools, RAG, LLM).
* **Retrieved Evidence:** The right card displays semantic chunks retrieved from vector stores matching your query.

### 🛢️ Page 2: VectorDB Mgnt (Editor / Admin Only)
* **Real-time Statistics:** Monitor total ingested document chunks, unique files, and vector DB size in MB.
* **Update Skills Database:** Scans the `skills/` directory and synchronizes new `SKILL.md` definitions into the ChromaDB skill collection.
* **Populate Vector Database:** Enter a URL or local directory path, adjust `Chunk Size` and `Overlap`, and ingest custom files.
* **Storage Status & Reset:** Inspect active document records, delete individual documents, or trigger a full database reset.

### 📊 Page 3: Telemetry
* **Throughput & Velocity Graphs:** Track Request Throughput (prompts, responses, errors) and Token Velocity (input and output tokens) across selectable intervals (1 min, 15 min, 1 hr, 1 day) and ranges.
* **Hardware-Agnostic Latency Metrics:** View calculated Time to First Token (TTFT), Inter-Token Latency (ITL), Tokens Per Second (TPS), and Time Per Output Token (TPOT).

### 📝 Page 4: Audit Logs & Events (Editor / Admin Only)
* **User Conversations Table:** Browse conversation sessions, user queries, agent types, and event counts.
* **Events for Conversation Table:** Select any conversation row to view chronologically sorted event traces.
* **Event Inspector:** Click any event row to open the interactive JSON inspector modal with copyable prompt/response payloads.

### 🚢 Page 5: Container Mgr (Admin Only)
* **Visual Topology Canvas:** Live drawing illustrating container interconnectivity and runtime state (light green for active, light red for stopped).
* **Interactive Node Control:** Click or right-click any container node to inspect port mappings, dependencies, and trigger `Start` or `Stop`.
* **Global Controls:** Use `Restart All` or `Shutdown All` for bulk orchestration.

### 🔑 Page 6: Passwords & API Keys
* **Current Account Info:** View your active email, assigned role, and SQLite storage backend path.
* **Passwords Sub-Tab (Admin Only):** Manage users, update role permissions (`Admin`, `Editor`, `User`), trigger password resets, and view user request activity logs.
* **API Keys Sub-Tab (Admin Only):** Generate new cryptographically secure API keys scoped to specific containers and access levels (`Read`, `Write`, `Admin`) with automatic 1-year expiration. Edit, delete, or revoke keys at any time.

---

## 7. Sample Skills and Tools Included

1. **`time-weather-skill`:** Real-time weather and local time lookup for any city worldwide using the free Open-Meteo public service.
2. **`person-information-skill`:** Employee registry lookups across 30 records (`tools/data/employee_database.csv`) by name, city, country, or job title.
3. **`stock-market-skill`:** Real-time stock queries for top percentage gainers, losers, or equity quotes.
4. **`document-search-skill`:** Vector search for top-$k$ text chunks from the ingested ChromaDB knowledge store.
