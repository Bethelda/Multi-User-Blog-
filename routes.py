import os
import uuid
import re

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from flask_login import (
    current_user,
    login_required
)

from sqlalchemy import or_, func

from werkzeug.utils import secure_filename

from db import db

from models import (
    User,
    Post,
    PostLike,
    Comment,
    PostView,
    PostImage
)


# ==========================================================
# MAIN BLUEPRINT
# ==========================================================

main_bp = Blueprint(
    "main",
    __name__
)


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def allowed_file(filename):
    """
    Check whether an uploaded file has an allowed extension.
    """

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    allowed_extensions = current_app.config.get(
        "ALLOWED_EXTENSIONS",
        {
            "jpg",
            "jpeg",
            "png",
            "gif",
            "webp"
        }
    )

    return extension in allowed_extensions


def save_uploaded_file(file):
    """
    Save an uploaded file safely into static/uploads.

    Returns:
        Generated filename if successful.
        None if the file cannot be saved.
    """

    if file is None:
        return None

    if not file.filename:
        return None

    if not allowed_file(file.filename):
        return None

    original_name = secure_filename(
        file.filename
    )

    if not original_name:
        return None

    extension = original_name.rsplit(
        ".",
        1
    )[1].lower()

    unique_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    upload_folder = os.path.join(
        current_app.static_folder,
        "uploads"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_folder,
        unique_filename
    )

    try:

        file.save(file_path)

    except OSError:

        return None

    return unique_filename


def delete_uploaded_file(filename):
    """
    Delete an uploaded file from static/uploads.
    """

    if not filename:
        return

    upload_folder = os.path.join(
        current_app.static_folder,
        "uploads"
    )

    file_path = os.path.join(
        upload_folder,
        filename
    )

    try:

        if os.path.exists(file_path):
            os.remove(file_path)

    except OSError:

        pass


# ==========================================================
# UNIQUE VIEW HELPERS
# ==========================================================

def get_unique_viewers(post_id):
    """
    Return unique registered users who viewed a post.

    Duplicate PostView records are ignored.
    """

    viewers = (
        db.session.query(User)
        .join(
            PostView,
            PostView.user_id == User.id
        )
        .filter(
            PostView.post_id == post_id,
            PostView.user_id.isnot(None)
        )
        .distinct()
        .order_by(
            User.username.asc()
        )
        .all()
    )

    return viewers


def get_unique_view_count(post_id):
    """
    Return the unique view count.

    Registered users:
        Counted only once per post.

    Anonymous users:
        Counted from PostView records created
        through session-based tracking.
    """

    registered_user_views = (
        db.session.query(
            func.count(
                func.distinct(
                    PostView.user_id
                )
            )
        )
        .filter(
            PostView.post_id == post_id,
            PostView.user_id.isnot(None)
        )
        .scalar()
    )

    anonymous_views = (
        db.session.query(
            func.count(PostView.id)
        )
        .filter(
            PostView.post_id == post_id,
            PostView.user_id.is_(None)
        )
        .scalar()
    )

    return (
        (registered_user_views or 0)
        +
        (anonymous_views or 0)
    )


# ==========================================================
# UNIQUE POST VIEW REGISTRATION
# ==========================================================

def register_post_view(post):
    """
    Register one unique view for a post.

    LOGGED-IN USERS:
        One view per user per post.

    ANONYMOUS USERS:
        One view per browser session per post.

    AUTHORS:
        Their own views are not counted.
    """

    if post is None:
        return

    # ======================================================
    # LOGGED-IN USER
    # ======================================================

    if current_user.is_authenticated:

        # --------------------------------------------------
        # Do not count author's own views
        # --------------------------------------------------

        if current_user.id == post.user_id:
            return

        # --------------------------------------------------
        # Check whether this user already viewed this post
        # --------------------------------------------------

        existing_view = (
            PostView.query
            .filter_by(
                user_id=current_user.id,
                post_id=post.id
            )
            .first()
        )

        if existing_view:
            return

        # --------------------------------------------------
        # Create the view
        # --------------------------------------------------

        new_view = PostView(
            user_id=current_user.id,
            post_id=post.id
        )

        try:

            db.session.add(
                new_view
            )

            db.session.commit()

        except Exception:

            # --------------------------------------------------
            # Database UNIQUE constraint protects against
            # duplicate registered-user views.
            # --------------------------------------------------

            db.session.rollback()

        return

    # ======================================================
    # ANONYMOUS USER
    # ======================================================

    viewed_posts = session.get(
        "viewed_posts",
        []
    )

    # ------------------------------------------------------
    # Make sure the session value is a list
    # ------------------------------------------------------

    if not isinstance(viewed_posts, list):

        viewed_posts = []

    post_key = str(
        post.id
    )

    # ------------------------------------------------------
    # Already viewed during this browser session
    # ------------------------------------------------------

    if post_key in viewed_posts:

        return

    # ------------------------------------------------------
    # Create anonymous view
    # ------------------------------------------------------

    new_view = PostView(
        user_id=None,
        post_id=post.id
    )

    try:

        db.session.add(
            new_view
        )

        db.session.commit()

        viewed_posts.append(
            post_key
        )

        session["viewed_posts"] = viewed_posts

        session.modified = True

    except Exception:

        db.session.rollback()


# ==========================================================
# HOME PAGE
# ==========================================================

@main_bp.route("/")
def index():

    posts = (
        Post.query
        .filter_by(
            published=True
        )
        .order_by(
            Post.created_at.desc()
        )
        .all()
    )

    return render_template(
        "index.html",
        posts=posts,
        search_query=""
    )


# ==========================================================
# SEARCH
# ==========================================================

@main_bp.route("/search")
def search():

    search_query = request.args.get(
        "q",
        ""
    ).strip()

    if not search_query:

        return redirect(
            url_for("main.index")
        )

    search_pattern = (
        f"%{search_query}%"
    )

    posts = (
        Post.query
        .filter(
            Post.published.is_(True),
            or_(
                Post.title.ilike(
                    search_pattern
                ),
                Post.content.ilike(
                    search_pattern
                )
            )
        )
        .order_by(
            Post.created_at.desc()
        )
        .all()
    )

    return render_template(
        "index.html",
        posts=posts,
        search_query=search_query
    )


# ==========================================================
# DASHBOARD
# ==========================================================

@main_bp.route("/dashboard")
@login_required
def dashboard():

    posts = (
        Post.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Post.created_at.desc()
        )
        .all()
    )

    return render_template(
        "dashboard.html",
        posts=posts
    )


# ==========================================================
# VIEW SINGLE POST
# ==========================================================

@main_bp.route("/post/<int:post_id>")
def view_post(post_id):

    post = db.session.get(
        Post,
        post_id
    )

    if post is None:

        flash(
            "Post not found.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # ======================================================
    # DRAFT PROTECTION
    # ======================================================

    if not post.published:

        if (
            not current_user.is_authenticated
            or (
                current_user.id != post.user_id
                and current_user.role != "admin"
            )
        ):

            flash(
                "This post is not available.",
                "warning"
            )

            return redirect(
                url_for("main.index")
            )

    # ======================================================
    # REGISTER UNIQUE VIEW
    # ======================================================

    register_post_view(post)

    # ======================================================
    # COMMENTS
    # ======================================================

    comments = (
        Comment.query
        .filter_by(
            post_id=post.id
        )
        .order_by(
            Comment.created_at.desc()
        )
        .all()
    )

    # ======================================================
    # CHECK WHETHER CURRENT USER LIKED THE POST
    # ======================================================

    user_liked = False

    if current_user.is_authenticated:

        user_liked = (
            PostLike.query
            .filter_by(
                user_id=current_user.id,
                post_id=post.id
            )
            .first()
            is not None
        )

    # ======================================================
    # UNIQUE VIEWERS
    # ======================================================

    viewers = get_unique_viewers(
        post.id
    )

    # ======================================================
    # UNIQUE VIEW COUNT
    # ======================================================

    unique_view_count = get_unique_view_count(
        post.id
    )

    # ======================================================
    # RENDER POST PAGE
    # ======================================================

    return render_template(
        "post.html",
        post=post,
        comments=comments,
        user_liked=user_liked,
        viewers=viewers,
        unique_view_count=unique_view_count
    )


# ==========================================================
# CREATE POST
# ==========================================================

@main_bp.route(
    "/create-post",
    methods=["GET", "POST"]
)
@login_required
def create_post():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        content = request.form.get(
            "content",
            ""
        ).strip()

        published = (
            request.form.get(
                "published"
            )
            == "on"
        )

        # --------------------------------------------------
        # Validate title
        # --------------------------------------------------

        if not title:

            flash(
                "Post title is required.",
                "danger"
            )

            return render_template(
                "create_post.html"
            )

        # --------------------------------------------------
        # Validate content
        # --------------------------------------------------

        if not content:

            flash(
                "Post content is required.",
                "danger"
            )

            return render_template(
                "create_post.html"
            )

        # ==================================================
        # MAIN IMAGE
        # ==================================================

        image = request.files.get(
            "image"
        )

        saved_main_image = None

        if image and image.filename:

            if not allowed_file(
                image.filename
            ):

                flash(
                    "Invalid image format. "
                    "Allowed: JPG, JPEG, PNG, GIF, WEBP.",
                    "danger"
                )

                return render_template(
                    "create_post.html"
                )

            saved_main_image = save_uploaded_file(
                image
            )

            if saved_main_image is None:

                flash(
                    "Unable to save the image.",
                    "danger"
                )

                return render_template(
                    "create_post.html"
                )

        # ==================================================
        # ADDITIONAL IMAGES
        # ==================================================

        additional_images = request.files.getlist(
            "images"
        )

        saved_additional_images = []

        for image_file in additional_images:

            if not image_file:
                continue

            if not image_file.filename:
                continue

            if not allowed_file(
                image_file.filename
            ):

                if saved_main_image:
                    delete_uploaded_file(
                        saved_main_image
                    )

                for filename in saved_additional_images:

                    delete_uploaded_file(
                        filename
                    )

                flash(
                    "One or more additional images "
                    "have an invalid format. "
                    "Allowed: JPG, JPEG, PNG, GIF, WEBP.",
                    "danger"
                )

                return render_template(
                    "create_post.html"
                )

            saved_filename = save_uploaded_file(
                image_file
            )

            if saved_filename is None:

                if saved_main_image:
                    delete_uploaded_file(
                        saved_main_image
                    )

                for filename in saved_additional_images:

                    delete_uploaded_file(
                        filename
                    )

                flash(
                    "Unable to save one or more additional images.",
                    "danger"
                )

                return render_template(
                    "create_post.html"
                )

            saved_additional_images.append(
                saved_filename
            )

        # ==================================================
        # CREATE POST OBJECT
        # ==================================================

        post = Post(
            title=title,
            content=content,
            published=published,
            user_id=current_user.id,
            image=saved_main_image
        )

        # ==================================================
        # ADD POST AND ADDITIONAL IMAGES
        # ==================================================

        try:

            db.session.add(
                post
            )

            db.session.flush()

            for filename in saved_additional_images:

                post_image = PostImage(
                    image_filename=filename,
                    post_id=post.id
                )

                db.session.add(
                    post_image
                )

            db.session.commit()

        except Exception:

            db.session.rollback()

            if saved_main_image:

                delete_uploaded_file(
                    saved_main_image
                )

            for filename in saved_additional_images:

                delete_uploaded_file(
                    filename
                )

            flash(
                "Unable to create the post. "
                "Please try again.",
                "danger"
            )

            return render_template(
                "create_post.html"
            )

        flash(
            "Post created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "main.dashboard"
            )
        )

    return render_template(
        "create_post.html"
    )


# ==========================================================
# EDIT POST
# ==========================================================

@main_bp.route(
    "/post/<int:post_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_post(post_id):

    post = db.session.get(
        Post,
        post_id
    )

    if post is None:

        flash(
            "Post not found.",
            "danger"
        )

        return redirect(
            url_for("main.dashboard")
        )

    # ======================================================
    # PERMISSION
    # ======================================================

    if (
        current_user.id != post.user_id
        and current_user.role != "admin"
    ):

        flash(
            "You do not have permission to edit this post.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        content = request.form.get(
            "content",
            ""
        ).strip()

        published = (
            request.form.get(
                "published"
            )
            == "on"
        )

        if not title:

            flash(
                "Post title is required.",
                "danger"
            )

            return render_template(
                "edit_post.html",
                post=post
            )

        if not content:

            flash(
                "Post content is required.",
                "danger"
            )

            return render_template(
                "edit_post.html",
                post=post
            )

        # ==================================================
        # IMAGE REPLACEMENT
        # ==================================================

        image = request.files.get(
            "image"
        )

        old_image = post.image

        new_image = None

        if image and image.filename:

            if not allowed_file(
                image.filename
            ):

                flash(
                    "Invalid image format. "
                    "Allowed: JPG, JPEG, PNG, GIF, WEBP.",
                    "danger"
                )

                return render_template(
                    "edit_post.html",
                    post=post
                )

            new_image = save_uploaded_file(
                image
            )

            if new_image is None:

                flash(
                    "Unable to save the new image.",
                    "danger"
                )

                return render_template(
                    "edit_post.html",
                    post=post
                )

        post.title = title

        post.content = content

        post.published = published

        if new_image:

            post.image = new_image

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            if new_image:

                delete_uploaded_file(
                    new_image
                )

            flash(
                "Unable to update the post.",
                "danger"
            )

            return render_template(
                "edit_post.html",
                post=post
            )

        if new_image and old_image:

            delete_uploaded_file(
                old_image
            )

        flash(
            "Post updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "main.view_post",
                post_id=post.id
            )
        )

    return render_template(
        "edit_post.html",
        post=post
    )


# ==========================================================
# DELETE POST
# ==========================================================

@main_bp.route(
    "/post/<int:post_id>/delete",
    methods=["POST"]
)
@login_required
def delete_post(post_id):

    post = db.session.get(
        Post,
        post_id
    )

    if post is None:

        flash(
            "Post not found.",
            "danger"
        )

        return redirect(
            url_for("main.dashboard")
        )

    if (
        current_user.id != post.user_id
        and current_user.role != "admin"
    ):

        flash(
            "You do not have permission to delete this post.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    main_image = post.image

    additional_images = [
        image.image_filename
        for image in post.images
    ]

    try:

        db.session.delete(
            post
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete the post.",
            "danger"
        )

        return redirect(
            url_for("main.dashboard")
        )

    if main_image:

        delete_uploaded_file(
            main_image
        )

    for filename in additional_images:

        delete_uploaded_file(
            filename
        )

    flash(
        "Post deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.dashboard")
    )


# ==========================================================
# LIKE / UNLIKE POST
# ==========================================================

@main_bp.route(
    "/post/<int:post_id>/like",
    methods=["POST"]
)
@login_required
def like_post(post_id):

    post = db.session.get(
        Post,
        post_id
    )

    if post is None:

        flash(
            "Post not found.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    existing_like = (
        PostLike.query
        .filter_by(
            user_id=current_user.id,
            post_id=post.id
        )
        .first()
    )

    try:

        if existing_like:

            db.session.delete(
                existing_like
            )

            flash(
                "You unliked this post.",
                "success"
            )

        else:

            new_like = PostLike(
                user_id=current_user.id,
                post_id=post.id
            )

            db.session.add(
                new_like
            )

            flash(
                "You liked this post.",
                "success"
            )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update the like.",
            "danger"
        )

    return redirect(
        url_for(
            "main.view_post",
            post_id=post.id
        )
    )


# ==========================================================
# ADD COMMENT
# ==========================================================

@main_bp.route(
    "/post/<int:post_id>/comment",
    methods=["POST"]
)
@login_required
def add_comment(post_id):

    post = db.session.get(
        Post,
        post_id
    )

    if post is None:

        flash(
            "Post not found.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    content = request.form.get(
        "content",
        ""
    ).strip()

    if not content:

        flash(
            "Comment cannot be empty.",
            "danger"
        )

        return redirect(
            url_for(
                "main.view_post",
                post_id=post.id
            )
        )

    comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post.id
    )

    try:

        db.session.add(
            comment
        )

        db.session.commit()

        flash(
            "Comment added successfully.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Unable to add the comment.",
            "danger"
        )

    return redirect(
        url_for(
            "main.view_post",
            post_id=post.id
        )
    )


# ==========================================================
# DELETE COMMENT
# ==========================================================

@main_bp.route(
    "/comment/<int:comment_id>/delete",
    methods=["POST"]
)
@login_required
def delete_comment(comment_id):

    comment = db.session.get(
        Comment,
        comment_id
    )

    if comment is None:

        flash(
            "Comment not found.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    post_id = comment.post_id

    if (
        current_user.id != comment.user_id
        and current_user.role != "admin"
    ):

        flash(
            "You do not have permission to delete this comment.",
            "danger"
        )

        return redirect(
            url_for(
                "main.view_post",
                post_id=post_id
            )
        )

    try:

        db.session.delete(
            comment
        )

        db.session.commit()

        flash(
            "Comment deleted successfully.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete the comment.",
            "danger"
        )

    return redirect(
        url_for(
            "main.view_post",
            post_id=post_id
        )
    )


# ==========================================================
# PROFILE
# ==========================================================

@main_bp.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
def profile():

    if request.method == "POST":

        # ==================================================
        # GET FORM VALUES
        # ==================================================

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip().lower()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        bio = request.form.get(
            "bio",
            ""
        ).strip()

        # ==================================================
        # VALIDATE FULL NAME
        # ==================================================

        if not full_name:

            flash(
                "Full name is required.",
                "danger"
            )

            return render_template(
                "profile.html"
            )

        # ==================================================
        # VALIDATE USERNAME
        # ==================================================

        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return render_template(
                "profile.html"
            )

        if len(username) < 3 or len(username) > 80:

            flash(
                "Username must be between 3 and 80 characters.",
                "danger"
            )

            return render_template(
                "profile.html"
            )

        if not re.fullmatch(
            r"[a-zA-Z0-9_]+",
            username
        ):

            flash(
                "Username can contain only letters, "
                "numbers, and underscores.",
                "danger"
            )

            return render_template(
                "profile.html"
            )

        # ==================================================
        # CHECK USERNAME UNIQUENESS
        # ==================================================

        existing_username = (
            User.query
            .filter(
                func.lower(User.username) == username,
                User.id != current_user.id
            )
            .first()
        )

        if existing_username:

            flash(
                "That username is already taken. "
                "Please choose another username.",
                "danger"
            )

            return render_template(
                "profile.html"
            )

        # ==================================================
        # VALIDATE EMAIL
        # ==================================================

        if not email:

            flash(
                "Email address is required.",
                "danger"
            )

            return render_template(
                "profile.html"
            )

        # ==================================================
        # CHECK EMAIL UNIQUENESS
        # ==================================================

        existing_user = (
            User.query
            .filter(
                User.email == email,
                User.id != current_user.id
            )
            .first()
        )

        if existing_user:

            flash(
                "Another account already uses this email.",
                "danger"
            )

            return render_template(
                "profile.html"
            )

        # ==================================================
        # UPDATE PROFILE INFORMATION
        # ==================================================

        current_user.full_name = full_name

        current_user.username = username

        current_user.email = email

        current_user.bio = bio

        # ==================================================
        # PROFILE IMAGE
        # ==================================================

        profile_image = request.files.get(
            "profile_image"
        )

        old_profile_image = (
            current_user.profile_image
        )

        new_profile_image = None

        if (
            profile_image
            and profile_image.filename
        ):

            if not allowed_file(
                profile_image.filename
            ):

                flash(
                    "Invalid profile image format. "
                    "Allowed: JPG, JPEG, PNG, GIF, WEBP.",
                    "danger"
                )

                return render_template(
                    "profile.html"
                )

            new_profile_image = save_uploaded_file(
                profile_image
            )

            if new_profile_image is None:

                flash(
                    "Unable to save the profile image.",
                    "danger"
                )

                return render_template(
                    "profile.html"
                )

            current_user.profile_image = (
                new_profile_image
            )

        # ==================================================
        # SAVE PROFILE
        # ==================================================

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            if new_profile_image:

                delete_uploaded_file(
                    new_profile_image
                )

            flash(
                "Unable to update your profile.",
                "danger"
            )

            return render_template(
                "profile.html"
            )

        # ==================================================
        # DELETE OLD PROFILE IMAGE
        # ==================================================

        if (
            new_profile_image
            and old_profile_image
        ):

            delete_uploaded_file(
                old_profile_image
            )

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.profile")
        )

    return render_template(
        "profile.html"
    )


# ==========================================================
# PUBLIC USER PROFILE
# ==========================================================

@main_bp.route(
    "/user/<username>"
)
def user_profile(username):

    user = (
        User.query
        .filter(
            func.lower(User.username) == username.lower()
        )
        .first()
    )

    if user is None:

        flash(
            "User profile not found.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # ======================================================
    # USER'S PUBLISHED POSTS
    # ======================================================

    posts = (
        Post.query
        .filter(
            Post.user_id == user.id,
            Post.published.is_(True)
        )
        .order_by(
            Post.created_at.desc()
        )
        .all()
    )

    return render_template(
        "user_profile.html",
        user=user,
        posts=posts
    )