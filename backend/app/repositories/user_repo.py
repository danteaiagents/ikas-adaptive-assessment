"""User Repository — PostgreSQL CRUD operations for User model."""

import uuid
from typing import Optional
from app.models.db_models import User
from app.extensions import db


def create_user(
    email: str,
    username: str,
    password_hash: str,
    display_name: str,
    role: str = 'student',
) -> User:
    """Create a new user with a UUID primary key."""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        username=username,
        password_hash=password_hash,
        display_name=display_name,
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def get_by_email(email: str) -> Optional[User]:
    """Look up a user by email address."""
    return User.query.filter_by(email=email).first()


def get_by_id(user_id: str) -> Optional[User]:
    """Look up a user by UUID."""
    return db.session.get(User, user_id)
