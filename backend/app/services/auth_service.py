from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.access_token_expire_hours)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return user


def create_admin_user(db: Session) -> None:
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        return
    user = User(
        username="admin",
        password_hash=hash_password(settings.admin_password),
        must_change_password=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()
