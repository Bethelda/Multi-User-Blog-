from datetime import datetime

from flask_login import UserMixin

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from db import db, login_manager


# ==========================================================
# USER LOADER
# ==========================================================

@login_manager.user_loader
def load_user(user_id):

    try:
        return db.session.get(User, int(user_id))

    except (TypeError, ValueError):
        return None


# ==========================================================
# USER MODEL
# ==========================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    # ------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ------------------------------------------------------
    # User Information
    # ------------------------------------------------------

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # ------------------------------------------------------
    # User Role
    # ------------------------------------------------------

    role = db.Column(
        db.String(20),
        nullable=False,
        default="user"
    )

    # ------------------------------------------------------
    # Profile Information
    # ------------------------------------------------------

    bio = db.Column(
        db.Text,
        nullable=True
    )

    profile_image = db.Column(
        db.String(255),
        nullable=True
    )

    # ------------------------------------------------------
    # Account Creation Date
    # ------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ------------------------------------------------------
    # Relationship with Posts
    # ------------------------------------------------------

    posts = db.relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy=True
    )

    # ------------------------------------------------------
    # Set Password
    # ------------------------------------------------------

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    # ------------------------------------------------------
    # Check Password
    # ------------------------------------------------------

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )

    # ------------------------------------------------------
    # Representation
    # ------------------------------------------------------

    def __repr__(self):

        return f"<User {self.username}>"


# ==========================================================
# POST MODEL
# ==========================================================

class Post(db.Model):

    __tablename__ = "posts"

    # ------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ------------------------------------------------------
    # Post Information
    # ------------------------------------------------------

    title = db.Column(
        db.String(200),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    image = db.Column(
        db.String(255),
        nullable=True
    )

    # ------------------------------------------------------
    # Publishing Status
    # ------------------------------------------------------

    published = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # ------------------------------------------------------
    # Dates
    # ------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ------------------------------------------------------
    # Author ID
    # ------------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # ------------------------------------------------------
    # Relationship with User
    # ------------------------------------------------------

    author = db.relationship(
        "User",
        back_populates="posts"
    )

    # ------------------------------------------------------
    # Representation
    # ------------------------------------------------------

    def __repr__(self):

        return f"<Post {self.title}>"