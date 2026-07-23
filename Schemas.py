from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- Photos ----------

class PhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    frame_no: Optional[str] = None
    exposure: Optional[str] = None
    caption: Optional[str] = None
    image_path: str
    sort_order: int
    created_at: datetime


class PhotoUpdate(BaseModel):
    category: Optional[str] = None
    frame_no: Optional[str] = None
    exposure: Optional[str] = None
    caption: Optional[str] = None
    sort_order: Optional[int] = None


# ---------- Reels ----------

class ReelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    caption: Optional[str] = None
    video_path: str
    sort_order: int
    created_at: datetime


# ---------- Contact ----------

class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5000)
    event_date: Optional[str] = Field(default=None, max_length=40)
    website: Optional[str] = Field(default="", max_length=200)


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    message: str
    event_date: Optional[str] = None
    read: bool
    created_at: datetime


# ---------- Admin auth ----------

class AdminLogin(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class AdminTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class AdminChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
