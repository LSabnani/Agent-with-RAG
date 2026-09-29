# Agent With RAG — System Specification V2.0 (`SPECIFICATIONS_GEN.md`)

Comprehensive system engineering specification for recreating the **Agent with RAG** multi-service autonomous agent platform. This document specifies the complete architecture, data models, inter-service API contracts, GUI behaviors, security mechanisms, seed data, and deployment configurations so that an independent developer or automated IDE agent can recreate the system from scratch.

---

## 1. System Overview & Architecture

### 1.1 Objective
The system is an enterprise-grade, microservice-based AI Agent platform equipped with Retrieval-Augmented Generation (RAG), autonomous multi-turn tool execution, real-time telemetry, forensic audit logging, container lifecycle control, and role-based access management (RBAC).

### 1.2 Microservice Mesh & Network Topology
The system consists of 7 isolated Docker containers communicating across an internal Docker bridge network (`agent-network`):

| Container Name | Service Role | Port | Base Framework / Image | Storage / Persistence |
| :--- | :--- | :--- | :--- | :--- |
| `web_ui` | Unified Web Dashboard & API Gateway | `8000` | Python 3.11 / Flask | `./web_ui/secrets`, Docker socket |
| `auth_service` | Authentication, RBAC & Key Authority | `8001` | Python 3.11 / Flask + SQLite | `./auth_service/secrets/auth.db` |
| `agents` | Custom Agent & Google ADK Microservice | `8002` | Python 3.11 / Flask + Google GenAI | `./agents/secrets`, `./agents/skills` |
| `doc_rag` | ChromaDB Vector Store & RAG Engine | `8003` | Python 3.11 / Flask + FastMCP | `./doc_RAG/chroma`, `./doc_RAG/secrets` |
| `tools` | Procedural Tools Execution Engine | `8005` | Python 3.11 / Flask + FastMCP | `./tools/data`, `./tools/secrets` |
| `logging` | Central Logging & Telemetry Engine | `8006` | Python 3.11 / Flask | `./logging/logs/log.json` |
| `ollama` | Local High-Dimensional Vector Embedder | `11434` | `ollama/ollama:latest` | Host `~/.ollama` volume |

```
                              ┌────────────────────────────────────────┐
                              │          Client Browser               │
                              └──────────────────┬─────────────────────┘
                                                 │ HTTP / JSON
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Web UI Gateway (`web_ui`, Port 8000)                                                        │
│ ├─ Chat & Knowledge Mgnt ├─ VectorDB Mgnt ├─ Telemetry ├─ Audit Logs ├─ Containers ├─ Auth │
└────────┬───────────────────────┬──────────────────────┬──────────────────────┬──────────────┘
         │                       │                      │                      │
         ▼                       ▼                      ▼                      ▼
┌─────────────────┐     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Agents Service  │     │ Vector Store    │    │ Auth Service    │    │ Logging Service │
│ (`agents`, 8002)│◄───►│ (`doc_rag`,8003)│◄──►│ (`auth_service`,│◄──►│ (`logging`,     │
│                 │     │                 │    │  8001)          │    │  8006)          │
└────────┬────────┘     └────────┬────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Tools Service   │     │ Ollama Embedder │
│ (`tools`, 8005) │     │ (`ollama`,11434)│
└─────────────────┘     └─────────────────┘
```

### 1.3 Repository Directory Layout
```text
Agent-with-RAG/
├── agents/                       # Custom & Google ADK agent service
│   ├── custom_agent/             # Autonomous planning orchestrator
│   │   └── custom_agent.py
│   ├── genai/                    # Google ADK agent implementation
│   ├── secrets/                  # Inter-container keys & env configs
│   ├── skills/                   # Discovered domain skills
│   │   ├── time-weather-skill/   # Live time & weather queries
│   │   ├── stock-analysis-skill/ # Financial market gainer/loser queries
│   │   ├── person-information-skill/  # Employee database lookup
│   │   └── document-search-skill/# Vector knowledge base retrieval
│   ├── Dockerfile
│   └── server.py
├── auth_service/                 # Authentication & authorization service
│   ├── secrets/                  # SQLite database (auth.db)
│   ├── Dockerfile
│   └── server.py
├── doc_RAG/                      # Vector store & RAG service
│   ├── chroma/                   # ChromaDB persistent directory
│   ├── secrets/                  # Keys & authorization storage
│   ├── Dockerfile
│   └── server.py
├── embedding/                    # Embedding service configuration
│   └── secrets/
├── logging/                      # Central logging & telemetry service
│   ├── logs/                     # Persistent event log (log.json)
│   ├── Dockerfile
│   └── server.py
├── tools/                        # Procedural execution tools service
│   ├── data/                     # Seed data (employee_database.csv)
│   ├── secrets/                  # Inter-container keys
│   ├── Dockerfile
│   └── server.py
├── web_ui/                       # Web UI gateway application
│   ├── static/                   # Static CSS, JS, and icons
│   │   ├── css/style.css
│   │   ├── js/app.js
│   │   └── images/
│   ├── templates/                # Jinja2 HTML templates
│   │   └── index.html
│   ├── secrets/                  # Session keys & inter-container keys
│   ├── Dockerfile
│   └── app.py
├── sample_docs/                  # Seed markdown documents (~3000 words each)
│   ├── agentic_rag_overview.md
│   ├── enterprise_marketing_strategy_2026.md
│   └── annual_financial_report_fy2025.md
├── tests/                        # Microservice test suite
│   └── test_microservices.py
├── docker-compose.yml            # Multi-service composition
├── requirements.txt              # Python runtime dependencies
├── README.md                     # System documentation
└── SPECIFICATIONS_GEN.md         # Generated master specification
```

---

## 2. Graphical User Interface (GUI) Specifications

### 2.1 Theme & Design System
- **Theme**: Premium High-Contrast Dark Glassmorphism (`#060a14` base background, `#0f172a` headers, `#1e293b` borders, vivid accent colors: `#38bdf8` sky blue, `#818cf8` indigo, `#10b981` emerald, `#ef4444` rose).
- **Typography**: System sans-serif stack (`Inter`, `system-ui`, `-apple-system`, `sans-serif`) with high contrast white text (`#ffffff` / `#f1f5f9`).
- **Responsive Layout**: App container `.app-content` takes `100%` width of the window (`max-width: 100%; box-sizing: border-box;`) with consistent horizontal padding (`1.5rem`) matching the top application header. Capping width at arbitrary pixel values (e.g. 1700px) is prohibited so that high-resolution screens (1080p, 1440p, 4K) utilize the full screen width.

### 2.2 Global Top Navigation Header
The fixed top bar (`.app-header`, height `64px`) contains:
1. **Left Brand Area**:
   - Application icon: Displays `static/images/app-icon.gif` if present, falling back to `🤖`.
   - Application title: **Agent With RAG**.
2. **Center Navigation Tabs** (6 interactive views):
   - `🗣️ Chat & Knowledge Mgnt`
   - `🛢️ VectorDB Mgnt`
   - `📊 Telemetry`
   - `📝 Log Viewer` (Audit Logs & Events)
   - `🐳 Container Mgr`
   - `🔑 Password & API Mgnt`
3. **Right Action Area**:
   - User identity pill displaying active user email and role badge (`Admin`, `Editor`, or `User`).
   - **Logout** button: Terminates session, records logout in audit log, and displays login modal.
   - **Shutdown** button (light red style `#ef4444`): Opens confirmation modal requiring user to type exact confirmation phrase `Shutdown the services` before enabling the `Confirm` button.

### 2.3 Authentication Modals
- **Startup Condition**: If no valid session exists, display centered glassmorphism Login Modal over dimmed backdrop.
- **Login Modal**:
  - Input fields: Username (Email) and Password.
  - Action buttons:
    - `Ok`: Sends credentials to `/api/auth/login`. On error, displays `Invalid username or password.` If user status is `Locked`, displays `Account is Locked. Please contact the administrator.`
    - `Create New Account`: Opens Account Registration modal.
    - `Cancel`: Displays `Thank you for using the app.` and closes window.
- **Registration Modal**:
  - Input fields: Username and Password.
  - Action buttons: `Cancel` (dismisses) and `Add` (submits to `/api/auth/register` creating account in `Locked` status by default, awaiting admin activation).

---

### 2.4 Tab 1: "Chat & Knowledge Mgnt"
The primary conversational agent and retrieval exploration interface.

#### 2.4.1 Page Sub-Header Controls
Positioned directly below the main navigation:
1. **Max Tokens**: Numeric input (Default: `2048`, Min: `128`, Max: `65536`, Step: `128`).
2. **Temperature**: Numeric input (Default: `0.7`, Min: `0.0`, Max: `2.0`, Step: `0.1`).
3. **Model Selection**: Dropdown populated from Google AI Studio / Gemini API active text models. Default: `GEMINI_MODEL` environment variable (e.g. `gemma-4-26b-a4b-it`).
   - Includes `Custom Model` option. When selected, displays adjacent **Custom API Endpoint** text input (defaults to `http://127.0.0.1:8010/v1/chat/completions`).

#### 2.4.2 Two-Card Split Grid Layout
The page layout uses `.split-cards-grid` with `grid-template-columns: 1fr 1fr; width: 100%;` ensuring **both Left and Right cards are each exactly 50% of the window width**.

```
┌───────────────────────────────────────────────┬───────────────────────────────────────────────┐
│ Left Card: "Chat with the Agent" (50% Width)  │ Right Card: "Context Evidence" (50% Width)    │
├───────────────────────────────────────────────┼───────────────────────────────────────────────┤
│ Header: Agent Selector | Max Turns (Default 3)│ Header: Max RAG Chunks (2,3,5,7,10)|Doc Thresh│
│                                               │ Row 2: Skill Selector | Skill Threshold (0.2) │
│ Chat Messages Scroll Stream                   │ Evidence Chunks & Matched Skills List         │
│ - User Prompts & Agent Syntheses              │ - Similarity Badges & Chunk Text              │
│ - Response Detail Box & "Show Logs" Bubbles   │ - Extracted Tool Results                      │
│                                               │                                               │
│ Chat Input Box + Send Button                  │ Scrollable Evidence Container                 │
└───────────────────────────────────────────────┴───────────────────────────────────────────────┘
```

#### 2.4.3 Left Card: "Chat with the Agent" (50% Window Width)
- **Header Controls**:
  - `Agent` dropdown: Choices are `Custom Agent` (default) and `Google ADK Agent`.
  - `Max Turns` input: Numeric input (Default: `3`, Min: `1`, Max: `10`). Limits autonomous agent reasoning loops.
- **Body Content**:
  - Scrollable conversation history container (`#chatMessages`).
  - Welcome banner with 4 quick prompt chips:
    - `🌤️ Weather in Tokyo`
    - `👤 Lucas Dubois`
    - `📈 Top Gainers`
    - `📚 Agentic RAG`
  - User messages render in right-aligned blue bubbles.
  - Agent responses render in left-aligned dark slate bubbles with markdown formatting.
  - **Collapsible Response Detail Box**:
    - Top-right anchored **Show Logs** toggle button.
    - Summary status bar showing execution time (ms), model used, and token count.
    - Component stage bubbles representing each step:
      - `🤖 Agent`: Autonomous reasoning / plan generation.
      - `⚙️ Tools`: Procedural tool execution and parameters.
      - `📚 RAG`: Vector similarity retrieval and chunk counts.
      - `✨ Skills`: Skill vector match or rule evaluation.
      - `🧠 LLM`: Raw model prompt and response payload.
    - Toggling **Show Logs** expands full JSON payload viewer with syntax styling.
- **Footer**:
  - Auto-resizing textarea for user prompt.
  - Send button (`Enter` to submit, `Shift+Enter` for newline).
  - Sends request to `/api/chat` with newly generated Conversation ID (`conv_<timestamp>`).

#### 2.4.4 Right Card: "Retrieved Context Evidence" (50% Window Width)
- **Header Controls** (`.card-action-group`):
  - `Max RAG Chunks` dropdown: Options are `2`, `3`, `5` (Default), `7`, `10`. Defines maximum context chunks retrieved from vector store.
  - `Doc Threshold` input: Numeric similarity threshold (Default: `0.3`, Min: `0.0`, Max: `1.0`, Step: `0.05`).
- **Second Parameter Row** (`.chat-param-row`):
  - `Skill Selector` dropdown: Options include `Vector Store Selects` (default), `LLM Selects`, and individually discovered skills (`time-weather-skill`, `stock-analysis-skill`, `person-information-skill`, `document-search-skill`).
  - `Skill Threshold` box: Numeric input (Default: `0.2`, Min: `0.0`, Max: `1.0`, Step: `0.05`). Visible when `Vector Store Selects` is active.
- **Body Content**:
  - Lists matched skills with similarity scores and rationale.
  - Displays retrieved document chunks with similarity score badges (`XX.X% match`), source document filename, chunk index, and complete chunk text.
  - Updates dynamically following every chat response from agent execution trace logs.

---

### 2.5 Tab 2: "VectorDB Mgnt"
Management console for the ChromaDB vector database and embedding engine.

#### 2.5.1 Left Card: "Populate Vector Database" (50% Width)
- Ingest input field accepting either a public web URL (e.g., `https://...`) or local directory/file path (e.g., `sample_docs/agentic_rag_overview.md`).
- 5 Quick Sample Document buttons for instant ingestion.
- Collapsible **Advanced Chunking Parameters** sub-card:
  - `Chunk Size`: Character count per chunk (Default: `800`, Min: `100`, Max: `5000`).
  - `Chunk Overlap`: Character overlap between adjacent chunks (Default: `100`, Min: `0`, Max: `1000`).
- **Populate Vector Database** submit button: Dispatches ingestion job to `/api/vectordb/ingest`. Shows progress spinner and chunk creation summary upon completion.

#### 2.5.2 Right Card: "Vector Storage Status" (50% Width)
- Header includes **Reset DB** button (clears all document vectors after confirmation).
- Ingestion status banner indicating whether indexing is active or idle.
- Ingested Documents Table:
  - Columns: Document Name, Chunks Count, Total Characters, Ingestion Date, Actions (`Delete` button).
  - Deleting a document removes all associated chunk vectors from ChromaDB via `/api/vectordb/document`.
- Loaded Skills Section:
  - Lists all domain skills registered in the vector store with status badges.

#### 2.5.3 Bottom Card: "Available Embedding Models" (Full Width)
- Displays catalog table of embedding models supported by Ollama:
  - Columns: Model Name, Dimensions, Context Window, File Size, Description, Status (`Active`, `Installed`, or `Available to Pull`).
  - **Change Active Model** button: Opens modal allowing admin to switch the active model (e.g. `bge-large:latest`, `nomic-embed-text:latest`). Switching models automatically wipes incompatible document vectors and triggers re-indexing of skills.

---

### 2.6 Tab 3: "Telemetry"
Live operational analytics and token velocity monitoring.

#### 2.6.1 Filter Bar
- **Model Selector**: Dropdown listing `All Models` (default) plus all distinct models logged in the system.
- **Aggregation Interval**: Choices: `1 min`, `15 min` (default), `1 hr`, `1 day`.
- **Time Range**: Choices: `Last hr`, `1 day` (default), `Week`, `Month`, and `Custom` (reveals Start Date and End Date calendar pickers).
- **Refresh Telemetry** button: Triggers on-demand re-aggregation.

#### 2.6.2 Top KPI Cards
- `Total Prompts`: Count of user requests processed.
- `Total Responses`: Count of agent synthesis responses returned.
- `Total Errors`: Total failed invocations or HTTP errors.
- `Total Input Tokens`: Cumulative prompt tokens consumed.
- `Total Output Tokens`: Cumulative completion tokens generated.

#### 2.6.3 Top Card: "System Throughput & Token Velocity"
Contains two interactive responsive timeline charts rendered with **local time** coordinates:
1. **Left Chart (Throughput)**: Multi-line chart tracking Prompts, Responses, and Errors per interval.
2. **Right Chart (Token Velocity)**: Multi-line chart tracking Input Tokens and Output Tokens per interval.
- **Timezone Handling**:
  - The client provides `tz_offset = new Date().getTimezoneOffset()` in API parameters.
  - Bucket boundaries are computed in the user's local timezone so day and hour buckets align to the local day and hour.
  - X-axis labels render in local time (`HH:MM` for minute/hour intervals, `MM-DD` for daily intervals).
  - Hover tooltips display the full local date and time (`YYYY-MM-DD HH:mm:ss`).

#### 2.6.4 Bottom Card: "Inference Performance & Latency Telemetry"
Displays computed generative AI performance telemetry:
- **Average Latency**: Mean end-to-end turn time (ms).
- **Time to First Token (TTFT)**: Estimated initial latency (ms).
- **Inter-Token Latency (ITL)**: Mean time between subsequent tokens (ms).
- **Tokens Per Second (TPS)**: Generation throughput rate.
- **Time Per Output Token (TPOT)**: Milliseconds required per generated output token.

---

### 2.7 Tab 4: "Audit Logs & Events" (Log Viewer)
Forensic auditing interface for inspecting raw messages and inter-container communication.

#### 2.7.1 Top Table: "User Conversations"
- Lists all user interaction sessions chronologically.
- Columns: `Timestamp (Local)`, `Conversation ID`, `User Query`, `Agent Response`, `Agent Type`, `Events Count`.
- All timestamps render in the client's **local time** format (`YYYY-MM-DD HH:mm:ss`).
- Aggregate Statistics Pills: `Total Prompts`, `Model Calls`, `Ollama Embeds`, `Avg Latency (ms)`.
- **Clear All Logs** button: Truncates `log.json` and resets statistics after user confirmation.
- Selecting any row highlights it and filters the Bottom Table for that Conversation ID.

#### 2.7.2 Bottom Table: "Events for Conversation <Conversation ID>"
- Chronological breakdown of every microservice hop and LLM interaction for the selected conversation.
- Columns: `Time & Date (Local)`, `Event Type`, `Invoker`, `Target / Recipient`, `Elapsed Time (ms)`, `Actions`.
- All timestamps render in the client's **local time** format (`YYYY-MM-DD HH:mm:ss`).
- Actions column provides **View Payload** button:
  - Opens modal displaying complete, untruncated JSON request and response payloads.
  - Modal metadata header displays `Time (Local)` in formatted local time.
  - API keys and sensitive tokens are automatically redacted (`****`).

---

### 2.8 Tab 5: "Container Mgr"
Direct container health inspection and inter-container key configuration via Docker socket.

#### 2.8.1 Containers Table
- Displays all 7 mesh containers (`web_ui`, `auth_service`, `agents`, `doc_rag`, `tools`, `logging`, `ollama`).
- Columns: `Container Name`, `Image`, `Status` (with color-coded badge: green `running`, red `exited`), `CPU %`, `Memory Usage / Limit`, `Actions`.
- Action buttons per container: `Start`, `Stop`, `Restart`, and `Configure Keys`.

#### 2.8.2 Inter-Container Key Configuration Modal
- Clicking **Configure Keys** reads `<container>/secrets/keys` for the selected container.
- Displays key mappings (`<target_container>=<api_key>`).
- Allows editing and saving keys. Saving writes directly to the container's mounted `secrets/keys` volume file on the host.

---

### 2.9 Tab 6: "Password & API Mgnt"
Security administration interface with two sub-tabs:

#### 2.9.1 Sub-Tab A: "User Accounts"
- User accounts table:
  - Columns: `Username / Email`, `Role` (`Admin`, `Editor`, `User`), `Status` (`Active`, `Locked`), `Created Date`, `Actions`.
  - Actions: Toggle Status (`Lock` / `Unlock`), Change Role, Reset Password, Delete User.
- **Add New User** button: Opens modal to create account with initial status `Active` or `Locked`.
- User Activity Log table: Historical audit log of logins, logouts, password resets, and account updates.

#### 2.9.2 Sub-Tab B: "API Keys"
- Table Header Controls:
  - **Select All Checkbox**: Selects or deselects all visible API key rows.
  - **Delete Selected API Keys Button**:
    - Active when one or more keys are checked.
    - Opens confirmation modal displaying the list of all selected key names and prefixes.
    - Modal layout: **Cancel** button at bottom-left, **Delete** button at bottom-right.
  - **Generate New API Key Button**:
    - Opens creation modal.
    - Fields: Key Name (text), Container Scope checkboxes (`tools`, `doc_rag`, `agents`, `logging`), Access Level dropdown (`Read`, `Write`, `Admin`), Expiration Date picker (defaults to 1 year from creation).
    - Submitting generates a cryptographically secure key formatted as `key-<16 hex chars>` and adds it to SQLite storage.
- API Keys Table:
  - Columns: `[ ]` (Checkbox), `Key Name`, `API Key` (masked as `key-xxxx...xxxx`), `Container Scopes`, `Access Level`, `Created Date`, `Expires At`, `Status`, `Actions` (`Edit`, `Delete`).

---

## 3. Microservice Specifications & API Reference

### 3.1 Authentication & Authorization Service (`auth_service`, Port 8001)

#### 3.1.1 Database Schema (SQLite: `auth.db`)
- `users`: `id INTEGER PRIMARY KEY`, `email TEXT UNIQUE`, `password_hash TEXT`, `role TEXT DEFAULT 'User'`, `status TEXT DEFAULT 'Active'`, `created_at TEXT`.
- `api_keys`: `id INTEGER PRIMARY KEY`, `key_name TEXT`, `api_key TEXT UNIQUE`, `creator_email TEXT`, `containers TEXT` (JSON array), `access_levels TEXT` (JSON array), `status TEXT DEFAULT 'Active'`, `created_at TEXT`, `expires_at TEXT`.
- `activity_logs`: `id INTEGER PRIMARY KEY`, `timestamp TEXT`, `username TEXT`, `action TEXT`, `ip_address TEXT`, `details TEXT`.

#### 3.1.2 Endpoints Contract
- `GET /health` -> `{"status": "ok", "service": "auth_service", "port": 8001}`
- `POST /api/auth/login`
  - Body: `{"username": "<email>", "password": "<password>", "ip_address": "<ip>"}`
  - Returns `200` with user object, or `401` (`Invalid username or password`), or `403` (`Account is Locked. Please contact the administrator.`).
- `POST /api/auth/register`
  - Body: `{"username": "<email>", "password": "<password>", "ip_address": "<ip>"}`
  - Returns `201` creating user with status `Locked`.
- `POST /api/auth/validate_key`
  - Validates inter-container API key.
  - Body: `{"api_key": "<key>", "container": "<target_container>", "access_level": "<read|write|admin>", "invoker": "<source_container>"}`
  - Returns `200`: `{"valid": true|false, "key_name": "...", "access_level": "...", "containers": [...]}`
- `GET /api/users` -> Lists all users. Admin only.
- `PUT /api/users/<id>/status` -> Body: `{"status": "Active"|"Locked"}`.
- `PUT /api/users/<id>/role` -> Body: `{"role": "Admin"|"Editor"|"User"}`.
- `POST /api/users/<id>/reset_password` -> Body: `{"password": "<new_pass>"}`.
- `DELETE /api/users/<id>` -> Deletes user.
- `GET /api/keys` -> Lists all API keys.
- `POST /api/keys` -> Creates new API key (`key-<hex>`). Returns `201`.
- `DELETE /api/keys/<id>` -> Deletes single key.
- `POST /api/keys/bulk_delete` -> Body: `{"key_ids": [1, 2, ...]}`. Bulk deletes specified keys.

---

### 3.2 Agents Service (`agents`, Port 8002)

#### 3.2.1 Responsibilities
Executes multi-turn autonomous reasoning, tool selection, skill matching, and synthesis using either the **Custom Autonomous Agent** or **Google ADK Agent**.

#### 3.2.2 Endpoints Contract
- `GET /health` -> `{"status": "ok", "service": "agents", "port": 8002}`
- `GET /api/agents/models`
  - Queries Google AI Studio / Gemini API using `GEMINI_API_KEY` for active text generation models.
  - Returns: `{"models": [{"id": "...", "name": "...", "input_token_limit": ..., "output_token_limit": ...}], "default": "gemma-4-26b-a4b-it"}`
- `GET /api/agents/skills`
  - Discovers domain skills in `agents/skills/*/SKILL.md`.
  - Returns: `{"skills": [{"name": "...", "description": "...", "trigger_queries": [...]}]}`
- `POST /api/agent/chat`
  - Dispatches chat query through agent execution loop.
  - Request Body:
    ```json
    {
      "message": "User query string",
      "conversation_id": "conv_1790000000",
      "agent_type": "Custom Agent" | "Google ADK Agent",
      "model": "gemma-4-26b-a4b-it",
      "temperature": 0.7,
      "max_tokens": 2048,
      "max_turns": 3,
      "skill_selector": "Vector Store Selects" | "LLM Selects" | "<skill_name>",
      "skill_threshold": 0.2,
      "doc_threshold": 0.3,
      "max_chunks": 5,
      "api_key": "<agent_api_key>"
    }
    ```
  - Response Body:
    ```json
    {
      "status": "success",
      "response": "Final synthesized answer",
      "conversation_id": "conv_1790000000",
      "agent_type": "Custom Agent",
      "model": "gemma-4-26b-a4b-it",
      "duration_ms": 1420,
      "steps": [
        {
          "step": 1,
          "component": "Agent",
          "action": "Plan Generation",
          "duration_ms": 310,
          "payload": { ... }
        }
      ],
      "evidence": {
        "skills": [ { "name": "...", "similarity_score": 0.85 } ],
        "documents": [ { "name": "...", "chunk_text": "...", "similarity_score": 0.74 } ]
      }
    }
    ```

---

### 3.3 Vector Store Service (`doc_RAG`, Port 8003)

#### 3.3.1 Responsibilities
Manages persistent ChromaDB vector store collections for `documents` and `skills`, performs text chunking, orchestrates vector generation via `ollama`, and executes similarity queries.

#### 3.3.2 Endpoints Contract
- `GET /health` -> `{"status": "ok", "service": "doc_rag", "port": 8003}`
- `GET /api/rag/list` (or `/api/rag/stats`)
  - Returns document and skill counts, chunk totals, and storage size in megabytes:
    `{"status": "success", "count_documents": 3, "count_skills": 4, "chunks_count": 42, "db_size_mb": 1.25}`
- `POST /api/rag/add`
  - Ingests text into ChromaDB.
  - Body:
    ```json
    {
      "user_id": "admin",
      "type": "document" | "skill",
      "name": "agentic_rag_overview.md",
      "text": "Full text content...",
      "chunk_size": 800,
      "overlap": 100,
      "vector_text": "Text used for embedding calculation",
      "api_key": "<key>"
    }
    ```
  - If `type == "document"`: Splits text using sliding character window (`chunk_size`, `overlap`), embeds each chunk via Ollama, and stores with metadata (`name`, `chunk_index`, `date_time`).
  - If `type == "skill"`: Embeds `vector_text` and stores skill definition.
- `POST /api/rag/query`
  - Semantic vector similarity search.
  - Body:
    ```json
    {
      "user_id": "admin",
      "conversation_id": "conv_1790000000",
      "type": "document" | "skill",
      "query": "What is Agentic RAG?",
      "k": 5,
      "threshold": 0.3,
      "api_key": "<key>"
    }
    ```
  - Response:
    ```json
    {
      "status": "success",
      "type": "document",
      "count": 2,
      "results": [
        {
          "name": "agentic_rag_overview.md",
          "similarity_score": 0.82,
          "chunk_text": "Agentic RAG combines autonomous reasoning...",
          "metadata": { "chunk_index": 0, "date_time": "..." }
        }
      ]
    }
    ```
- `POST /api/rag/delete` -> Body: `{"type": "document"|"skill", "name": "<name>|ALL"}`.
- `POST /api/rag/reset` -> Clears all document vectors. Admin only.

---

### 3.4 Procedural Tools Service (`tools`, Port 8005)

#### 3.4.1 Responsibilities
Executes deterministic business logic, data lookups, and algorithmic analyses requested by agents.

#### 3.4.2 Seed Data: Employee Registry (`tools/data/employee_database.csv`)
The employee search tool relies on a seed CSV with exact schema `name,city,country,job_title` containing at least 30 diverse records across global locations:
```csv
name,city,country,job_title
Lucas Dubois,Paris,France,Senior AI Engineer
Elena Rostova,Berlin,Germany,Data Scientist
Kenji Takahashi,Tokyo,Japan,Machine Learning Architect
Sarah Jenkins,London,United Kingdom,Product Manager
Mateo Silva,Madrid,Spain,DevOps Engineer
Chloe Martin,Montreal,Canada,Frontend Developer
Liam O'Connor,Dublin,Ireland,Backend Developer
Priya Sharma,Bengaluru,India,Full Stack Engineer
Carlos Mendez,Mexico City,Mexico,Cloud Solutions Architect
Amina Al-Mansoor,Dubai,United Arab Emirates,Security Analyst
David Kim,Seoul,South Korea,Research Scientist
Anna Kowalska,Warsaw,Poland,QA Automation Lead
Marcus Aurelius,Rome,Italy,Database Administrator
Ingrid Lindqvist,Stockholm,Sweden,Site Reliability Engineer
Gabriel Santos,Sao Paulo,Brazil,Software Engineer
Fatima Zahra,Casablanca,Morocco,Systems Analyst
Nils Hansen,Oslo,Norway,Infrastructure Engineer
Mei Ling,Singapore,Singapore,Prompt Engineer
Alexander Petrov,Belgrade,Serbia,Embedded Systems Developer
Hannah Schmidt,Zurich,Switzerland,Chief Technology Officer
Oliver Brown,Sydney,Australia,UX/UI Designer
Zainab Bello,Lagos,Nigeria,Data Engineer
Dmitri Sokolov,Prague,Czech Republic,Platform Engineer
Maria Garcia,Barcelona,Spain,Scrum Master
Taro Yamada,Osaka,Japan,Network Engineer
Sophie Bernard,Geneva,Switzerland,Compliance Officer
Arthur Pendelton,Edinburgh,United Kingdom,Technical Writer
Ananya Patel,Mumbai,India,AI Ethics Specialist
Jorge Morales,Bogota,Colombia,Customer Success Architect
Emma Watson,Vancouver,Canada,Director of Engineering
```

#### 3.4.3 Endpoints Contract
- `GET /health` -> `{"status": "ok", "service": "tools", "port": 8005}`
- `GET /api/tools/list`
  - Returns metadata and parameter schemas for available tools:
    1. `person_search.query_person_registry`: Searches `tools/data/employee_database.csv` across fields (`name`, `city`, `country`, `job_title`) using a list of search texts (`keywords`, or single text `keyword`). Searches for all queried items and returns combined, deduplicated matching entries.
    2. `stock_search.query_stocks`: Evaluates mock market feed and returns top `gainers` or `losers` limited by `limit`.
- `POST /api/tools/call`
  - Dispatches tool invocation.
  - Body:
    ```json
    {
      "tool": "person_search.query_person_registry",
      "arguments": { "keywords": ["Lucas Dubois", "Berlin"], "field": "all" },
      "conversation_id": "conv_1790000000",
      "api_key": "<key>"
    }
    ```
  - Response:
    ```json
    {
      "status": "success",
      "tool": "person_search.query_person_registry",
      "duration_ms": 15,
      "result": {
        "count": 2,
        "total_matches": 2,
        "query": ["Lucas Dubois", "Berlin"],
        "field": "all",
        "results": [
          { "name": "Lucas Dubois", "city": "Paris", "country": "France", "job_title": "Senior AI Engineer" },
          { "name": "Elena Rostova", "city": "Berlin", "country": "Germany", "job_title": "Data Scientist" }
        ]
      }
    }
    ```

---

### 3.5 Central Logging & Telemetry Service (`logging`, Port 8006)

#### 3.5.1 Storage & Schema
- Logs persist to disk at `logging/logs/log.json` (`./logging/logs:/app/logs`).
- Every entry conforms to the schema:
  ```json
  {
    "id": "log_1790000000000_a1b2",
    "timestamp": "2026-09-29T12:00:00.000000+00:00",
    "type": "send_chat_request|received_chat_request|send_chat_response|received_chat_response|llm_invocation|llm_response|tool_invocation|tool_response|skill_vector_query|skill_vector_response|document_vector_query|document_vector_response|embedding_query",
    "invoker": "web_ui|agents|doc_rag|tools|ollama",
    "recipient": "agents|doc_rag|tools|logging|web_ui|llm",
    "conversation_id": "conv_1790000000",
    "short_description": "Summary description (e.g. Agent received chat response 1420ms)",
    "payload": {
      "request": { ... },
      "response": { ... }
    },
    "status": "success|error",
    "duration_ms": 1420,
    "input_tokens": 863,
    "output_tokens": 124,
    "model": "gemma-4-26b-a4b-it",
    "is_error": false
  }
  ```

#### 3.5.2 Features
- **Full Payload Retention**: All inter-service requests and responses retain complete, untruncated payloads.
- **Recursive Key Redaction**: Before writing to disk, any field matching `api_key`, `secret`, `password`, or starting with `key-`, `AIza`, `sk-` is replaced with `****`.
- **Automatic Fallback Extraction**: If top-level `duration_ms`, `tokens`, or `model` are omitted, the service recursively extracts them from nested payload dictionaries.
- **Local Time Conversion**:
  - Accepts `tz_offset` parameter (offset in minutes from UTC provided by browser client).
  - Shifts telemetry timeline buckets so hourly/daily intervals align with client's local day/hour.
  - Returns `local_time` and `local_timestamp` formatted as `YYYY-MM-DD HH:MM:SS` for all conversations and event traces.

#### 3.5.3 Endpoints Contract
- `GET /health` -> `{"status": "ok", "service": "logging", "port": 8006}`
- `POST /api/logs` -> Ingests log entry. Returns `201` with `log_id`.
- `GET /api/conversations` (or `/api/logs`)
  - Aggregates conversation summaries and user queries/responses with local timestamps.
  - Returns: `{"conversations": [...], "statistics": {"total_user_prompts": ..., "total_model_calls": ..., "total_ollama_embeds": ..., "avg_latency_ms": ...}}`
- `GET /api/conversations/<conversation_id>/events` -> Returns chronological events for conversation with `local_time`.
- `GET /api/logs/telemetry`
  - Query Params: `model`, `interval` (`1 min`, `15 min`, `1 hr`, `1 day`), `time_range` (`Last hr`, `1 day`, `Week`, `Month`, `Custom`), `start_date`, `end_date`, `tz_offset`.
  - Returns timeline chart series (`prompts`, `responses`, `errors`, `input_tokens`, `output_tokens`), `labels` (in local time), `epochs`, and performance metrics (`avg_latency_ms`, `ttft_ms`, `itl_ms`, `tps`, `tpot_ms`).
- `POST /api/logs/clear` -> Wipes `log.json` and resets statistics.

---

### 3.6 Ollama Embedding Service (`ollama`, Port 11434)
Runs official `ollama/ollama:latest` container providing high-dimensional vector embeddings.
- `POST /api/embeddings` -> Body: `{"model": "bge-large:latest", "prompt": "<text>"}`. Returns vector array.
- `GET /api/tags` -> Lists installed local models.
- `POST /api/pull` -> Downloads model from library.

---

## 4. Autonomous Agent Orchestration Logic

### 4.1 Custom Autonomous Agent (`agents/custom_agent/custom_agent.py`)
The Custom Agent operates as a multi-turn planning loop:

```
[User Message Received]
        │
        ▼
[Check Skill Selector Setting]
 ├── "Vector Store Selects" ──► Query doc_rag for skills matching similarity threshold
 ├── "LLM Selects"          ──► Pass all skill definitions to LLM to select best match
 └── "Skill: <name>"        ──► Directly load specified skill instructions
        │
        ▼
[Synthesize Execution Plan via LLM]
 ├── No tool needed ───────► Generate immediate direct synthesis
 └── Tool required ────────► Respond with JSON Tool Execution Request:
                             {
                               "tool": "service.function_name",
                               "arguments": { "param1": "val1" }
                             }
        │
        ▼
[Dispatch Procedural Tool Call to Tools Service]
        │
        ▼
[Append Tool Result to Prompt Context]
        │
        ▼
[Loop until Answer Ready or Max Turns Reached]
        │
        ▼
[Final LLM Synthesis Call]
        │
        ▼
[Log All Hops & Return Formatted Output + Evidence to Web UI]
```

### 4.2 Document RAG Integration Rule
- Vector search for document chunks is **not** performed blindly on every query.
- It is executed **only** when either:
  1. The selected skill specifically directs the agent to query the document vector store (`document-search-skill`), OR
  2. The LLM determines domain knowledge is required and emits a tool call to `doc_rag`.

---

## 5. Security, Secrets & Inter-Container Authentication

### 5.1 Host Volume Secrets Architecture
Each service mounts a `secrets/` subfolder mapped to the host filesystem:
- `./auth_service/secrets` -> Hosts `auth.db` (SQLite user credentials and API keys).
- `./<service>/secrets/keys` -> Key configuration file storing inter-container credentials in `<target_container>=<api_key>` format.
- The `web_ui` container mounts all service secrets in `/app/container_secrets/<service>` allowing Container Mgr to read and update keys.

### 5.2 Inter-Container Authentication Flow
1. When `agents` calls `tools` or `doc_rag`, it reads the API key for that target from its `secrets/keys` file.
2. The caller attaches the key in the request payload or `Authorization: Bearer <key>` header.
3. The recipient validates the key against `auth_service` via `POST /api/auth/validate_key`.
4. If valid, the action proceeds; otherwise `401 Unauthorized` is returned.

---

## 6. Deployment & Operational Procedures

### 6.1 Prerequisites
- Docker Engine 24.0+ and Docker Compose v2.
- Linux, macOS, or WSL2.
- Ollama local embedding model `bge-large:latest` pulled.
- Valid `GEMINI_API_KEY` for Google AI Studio / Gemini API text synthesis.

### 6.2 Docker Compose Configuration (`docker-compose.yml`)
```yaml
services:
  logging:
    build: { context: ./logging, dockerfile: Dockerfile }
    container_name: logging-service
    ports: ["8006:8006"]
    volumes:
      - ./logging/logs:/app/logs
      - ./logging/server.py:/app/server.py
    environment: [PORT=8006, RUNNING_IN_DOCKER=true]

  auth_service:
    build: { context: ./auth_service, dockerfile: Dockerfile }
    container_name: auth-service
    ports: ["8001:8001"]
    volumes: ["./auth_service/secrets:/app/secrets"]
    environment: [PORT=8001, RUNNING_IN_DOCKER=true, SECRETS_DIR=/app/secrets, LOGGING_SERVICE_URL=http://logging:8006/api/logs]
    depends_on: [logging]

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-embedding
    ports: ["11434:11434"]
    volumes: ["/home/pi-net/.ollama:/root/.ollama"]

  doc_rag:
    build: { context: ./doc_RAG, dockerfile: Dockerfile }
    container_name: doc-rag-service
    ports: ["8003:8003"]
    volumes: ["./doc_RAG/chroma:/app/chroma", "./doc_RAG/secrets:/app/secrets"]
    environment: [PORT=8003, RUNNING_IN_DOCKER=true, CHROMA_DIR=/app/chroma, OLLAMA_URL=http://ollama:11434, AUTH_SERVICE_URL=http://auth_service:8001/api/auth/validate_key, LOGGING_SERVICE_URL=http://logging:8006/api/logs]
    depends_on: [logging, auth_service, ollama]

  tools:
    build: { context: ./tools, dockerfile: Dockerfile }
    container_name: tools-service
    ports: ["8005:8005"]
    volumes: ["./tools/data:/app/data", "./tools/secrets:/app/secrets"]
    environment: [PORT=8005, RUNNING_IN_DOCKER=true, DATA_DIR=/app/data, AUTH_SERVICE_URL=http://auth_service:8001/api/auth/validate_key, LOGGING_SERVICE_URL=http://logging:8006/api/logs]
    depends_on: [logging, auth_service]

  agents:
    build: { context: ./agents, dockerfile: Dockerfile }
    container_name: agents-service
    ports: ["8002:8002"]
    volumes: ["./agents/secrets:/app/secrets", "./agents/skills:/app/skills:ro"]
    environment: [PORT=8002, RUNNING_IN_DOCKER=true, DOC_RAG_URL=http://doc_rag:8003, TOOLS_URL=http://tools:8005, LOGGING_URL=http://logging:8006, AUTH_SERVICE_URL=http://auth_service:8001/api/auth/validate_key, GEMINI_API_KEY=${GEMINI_API_KEY}, GEMINI_MODEL=${GEMINI_MODEL:-gemma-4-26b-a4b-it}]
    depends_on: [logging, doc_rag, tools]

  web_ui:
    build: { context: ./web_ui, dockerfile: Dockerfile }
    container_name: web-ui-service
    ports: ["8000:8000"]
    volumes:
      - ./web_ui/secrets:/app/secrets
      - ./web_ui/static:/app/static
      - ./web_ui/templates:/app/templates
      - ./web_ui/app.py:/app/app.py
      - ./agents/secrets:/app/container_secrets/agents
      - ./doc_RAG/secrets:/app/container_secrets/doc_rag
      - ./tools/secrets:/app/container_secrets/tools
      - ./auth_service/secrets:/app/container_secrets/auth_service
      - ./web_ui/secrets:/app/container_secrets/web_ui
      - ./embedding/secrets:/app/container_secrets/ollama
      - ./sample_docs:/app/sample_docs:ro
      - /var/run/docker.sock:/var/run/docker.sock
    environment: [PORT=8000, RUNNING_IN_DOCKER=true, AUTH_SERVICE_URL=http://auth_service:8001, AGENTS_URL=http://agents:8002, DOC_RAG_URL=http://doc_rag:8003, TOOLS_URL=http://tools:8005, LOGGING_URL=http://logging:8006, OLLAMA_URL=http://ollama:11434]
    depends_on: [logging, auth_service, agents, doc_rag, tools]
```

### 6.3 Startup & Build Commands
```bash
# 1. Build and start all services in detached mode
docker compose up -d --build

# 2. Verify all 7 containers are healthy
docker compose ps

# 3. Access web dashboard
open http://localhost:8000
```

### 6.4 Verification Test Suite
Run the test suite from the repository root:
```bash
PYTHONPATH=. pytest tests/test_microservices.py -v
```
All unit and integration assertions must pass, covering:
1. `logging` health, log ingestion, query filtering, and secret redaction.
2. `auth_service` login, locked registration, unlocking, key creation, and validation.
3. `tools` procedural employee search and stock gainers/losers calculation.
4. `doc_rag` document/skill addition, semantic querying, stats, and deletion.
5. `agents` model catalog and skill discovery.
6. `web_ui` route availability and authentication template rendering.

---

## 7. Compliance Checklist for Re-creation

When recreating this project from this specification, verify that:
- [x] All 7 containers build, start, and communicate without manual IP configuration.
- [x] On Chat & Knowledge Mgnt, Left Card and Right Card each take exactly 50% of the window width with full-width layout (`max-width: 100%`).
- [x] Max RAG Chunks (2, 3, 5, 7, 10), Skill Selector, and Skill Threshold are located in the Right Card.
- [x] Max Tokens defaults to 2048 and Temperature defaults to 0.7 in the page header.
- [x] Response detail boxes contain expandable "Show Logs" toggle with component bubbles and elapsed times.
- [x] "Select All" checkbox and "Delete Selected API Keys" confirmation modal work in Password & API Mgnt.
- [x] Inter-container keys edited via Container Mgr update `<container>/secrets/keys` and authenticate calls.
- [x] Log viewer displays both User Query and Agent Response in User Conversations table.
- [x] All timestamps in Telemetry and Log View are converted and displayed in the user's **local time**.
- [x] Sensitive tokens (`api_key`, `secret`, `password`) are masked as `****` in `log.json`.
- [x] Shutdown button triggers confirmation modal requiring "Shutdown the services" text.

---

## 8. Evaluation & System Recreatability Assessment

### 8.1 Question: Can a similar app be created from the specification in `SPECIFICATIONS_GEN.md`?

**Yes, absolutely.** The specification in `SPECIFICATIONS_GEN.md` contains all the necessary architectural, behavioral, and data requirements for an independent developer or automated IDE agent to recreate this identical system without ambiguity.

### 8.2 Why the Specification is Complete & Actionable:
1. **Deterministic Microservice Boundary Definitions**:
   - The network topology, ports (`8000`, `8001`, `8002`, `8003`, `8005`, `8006`, `11434`), and inter-service HTTP REST contracts are explicitly declared with complete JSON request and response payloads.
2. **Explicit Data Models & Schemas**:
   - The SQLite database schema for authentication (`auth.db`), the JSON schema for central logs (`log.json`), the ChromaDB collections (`documents`, `skills`), and the seed data for tools (`tools/data/employee_database.csv`) are documented in full.
3. **Exact GUI Layout & Component Behavior**:
   - Every UI tab, card split ratio (50%/50% grid width), default control value (Max Tokens 2048, Temperature 0.7, Max Turns 3, Chunk Size 800, Overlap 100), and interactive modal flow (Registration in locked state, bulk key deletion confirmation, shutdown confirmation) has exact specifications.
4. **Autonomous Agent Planning Loop**:
   - The planning and reasoning workflow (`custom_agent.py`) is specified step-by-step, including skill discovery, similarity matching, tool calling format (`{"tool": "...", "arguments": {...}}`), loop termination criteria (`max_turns`), and conditional document vector searching.
5. **Security & Inter-Service Authentication**:
   - The host volume secret persistence (`secrets/keys`), token formats (`key-<hex>`), Bearer token validation endpoints, and automatic regex-based secret redaction (`****`) are clearly detailed.
6. **Timezone Handling**:
   - Explicit instructions for translating UTC timestamps to local client time across both chart coordinates and tabular forensic logs using client timezone offset (`tz_offset`).
7. **Complete Docker Composition & Automated Tests**:
   - The exact `docker-compose.yml` service blocks, environment variables, volume mounts, and `pytest tests/test_microservices.py` test suite provide a turn-key verification harness to guarantee compliance.
