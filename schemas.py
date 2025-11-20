"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

# Realtime Listening Room schema
class Room(BaseModel):
    """
    Listening rooms where multiple devices join and sync playback.
    Collection name: "room"
    """
    code: str = Field(..., description="Short room code used to join")
    track_url: Optional[str] = Field(None, description="Current audio URL for the room")
    is_playing: bool = Field(False, description="Whether the room is currently playing")
    position: float = Field(0.0, ge=0, description="Playback position in seconds")
    updated_at: float = Field(0.0, ge=0, description="Server epoch seconds of last state change")

# Example schemas (kept for reference)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
