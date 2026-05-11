import os
import uuid
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.database import SessionLocal, UserModel

SECRET_KEY = os.environ.get("SECRET_KEY", "cerebro-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        db = SessionLocal()
        user = db.query(UserModel).filter(UserModel.username == username).first()
        db.close()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_admin_user(current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user

def get_user(username: str):
    db = SessionLocal()
    try:
        return db.query(UserModel).filter(UserModel.username == username).first()
    finally:
        db.close()

def create_user(username: str, email: str, password: str, is_admin: bool = False):
    db = SessionLocal()
    try:
        user = UserModel(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_admin=is_admin,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        return user
    finally:
        db.close()

def init_default_admin():
    db = SessionLocal()
    try:
        existing = db.query(UserModel).filter(UserModel.username == "daniel").first()
        if not existing:
            create_user("daniel", "daniel.glez.solucionador@gmail.com", "cerebro24", is_admin=True)
            print("Admin created: daniel")
        else:
            print("Admin exists: daniel")
    finally:
        db.close()
