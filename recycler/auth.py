import os
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User, MerchantCompany, RecyclerCompany

SECRET_KEY = os.environ.get("RECYCLE_SECRET_KEY") or secrets.token_urlsafe(48)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, session_version: int = 0) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "session_version": session_version,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="未登录或 token 无效")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="未登录或 token 无效")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    if user.status != "approved":
        raise HTTPException(403, {"code": "ACCOUNT_DISABLED", "message": "账号已清退或尚未通过审核，请重新登录"})

    if payload.get("session_version", 0) != (user.session_version or 0):
        raise HTTPException(401, "登录已失效，请重新登录")

    if user.company_type in ("merchant", "recycler"):
        cls = MerchantCompany if user.company_type == "merchant" else RecyclerCompany
        company = db.get(cls, user.company_id) if user.company_id else None
        owner = db.get(User, company.owner_user_id) if company else None
        owner_role = "merchant_owner" if user.company_type == "merchant" else "recycler_owner"
        if (not company or company.status != "active" or not owner or
                owner.status != "approved" or owner.role != owner_role or
                owner.company_type != user.company_type or owner.company_id != company.id):
            raise HTTPException(403, {"code": "ACCOUNT_DISABLED", "message": "所属公司没有有效老板账号，请联系平台核对公司归属"})

    return user


def require_platform_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "platform_admin":
        raise HTTPException(status_code=403, detail="暂无平台管理员权限")

    return current_user
