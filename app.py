from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import torch
from model_loader import load_model
from median_store import RollingMedianStore
from utils.create_model import InefficientModel

app = FastAPI()

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Device setup
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model ONCE
model = InefficientModel(in_dim=3).to(device)
model = load_model()

# Init store
store = RollingMedianStore()
event_count = 0  # track how many events processed

@app.post("/ingest")
async def ingest(request: Request):
    """
    Ingest a batch of events.
    Each event has: {user_id, timestamp, features}
    """
    global event_count
    payload = await request.json()
    events = payload.get("events", [])

    for e in events:
        try:
            # Convert features to tensor on correct device
            features = torch.tensor(e["features"], dtype=torch.float32).to(device)

            # Run inference
            with torch.no_grad():
                score = model(features).item()

            # Store the result
            store.add(e["user_id"], score, e["timestamp"])
            event_count += 1

        except Exception as ex:
            print(f"Error processing event {e}: {ex}")

    return {"status": "ok", "count": len(events)}

@app.get("/stats")
async def get_stats():
    return {
        "status": "ok",
        "event_count": event_count,
        "users_tracked": store.num_users(),
    }

@app.get("/users/{user_id}/median")
async def get_user_median(user_id: str):
    median_value = store.median(user_id)
    return {"user_id": user_id, "median": median_value}
