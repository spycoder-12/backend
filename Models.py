from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from Database import Base


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True, nullable=False)   # weddings, portraits, landscapes, events, products
    frame_no = Column(String(20), nullable=True)                 # e.g. "04A" - contact-sheet frame tag
    exposure = Column(String(60), nullable=True)                 # e.g. "f/1.8 · 1/200 · 35mm"
    caption = Column(String(200), nullable=True)
    image_path = Column(String(300), nullable=False)             # relative path under /uploads
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Reel(Base):
    __tablename__ = "reels"

    id = Column(Integer, primary_key=True, index=True)
    caption = Column(String(200), nullable=True)
    video_path = Column(String(300), nullable=False)              # relative path under /uploads
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    message = Column(Text, nullable=False)
    event_date = Column(String(40), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
