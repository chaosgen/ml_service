from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import torch
import torch.nn as nn
from collections import defaultdict, deque
import time
import numpy as np

from model_loader import load_model
from median_store import RollingMedianStore

app = FastAPI()

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model once at startup
model = load_model()
store = RollingMedianStore()

@app.post("/ingest")
async def ingest(request: Request):
    """
    Ingest a batch of events.
    Each event has: {user_id, timestamp, features}
    """

    # Parse JSON body
    payload = await request.json()
    events = payload.get("events", [])

    print(events)

    for e in events:
        try:
            # Convert features into torch tensor
            features = torch.tensor(e["features"], dtype=torch.float32)

            # Run inference
            with torch.no_grad():
                score = model(features).item()

            # Store the result
            store.add(e["user_id"], score, e["timestamp"])

        except Exception as ex:
            print(f"Error processing event {e}: {ex}")

    # Return summary
    return {"status": "ok", "count": len(events)}


@app.get("/stats")
async def get_stats():
    return {"status": "ok", "event_count": store.event_count}

@app.get("/users/{user_id}/median")
async def get_user_median(user_id: str):
    pass