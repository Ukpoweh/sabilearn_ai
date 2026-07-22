import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import create_access_token, hash_password, verify_password
from ..data_models import models, schemas
from ..data_models.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: schemas.TeacherRegisterRequest, db: Session = Depends(get_db)):
    role = "teacher"
    admin_code = os.getenv("ADMIN_SIGNUP_CODE")
    if admin_code and request.admin_code == admin_code:
        role = "admin"

    teacher = models.Teacher(
        username=request.username,
        password_hash=hash_password(request.password),
        name=request.name,
        school_id=request.school_id,
        subject=request.subject,
        role=role,
    )
    db.add(teacher)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken.")
    db.refresh(teacher)

    return {"id": str(teacher.id), "username": teacher.username, "role": teacher.role}


@router.post("/token", response_model=schemas.TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    teacher = db.query(models.Teacher).filter(models.Teacher.username == form_data.username).first()
    if not teacher or not verify_password(form_data.password, teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": create_access_token(str(teacher.id)),
        "token_type": "bearer",
        "role": teacher.role,
        "username": teacher.username,
    }
