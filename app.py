from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import torch
import torch.nn as nn
from collections import defaultdict, deque
import time
import numpy as np

app = FastAPI()

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ingest")
async def ingest(request: Request):
    pass

@app.get("/stats")
async def get_stats():
    pass

@app.get("/users/{user_id}/median")
async def get_user_median(user_id: str):
    pass