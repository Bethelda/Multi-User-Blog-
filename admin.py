from functools import wraps

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from db import db
from models import User, Post


# ==========================================================
# ADMIN BLUEPRINT
# ==========================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ==========================================================
# ADMIN ACCESS DECORATOR
# ==========================================================

def admin_required(function):
    """
    Allow access only to authenticated administrators.
    """

    @wraps(function)
    @login_required
    def decorated_function(*args, **kwargs):

        if current_user.role != "admin":

            flash(
                "Administrator access is required.",
                "danger"
            )

            return redirect(
                url_for("main.index")
            )

        return function(
            *args,
            **kwargs
        )

    return decorated_function


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@admin_bp.route("/")
@admin_required
def dashboard():

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    posts = Post.query.order_by(
        Post.created_at.desc()
    ).all()

    return render_template(
        "admin_dashboard.html",
        users=users,
        posts=posts
    )


# ==========================================================
# MAKE USER ADMIN
# ==========================================================

@admin_bp.route(
    "/user/<int:user_id>/make-admin",
    methods=["POST"]
)
@admin_required
def make_admin(user_id):

    user = db.session.get(
        User,
        user_id
    )


    if user is None:

        flash(
            "User not found.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    if user.id == current_user.id:

        flash(
            "You are already an administrator.",
            "warning"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    user.role = "admin"


    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to change the user's role.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    flash(
        f"{user.username} is now an administrator.",
        "success"
    )


    return redirect(
        url_for("admin.dashboard")
    )


# ==========================================================
# REMOVE ADMIN ROLE
# ==========================================================

@admin_bp.route(
    "/user/<int:user_id>/make-user",
    methods=["POST"]
)
@admin_required
def make_user(user_id):

    user = db.session.get(
        User,
        user_id
    )


    if user is None:

        flash(
            "User not found.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    if user.id == current_user.id:

        flash(
            "You cannot remove your own administrator role.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    user.role = "user"


    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to change the user's role.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    flash(
        f"{user.username} is now a normal user.",
        "success"
    )


    return redirect(
        url_for("admin.dashboard")
    )


# ==========================================================
# DELETE USER
# ==========================================================

@admin_bp.route(
    "/user/<int:user_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_user(user_id):

    user = db.session.get(
        User,
        user_id
    )


    if user is None:

        flash(
            "User not found.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    # ------------------------------------------------------
    # Prevent administrator from deleting themselves
    # ------------------------------------------------------

    if user.id == current_user.id:

        flash(
            "You cannot delete your own account from the admin dashboard.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    # ------------------------------------------------------
    # Delete user
    # ------------------------------------------------------

    try:

        db.session.delete(user)

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete the user.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    flash(
        f"User {user.username} was deleted successfully.",
        "success"
    )


    return redirect(
        url_for("admin.dashboard")
    )


# ==========================================================
# DELETE POST
# ==========================================================

@admin_bp.route(
    "/post/<int:post_id>/delete",
    methods=["POST"]
)
@admin_required
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
            url_for("admin.dashboard")
        )


    try:

        db.session.delete(post)

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete the post.",
            "danger"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    flash(
        "Post deleted successfully.",
        "success"
    )


    return redirect(
        url_for("admin.dashboard")
    )