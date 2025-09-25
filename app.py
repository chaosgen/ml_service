from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware

import torch
from utils.model_loader import load_model
from utils.median_store import RollingMedianStore
from utils.create_model import InefficientModel

import json

class MLService:
    def __init__(self):
        """ Initialize the ML service with model, data store, and FastAPI app. """
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
        self.model = load_model(device=self.device)
        
        self.store = RollingMedianStore(window_sec=300, db_path="events.db")
        self.event_count = 0

        # Register routes
        self.app.post("/ingest")(self.ingest)
        self.app.get("/stats")(self.get_stats)
        self.app.get("/users/{user_id}/median")(self.get_user_median)
        self.app.get("/users/{user_id}/history")(self.get_user_history)

    async def ingest(self, request: Request, batch_size: int = 64):
        """ Ingest a stream of events, process in batches. """
        buffer = []
        async for line in request.stream():
            if not line:
                continue

            e = json.loads(line)
            buffer += e['events']  # assuming one event per line
            if len(buffer) >= batch_size:
                await self._process_batch(buffer)
                buffer = []

        # flush leftovers
        if buffer:
            await self._process_batch(buffer)

        return {"status": "ok", "count": self.event_count}
    
    async def _process_batch(self, events):
        """ Process a batch of events: run model inference and update rolling medians. """
        features_batch = torch.tensor([e["features"] for e in events],
                                    dtype=torch.float32).to(self.device)
        user_ids = [e["user_id"] for e in events]
        timestamps = [e["timestamp"] for e in events]
        
        with torch.no_grad():
            scores = self.model(features_batch).detach().cpu().numpy()

        for uid, ts, score in zip(user_ids, timestamps, scores):
            self.store.add(uid, float(score), ts)
            self.event_count += 1

    async def get_stats(self):
        """ Return overall stats about the service. """
        return {
            "status": "ok",
            "event_count": self.event_count,
            "users_tracked": self.store.num_users(),
            "median_of_medians": self.store.median_of_medians(),
        }

    async def get_user_median(self, user_id: str):
        """ Return the rolling median for a user. """
        median_value = self.store.median(user_id)
        return {"user_id": user_id, "median": median_value}
    
    async def get_user_history(
        self,
        user_id: str,
        since: int | None = Query(None, description="Only return events with timestamp >= since"),
        until: int | None = Query(None, description="Only return events with timestamp <= until")
    ):
        """
        Return the full historical scores for a user.
        Optional query params:
            since: filter events with timestamp >= since
            until: filter events with timestamp <= until
        """
        rows = self.store.db.get_user_history(user_id, since, until)
        return {
            "user_id": user_id,
            "history": [{"timestamp": ts, "score": s} for ts, s in rows]
        }

# Instantiate the service and expose the FastAPI app
ml_service = MLService()
app = ml_service.app
