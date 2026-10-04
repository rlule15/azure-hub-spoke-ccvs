# TODO Implement security
import app.db.schema as schema
from fastapi import HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy import select

password_hash = PasswordHash.recommended()


def hash_password(password: str):
    return PasswordHash.hash(password_hash, password)


def verify_password(password: str, hashed_password: str):
    return password_hash.verify(password, hashed_password)


def get_user(db, username: str):
    user = db.execute(
        select(schema.User).where(schema.User.username == username)
    ).scalar_one_or_none()
    if not user:
        return False
    return user


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def verify_session(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id
