import pytest
from app.models.user import User
from app.services.auth_service import (
    authenticate_user,
    create_admin_user,
    hash_password,
    verify_password,
    verify_token,
    create_access_token,
)


def test_hash_and_verify():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_verify_token():
    token = create_access_token(42)
    assert verify_token(token) == 42


def test_verify_invalid_token():
    assert verify_token("not-a-jwt") is None
    assert verify_token("eyJ.invalid.token") is None


def test_authenticate_user(db):
    user = User(
        username="testuser",
        password_hash=hash_password("pass1234"),
        must_change_password=False,
        is_admin=False,
    )
    db.add(user)
    db.commit()

    result = authenticate_user(db, "testuser", "pass1234")
    assert result is not None
    assert result.username == "testuser"

    result = authenticate_user(db, "testuser", "wrong")
    assert result is None

    result = authenticate_user(db, "nouser", "pass1234")
    assert result is None


def test_create_admin_user(db):
    create_admin_user(db)
    admin = db.query(User).filter(User.username == "admin").first()
    assert admin is not None
    assert admin.is_admin is True
    assert admin.must_change_password is True

    # Calling again should not create duplicate
    create_admin_user(db)
    count = db.query(User).filter(User.username == "admin").count()
    assert count == 1
