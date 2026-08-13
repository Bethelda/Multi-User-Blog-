import os
import uuid

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_required
)

from sqlalchemy import or_

from werkzeug.utils import secure_filename

from db import db
from models import Post


# ==========================================================
# MAIN BLUEPRINT
# ==========================================================

main_bp = Blueprint(
    "main",
    __name__
)


# ==========================================================
# FILE UPLOAD FUNCTIONS
# ==========================================================

def allowed_file(filename):
    """
    Check whether the uploaded file is an allowed image.
    """

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    allowed_extensions = current_app.config.get(
        "ALLOWED_EXTENSIONS",
        {"png", "jpg", "jpeg", "gif", "webp"}
    )

    return extension in allowed_extensions


def save_uploaded_file(file):
    """
    Save an uploaded image to static/uploads.
    """

    if not file or not file.filename:
        return None

    if not allowed_file(file.filename):
        return None

    original_filename = secure_filename(
        file.filename
    )

    if "." not in original_filename:
        return None

    extension = original_filename.rsplit(
        ".",
        1
    )[1].lower()

    filename = f"{uuid.uuid4().hex}.{extension}"

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
        filename
    )

    file.save(file_path)

    return filename


def delete_uploaded_file(filename):
    """
    Delete an uploaded image.
    """

    if not filename:
        return

    file_path = os.path.join(
        current_app.static_folder,
        "uploads",
        filename
    )

    if os.path.isfile(file_path):

        try:
            os.remove(file_path)

        except OSError:
            pass


# ==========================================================
# HOME PAGE
# ==========================================================

@main_bp.route("/")
def index():

    posts = (
        Post.query
        .filter_by(published=True)
        .order_by(Post.created_at.desc())
        .all()
    )

    return render_template(
        "index.html",
        posts=posts
    )


# ==========================================================
# POST DETAILS
# ==========================================================

@main_bp.route("/post/<int:post_id>")
def view_post(post_id):

    post = Post.query.get_or_404(post_id)

    return render_template(
        "post.html",
        post=post
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

        published = request.form.get(
            "published"
        )

        image = request.files.get(
            "image"
        )

        if not title:

            flash(
                "Please enter a post title.",
                "danger"
            )

            return render_template(
                "create_post.html"
            )

        if not content:

            flash(
                "Please enter post content.",
                "danger"
            )

            return render_template(
                "create_post.html"
            )

        image_filename = None

        if image and image.filename:

            image_filename = save_uploaded_file(
                image
            )

            if image_filename is None:

                flash(
                    "Invalid image file.",
                    "danger"
                )

                return render_template(
                    "create_post.html"
                )

        post = Post(
            title=title,
            content=content,
            image=image_filename,
            published=published == "on",
            user_id=current_user.id
        )

        db.session.add(post)
        db.session.commit()

        flash(
            "Post created successfully!",
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
    "/edit-post/<int:post_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_post(post_id):

    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:

        flash(
            "You are not allowed to edit this post.",
            "danger"
        )

        return redirect(
            url_for(
                "main.dashboard"
            )
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

        published = request.form.get(
            "published"
        )

        image = request.files.get(
            "image"
        )

        if not title:

            flash(
                "Please enter a post title.",
                "danger"
            )

            return render_template(
                "edit_post.html",
                post=post
            )

        if not content:

            flash(
                "Please enter post content.",
                "danger"
            )

            return render_template(
                "edit_post.html",
                post=post
            )

        post.title = title
        post.content = content
        post.published = published == "on"

        if image and image.filename:

            new_image = save_uploaded_file(
                image
            )

            if new_image is None:

                flash(
                    "Invalid image file.",
                    "danger"
                )

                return render_template(
                    "edit_post.html",
                    post=post
                )

            old_image = post.image

            post.image = new_image

            if old_image:

                delete_uploaded_file(
                    old_image
                )

        db.session.commit()

        flash(
            "Post updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "main.dashboard"
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
    "/delete-post/<int:post_id>",
    methods=["POST"]
)
@login_required
def delete_post(post_id):

    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:

        flash(
            "You are not allowed to delete this post.",
            "danger"
        )

        return redirect(
            url_for(
                "main.dashboard"
            )
        )

    image = post.image

    db.session.delete(post)
    db.session.commit()

    if image:

        delete_uploaded_file(
            image
        )

    flash(
        "Post deleted successfully!",
        "success"
    )

    return redirect(
        url_for(
            "main.dashboard"
        )
    )


# ==========================================================
# PROFILE
# ==========================================================

@main_bp.route(
    "/profile",
    methods=["GET"]
)
@login_required
def profile():

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
        "profile.html",
        user=current_user,
        posts=posts
    )


# ==========================================================
# UPDATE PROFILE
# ==========================================================

@main_bp.route(
    "/profile",
    methods=["POST"]
)
@login_required
def update_profile():

    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    bio = request.form.get(
        "bio",
        ""
    ).strip()

    profile_image = request.files.get(
        "profile_image"
    )

    if not full_name:

        flash(
            "Full name is required.",
            "danger"
        )

        return redirect(
            url_for(
                "main.profile"
            )
        )

    current_user.full_name = full_name
    current_user.bio = bio

    if profile_image and profile_image.filename:

        new_image = save_uploaded_file(
            profile_image
        )

        if new_image is None:

            flash(
                "Invalid profile image.",
                "danger"
            )

            return redirect(
                url_for(
                    "main.profile"
                )
            )

        old_image = current_user.profile_image

        current_user.profile_image = new_image

        if old_image:

            delete_uploaded_file(
                old_image
            )

    db.session.commit()

    flash(
        "Profile updated successfully!",
        "success"
    )

    return redirect(
        url_for(
            "main.profile"
        )
    )


# ==========================================================
# SEARCH POSTS
# ==========================================================

@main_bp.route("/search")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return render_template(
            "index.html",
            posts=[],
            search_query=""
        )

    search_term = f"%{query}%"

    posts = (
        Post.query
        .filter(
            Post.published.is_(True),
            or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term)
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
        search_query=query
    )