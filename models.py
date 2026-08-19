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
        return db.session.get(
            User,
            int(user_id)
        )

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
    # Relationships
    # ------------------------------------------------------

    posts = db.relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
        lazy=True
    )

    likes = db.relationship(
        "PostLike",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True
    )

    comments = db.relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True
    )

    views = db.relationship(
        "PostView",
        back_populates="user",
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

    # ------------------------------------------------------
    # Main Post Image
    # ------------------------------------------------------
    # Kept for compatibility with the existing project.
    # Additional images are stored in PostImage.

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
        nullable=False,
        index=True
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    author = db.relationship(
        "User",
        back_populates="posts"
    )

    images = db.relationship(
        "PostImage",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy=True
    )

    likes = db.relationship(
        "PostLike",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy=True
    )

    comments = db.relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy=True
    )

    views = db.relationship(
        "PostView",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy=True
    )

    # ------------------------------------------------------
    # Helper Properties
    # ------------------------------------------------------

    @property
    def like_count(self):

        return len(self.likes)

    @property
    def comment_count(self):

        return len(self.comments)

    @property
    def view_count(self):

        return len(self.views)

    # ------------------------------------------------------
    # Representation
    # ------------------------------------------------------

    def __repr__(self):

        return f"<Post {self.title}>"


# ==========================================================
# POST IMAGE MODEL
# ==========================================================

class PostImage(db.Model):

    __tablename__ = "post_images"

    # ------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ------------------------------------------------------
    # Image Filename
    # ------------------------------------------------------

    image_filename = db.Column(
        db.String(255),
        nullable=False
    )

    # ------------------------------------------------------
    # Post ID
    # ------------------------------------------------------

    post_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "posts.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ------------------------------------------------------
    # Creation Date
    # ------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ------------------------------------------------------
    # Relationship
    # ------------------------------------------------------

    post = db.relationship(
        "Post",
        back_populates="images"
    )

    # ------------------------------------------------------
    # Representation
    # ------------------------------------------------------

    def __repr__(self):

        return f"<PostImage {self.image_filename}>"


# ==========================================================
# POST LIKE MODEL
# ==========================================================

class PostLike(db.Model):

    __tablename__ = "post_likes"

    # ------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ------------------------------------------------------
    # User ID
    # ------------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ------------------------------------------------------
    # Post ID
    # ------------------------------------------------------

    post_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "posts.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ------------------------------------------------------
    # Creation Date
    # ------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    user = db.relationship(
        "User",
        back_populates="likes"
    )

    post = db.relationship(
        "Post",
        back_populates="likes"
    )

    # ------------------------------------------------------
    # Prevent Multiple Likes
    # ------------------------------------------------------

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "post_id",
            name="unique_user_post_like"
        ),
    )

    # ------------------------------------------------------
    # Representation
    # ------------------------------------------------------

    def __repr__(self):

        return (
            f"<PostLike "
            f"user={self.user_id} "
            f"post={self.post_id}>"
        )


# ==========================================================
# COMMENT MODEL
# ==========================================================

class Comment(db.Model):

    __tablename__ = "comments"

    # ------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ------------------------------------------------------
    # Comment Content
    # ------------------------------------------------------

    content = db.Column(
        db.Text,
        nullable=False
    )

    # ------------------------------------------------------
    # User ID
    # ------------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ------------------------------------------------------
    # Post ID
    # ------------------------------------------------------

    post_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "posts.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
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
    # Relationships
    # ------------------------------------------------------

    user = db.relationship(
        "User",
        back_populates="comments"
    )

    post = db.relationship(
        "Post",
        back_populates="comments"
    )

    # ------------------------------------------------------
    # Representation
    # ------------------------------------------------------

    def __repr__(self):

        return f"<Comment {self.id}>"


# ==========================================================
# POST VIEW MODEL
# ==========================================================

class PostView(db.Model):

    __tablename__ = "post_views"

    # ------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ------------------------------------------------------
    # User ID
    # ------------------------------------------------------
    # NULL is allowed for anonymous visitors.
    #
    # Logged-in users are protected from duplicate views
    # by the application logic in routes.py and this
    # database constraint.

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    # ------------------------------------------------------
    # Post ID
    # ------------------------------------------------------

    post_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "posts.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ------------------------------------------------------
    # View Date
    # ------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    user = db.relationship(
        "User",
        back_populates="views"
    )

    post = db.relationship(
        "Post",
        back_populates="views"
    )

    # ------------------------------------------------------
    # Prevent Duplicate Registered-User Views
    # ------------------------------------------------------
    #
    # This prevents the same logged-in user from having
    # multiple PostView rows for the same post.
    #
    # NOTE:
    # PostgreSQL allows multiple NULL values in a UNIQUE
    # constraint. Therefore this constraint applies to
    # registered users, while anonymous users are protected
    # by session-based tracking in routes.py.

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "post_id",
            name="unique_user_post_view"
        ),
    )

    # ------------------------------------------------------
    # Representation
    # ------------------------------------------------------

    def __repr__(self):

        return (
            f"<PostView "
            f"user={self.user_id} "
            f"post={self.post_id}>"
        )