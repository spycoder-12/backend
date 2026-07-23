from fastapi import (
    FastAPI,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session

import os
import shutil
import uuid

import Models
import Schemas

from Database import Base, engine, get_db, SessionLocal
from Emailer import send_contact_notification
from config import CORS_ORIGINS, UPLOAD_DIR, ALLOWED_VIDEO_TYPES, MAX_REEL_MB
from Auth import (
    require_admin,
    ensure_default_admin,
    verify_password,
    hash_password,
    create_access_token,
)


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Photography Portfolio API",
    version="1.1.0",
)


# -------------------------
# Startup: make sure a default admin account exists
# -------------------------

@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    try:
        ensure_default_admin(db)
    finally:
        db.close()


# -------------------------
# CORS
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Static uploads folder
# -------------------------

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads",
)


# =========================
# ADMIN AUTH APIs
# =========================

@app.post("/admin/login", response_model=Schemas.AdminTokenOut)
def admin_login(
    credentials: Schemas.AdminLogin,
    db: Session = Depends(get_db),
):
    admin = (
        db.query(Models.Admin)
        .filter(Models.Admin.username == credentials.username)
        .first()
    )

    if admin is None or not verify_password(credentials.password, admin.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    token = create_access_token(admin.username)

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": admin.username,
    }


@app.post("/admin/change-password")
def admin_change_password(
    payload: Schemas.AdminChangePassword,
    db: Session = Depends(get_db),
    admin_username: str = Depends(require_admin),
):
    admin = (
        db.query(Models.Admin)
        .filter(Models.Admin.username == admin_username)
        .first()
    )

    if admin is None:
        raise HTTPException(status_code=404, detail="Admin not found")

    if not verify_password(payload.current_password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    admin.password_hash = hash_password(payload.new_password)
    db.commit()

    return {
        "success": True,
        "message": "Password updated successfully",
    }


@app.get("/admin/me")
def admin_me(admin_username: str = Depends(require_admin)):
    return {"username": admin_username}


# =========================
# PHOTO APIs
# =========================


# GET ALL PHOTOS
@app.get("/photos", response_model=list[Schemas.PhotoOut])
def get_photos(
    db: Session = Depends(get_db),
):
    return (
        db.query(Models.Photo)
        .order_by(Models.Photo.sort_order)
        .all()
    )


# UPLOAD PHOTO
@app.post("/photos/upload")
def upload_photo(
    category: str = Form(...),
    caption: str = Form(""),
    frame_no: str = Form(""),
    exposure: str = Form(""),
    sort_order: int = Form(0),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed",
        )

    extension = os.path.splitext(image.filename)[1]
    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    new_photo = Models.Photo(
        category=category,
        caption=caption,
        frame_no=frame_no,
        exposure=exposure,
        image_path=filename,
        sort_order=sort_order,
    )

    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)

    return {
        "success": True,
        "message": "Photo uploaded successfully",
        "photo": Schemas.PhotoOut.model_validate(new_photo).model_dump(mode="json"),
    }


# UPDATE PHOTO
@app.put("/photos/{photo_id}")
def update_photo(
    photo_id: int,
    category: str = Form(None),
    caption: str = Form(None),
    frame_no: str = Form(None),
    exposure: str = Form(None),
    sort_order: int = Form(None),
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
):
    photo = db.query(Models.Photo).filter(Models.Photo.id == photo_id).first()

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Compare to None (not falsy-check) so an intentional empty string
    # actually clears the field instead of being silently ignored.
    if category is not None:
        photo.category = category

    if caption is not None:
        photo.caption = caption

    if frame_no is not None:
        photo.frame_no = frame_no

    if exposure is not None:
        photo.exposure = exposure

    if sort_order is not None:
        photo.sort_order = sort_order

    db.commit()
    db.refresh(photo)

    return {
        "success": True,
        "message": "Photo updated successfully",
        "photo": Schemas.PhotoOut.model_validate(photo).model_dump(mode="json"),
    }


# DELETE PHOTO
@app.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
):
    photo = db.query(Models.Photo).filter(Models.Photo.id == photo_id).first()

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    file_path = os.path.join(UPLOAD_DIR, photo.image_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(photo)
    db.commit()

    return {
        "success": True,
        "message": "Photo deleted successfully",
    }


# =========================
# REEL APIs
# =========================


# GET ALL REELS
@app.get("/reels", response_model=list[Schemas.ReelOut])
def get_reels(
    db: Session = Depends(get_db),
):
    return (
        db.query(Models.Reel)
        .order_by(Models.Reel.sort_order)
        .all()
    )


# UPLOAD REEL
@app.post("/reels/upload")
def upload_reel(
    caption: str = Form(""),
    sort_order: int = Form(0),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
):
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
    extension = os.path.splitext(video.filename)[1].lower()

    content_type_ok = video.content_type in ALLOWED_VIDEO_TYPES
    extension_ok = extension in ALLOWED_VIDEO_EXTENSIONS

    if not (content_type_ok or extension_ok):
        raise HTTPException(
            status_code=400,
            detail="Only mp4, webm, or mov video files are allowed",
        )

    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    max_bytes = MAX_REEL_MB * 1024 * 1024
    size = 0

    with open(file_path, "wb") as buffer:
        while chunk := video.file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                buffer.close()
                os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"Video exceeds the {MAX_REEL_MB}MB limit",
                )
            buffer.write(chunk)

    new_reel = Models.Reel(
        caption=caption,
        video_path=filename,
        sort_order=sort_order,
    )

    db.add(new_reel)
    db.commit()
    db.refresh(new_reel)

    return {
        "success": True,
        "message": "Reel uploaded successfully",
        "reel": Schemas.ReelOut.model_validate(new_reel).model_dump(mode="json"),
    }


# UPDATE REEL
@app.put("/reels/{reel_id}")
def update_reel(
    reel_id: int,
    caption: str = Form(None),
    sort_order: int = Form(None),
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
):
    reel = db.query(Models.Reel).filter(Models.Reel.id == reel_id).first()

    if reel is None:
        raise HTTPException(status_code=404, detail="Reel not found")

    if caption is not None:
        reel.caption = caption

    if sort_order is not None:
        reel.sort_order = sort_order

    db.commit()
    db.refresh(reel)

    return {
        "success": True,
        "message": "Reel updated successfully",
        "reel": Schemas.ReelOut.model_validate(reel).model_dump(mode="json"),
    }


# DELETE REEL
@app.delete("/reels/{reel_id}")
def delete_reel(
    reel_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
):
    reel = db.query(Models.Reel).filter(Models.Reel.id == reel_id).first()

    if reel is None:
        raise HTTPException(status_code=404, detail="Reel not found")

    file_path = os.path.join(UPLOAD_DIR, reel.video_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(reel)
    db.commit()

    return {
        "success": True,
        "message": "Reel deleted successfully",
    }


# =========================
# CONTACT APIs
# =========================


# CREATE CONTACT MESSAGE
@app.post("/contact")
def contact(
    contact: Schemas.ContactCreate,
    db: Session = Depends(get_db),
):
    # Honeypot spam protection
    if contact.website:
        return {"message": "Success"}

    new_message = Models.ContactMessage(
        name=contact.name,
        email=contact.email,
        message=contact.message,
        event_date=contact.event_date,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    try:
        send_contact_notification(
            contact.name,
            contact.email,
            contact.message,
            contact.event_date,
        )
    except Exception as e:
        print("EMAIL ERROR:", e)

    return {
        "success": True,
        "message": "Thank you for contacting us!",
    }


# GET ALL CONTACT MESSAGES
@app.get("/contacts", response_model=list[Schemas.ContactOut])
def get_contacts(
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
):
    return (
        db.query(Models.ContactMessage)
        .order_by(Models.ContactMessage.id.desc())
        .all()
    )


# DELETE CONTACT MESSAGE
@app.delete("/contact/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(require_admin),
):
    contact = (
        db.query(Models.ContactMessage)
        .filter(Models.ContactMessage.id == contact_id)
        .first()
    )

    if contact is None:
        raise HTTPException(status_code=404, detail="Contact message not found")

    db.delete(contact)
    db.commit()

    return {
        "success": True,
        "message": "Contact deleted successfully",
    }

@app.get("/")
def read_root():
    return {"message": "API is running"}
