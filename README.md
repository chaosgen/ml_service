# ML Event Processing & Real-Time Analytics Service

## 📌 About the Project

This project is a **real-time machine learning service** that:

* Accepts a **stream of user events** (`user_id`, `timestamp`, `features`).
* Runs **PyTorch model inference** to compute a score for each event.
* Maintains a **rolling median score per user** over a configurable time window (default: 5 minutes).
* Persists all events into a **SQLite database** for historical queries.
* Provides a RESTful API to query:

  * Latest rolling median for a user.
  * Full historical scores (optionally time-filtered).
  * Global service statistics (event count, number of users, median of medians).

The service is built with **FastAPI** for high performance and async streaming ingestion.
It’s designed to be **scalable**, **easy to deploy**, and **profilable** for performance improvements.

---

## ⚙️ Architecture

### High-Level Components

```
 ┌──────────────────────┐
 │  Event Generator     │
 │ (synthetic load)     │
 └──────────┬───────────┘
            │ HTTP POST (streamed / batched JSON)
 ┌──────────▼───────────┐
 │  FastAPI Service     │
 │  - /ingest           │
 │  - /stats            │
 │  - /users/{id}/...   │
 └──────────┬───────────┘
            │
            │  Model inference (PyTorch)
            │
 ┌──────────▼───────────┐
 │ RollingMedianStore   │
 │  - 5 min sliding win │
 │  - median calc       │
 │  - out-of-order safe │
 └──────────┬───────────┘
            │
            │ SQLite persistence
 ┌──────────▼───────────┐
 │       EventDB        │
 │  - Full history      │
 │  - Stats             │
 └──────────────────────┘
```

### Key Design Choices

* **Async Streaming Ingestion**: The `/ingest` endpoint reads the request body line by line, buffering events and processing them in **batches** (default batch size = 64).
* **Batch Model Inference**: Converts event features into a tensor and runs **vectorized inference** to maximize GPU/CPU efficiency.
* **Out-of-Order Events**: Uses `bisect.insort` to keep user event lists sorted by timestamp even when late events arrive.
* **Rolling Median**: Maintains a **5-minute sliding window** for each user and computes the median efficiently.
* **Persistence**: All processed events are stored in a **SQLite database (`events.db`)** for long-term querying.
* **Statistics**: Provides **median of medians** for overall service health monitoring.
* **Profiling Ready**: Designed to run with `pyinstrument` or `cProfile` for performance debugging.

---

## 🚀 Installation & Setup

### 1️⃣ Clone and Set Up

```bash
git clone https://github.com/chaosgen/ml_service.git
cd ml_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Prepare the Model

The service expects a pretrained PyTorch model at `model/inefficient_model.pt`.
You can generate a dummy model with:

```bash
python utils/create_model.py
```

This creates a simple `InefficientModel` and saves weights.

### 3️⃣ Start the Service

Run with **Uvicorn**:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

For production (faster workers & no reload):

```bash
pip install gunicorn
gunicorn -k uvicorn.workers.UvicornWorker -w 4 app:app
```

---

## 🌐 API Endpoints

### **POST /ingest**

Ingest a stream of events. Accepts **streamed JSON lines** or batched JSON objects.

```json
{"events": [
    {"user_id": "user-123", "timestamp": 1758767856, "features": [0.1, 0.2, 0.3]},
    {"user_id": "user-456", "timestamp": 1758767857, "features": [0.4, 0.5, 0.6]}
]}
```

* The service buffers events (default `batch_size=64`) and runs batched model inference.

---

### **GET /stats**

Returns global service statistics.

```json
{
  "status": "ok",
  "event_count": 10500,
  "users_tracked": 320,
  "median_of_medians": 0.4738
}
```

---

### **GET /users/{user_id}/median**

Returns the **rolling median** of the user’s scores (last 5 minutes).

```json
{
  "user_id": "user-123",
  "median": 0.5321
}
```

---

### **GET /users/{user_id}/history**

Returns the **full historical scores** for a user.
Supports optional time filters `since` and `until` (UNIX timestamps).

* **Examples:**

  * `/users/user-1337/history`
  * `/users/user-1337/history?since=1758767000&until=1758769000`

```json
{
  "user_id": "user-1337",
  "history": [
    {"timestamp": 1758767856, "score": 0.47},
    {"timestamp": 1758767901, "score": 0.52}
  ]
}
```

---

## 🔬 Load Testing

You can simulate high-throughput event streams using the provided script:

```bash
python utils/event_generator.py
```

Options (edit script or add args):

* `target_url`: default `http://localhost:8000/ingest`
* `rps`: events per second (default 5000)
* `duration_sec`: test duration
* `users`: number of unique users

Example:

```bash
python utils/event_generator.py --target_url http://localhost:8000/ingest --rps 10000 --duration_sec 120
```

---

## 🗄️ Database & Persistence

* Events are persisted to a **SQLite database (`events.db`)**.
* Schema:

```sql
CREATE TABLE events (
    user_id TEXT,
    timestamp INTEGER,
    score REAL
);
CREATE INDEX idx_user_ts ON events(user_id, timestamp);
```

* You can open `events.db` in **VS Code** using:

  * [SQLite Viewer](https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer) (simple)
  * [SQLite by alexcvzz](https://marketplace.visualstudio.com/items?itemName=alexcvzz.vscode-sqlite) (interactive querying)

---

## 🐳 Docker Deployment

Minimal `Dockerfile`:

```dockerfile
FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

```

Build & run:

```bash
docker build -t ml-service .
docker run -p 8000:8000 ml-service
```

---

## 🛡️ Reliability & Performance Notes

* **Async streaming** allows ingesting very high event rates.
* **Batch inference** reduces PyTorch overhead.
* **Out-of-order safe**: `bisect.insort` keeps per-user events sorted.
* **Median calculation**: efficient for rolling window; can be swapped for heap-based if needed.
* **Persistence**: SQLite is simple; for huge loads consider Postgres or a message queue (Kafka).
