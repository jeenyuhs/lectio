import typing
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from lectio import lectio
from lectio.user import User

import os
import cache

SECRET_KEY = os.urandom(24)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION = 100000  # minutes

CREDENTIAL_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInfo(BaseModel):
    username: str
    school_district: int
    exp: timedelta | None = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain: str, hashed: bytes) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


async def authenticate(_username: str, password: str):
    # since jwt authetication, can only be taken by username and password
    # the school_district has to be inside of the username.
    if "|" not in _username:
        return False

    username, school_district = _username.split("|")
    user = await lectio.login(username, password, int(school_district))

    if not user:
        # failed login
        return

    cache.lectio_users[username] = user
    return user


def create_access_token(u: User, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    return jwt.encode(
        {"user": u.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM
    )


async def get_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if not payload:
        return CREDENTIAL_ERROR

    username = payload.get("user")

    if username not in cache.lectio_users:
        return CREDENTIAL_ERROR

    return cache.lectio_users[username]  # type: ignore
