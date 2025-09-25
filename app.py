from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import torch
from model_loader import load_model
from median_store import RollingMedianStore
from utils.create_model import InefficientModel

import threading
import json

class MLService:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = InefficientModel(in_dim=3).to(self.device)
        self.model = load_model()
        self.store = RollingMedianStore()
        self.event_count = 0

        self.lock = threading.Lock()

        # Register routes
        self.app.post("/ingest")(self.ingest)
        self.app.get("/stats")(self.get_stats)
        self.app.get("/users/{user_id}/median")(self.get_user_median)

    async def ingest(self, request: Request):
        async for line in request.stream():
            if line:
                e = json.loads(line)
                with self.lock:
                    try:
                        features = torch.tensor(e["features"], dtype=torch.float32).to(self.device)
                        with torch.no_grad():
                            score = self.model(features).item()
                        self.store.add(e["user_id"], score, e["timestamp"])
                        self.event_count += 1
                    except Exception as ex:
                        print(f"Error processing event {e}: {ex}")

        return {"status": "ok", "count": self.event_count}

    async def get_stats(self):
        return {
            "status": "ok",
            "event_count": self.event_count,
            "users_tracked": self.store.num_users(),
        }

    async def get_user_median(self, user_id: str):
        median_value = self.store.median(user_id)
        return {"user_id": user_id, "median": median_value}

# Instantiate the service and expose the FastAPI app
ml_service = MLService()
app = ml_service.app
