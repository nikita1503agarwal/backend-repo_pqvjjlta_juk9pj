import os
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Room

app = FastAPI(title="SyncWave API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateRoomRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=10)
    track_url: Optional[str] = None


class JoinRoomRequest(BaseModel):
    code: str


class UpdateStateRequest(BaseModel):
    code: str
    is_playing: Optional[bool] = None
    position: Optional[float] = Field(None, ge=0)
    track_url: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "SyncWave backend running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Helper
def _room_collection():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    return db["room"]


@app.post("/api/rooms")
def create_room(payload: CreateRoomRequest):
    col = _room_collection()
    code = payload.code.upper()

    if col.find_one({"code": code}):
        raise HTTPException(status_code=400, detail="Room code already exists")

    now = time.time()
    room = Room(code=code, track_url=payload.track_url, is_playing=False, position=0.0, updated_at=now)
    room_id = create_document("room", room)
    return {"id": room_id, "code": code}


@app.post("/api/rooms/join")
def join_room(payload: JoinRoomRequest):
    col = _room_collection()
    room = col.find_one({"code": payload.code.upper()})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room["_id"] = str(room["_id"])
    return room


@app.get("/api/rooms/{code}")
def get_room(code: str):
    col = _room_collection()
    room = col.find_one({"code": code.upper()})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room["_id"] = str(room["_id"])
    return room


@app.patch("/api/rooms/{code}")
def update_room_state(code: str, payload: UpdateStateRequest):
    col = _room_collection()
    room = col.find_one({"code": code.upper()})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    update = {"updated_at": time.time()}
    if payload.is_playing is not None:
        update["is_playing"] = payload.is_playing
    if payload.position is not None:
        update["position"] = float(payload.position)
    if payload.track_url is not None:
        update["track_url"] = payload.track_url

    col.update_one({"_id": room["_id"]}, {"$set": update})
    new_room = col.find_one({"code": code.upper()})
    new_room["_id"] = str(new_room["_id"])
    return new_room


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
