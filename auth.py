from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from db import db
from models import User


# ==========================================================
# AUTHENTICATION BLUEPRINT
# ==========================================================

auth_bp = Blueprint(
    "auth",
    __name__
)


# ==========================================================
# REGISTER
# ==========================================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    # ------------------------------------------------------
    # If already logged in
    # ------------------------------------------------------

    if current_user.is_authenticated:

        return redirect(
            url_for("main.dashboard")
        )


    # ------------------------------------------------------
    # Handle form submission
    # ------------------------------------------------------

    if request.method == "POST":

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


        password = request.form.get(
            "password",
            ""
        )


        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        # --------------------------------------------------
        # Validate required fields
        # --------------------------------------------------

        if not full_name:

            flash(
                "Full name is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if not email:

            flash(
                "Email address is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        # --------------------------------------------------
        # Validate username
        # --------------------------------------------------

        if len(username) < 3:

            flash(
                "Username must contain at least 3 characters.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if len(username) > 80:

            flash(
                "Username is too long.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        # --------------------------------------------------
        # Validate password
        # --------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        # --------------------------------------------------
        # Confirm password
        # --------------------------------------------------

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        # --------------------------------------------------
        # Check username
        # --------------------------------------------------

        existing_username = User.query.filter_by(
            username=username
        ).first()


        if existing_username:

            flash(
                "Username is already taken.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        # --------------------------------------------------
        # Check email
        # --------------------------------------------------

        existing_email = User.query.filter_by(
            email=email
        ).first()


        if existing_email:

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        # --------------------------------------------------
        # Create user
        # --------------------------------------------------

        user = User(

            full_name=full_name,

            username=username,

            email=email,

            role="user"

        )


        user.set_password(
            password
        )


        # --------------------------------------------------
        # Save user
        # --------------------------------------------------

        try:

            db.session.add(user)

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Unable to create the account. Please try again.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        flash(
            "Registration successful. You can now log in.",
            "success"
        )


        return redirect(
            url_for("auth.login")
        )


    # ------------------------------------------------------
    # Display registration page
    # ------------------------------------------------------

    return render_template(
        "register.html"
    )


# ==========================================================
# LOGIN
# ==========================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # ------------------------------------------------------
    # If already logged in
    # ------------------------------------------------------

    if current_user.is_authenticated:

        return redirect(
            url_for("main.dashboard")
        )


    # ------------------------------------------------------
    # Handle login
    # ------------------------------------------------------

    if request.method == "POST":

        username_or_email = request.form.get(
            "username",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        # --------------------------------------------------
        # Validate
        # --------------------------------------------------

        if not username_or_email:

            flash(
                "Username or email is required.",
                "danger"
            )

            return render_template(
                "login.html"
            )


        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return render_template(
                "login.html"
            )


        # --------------------------------------------------
        # Find user
        # --------------------------------------------------

        user = User.query.filter(
            db.or_(
                User.username == username_or_email,
                User.email == username_or_email
            )
        ).first()


        # --------------------------------------------------
        # Check credentials
        # --------------------------------------------------

        if user is None or not user.check_password(
            password
        ):

            flash(
                "Invalid username/email or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )


        # --------------------------------------------------
        # Login user
        # --------------------------------------------------

        login_user(
            user,
            remember=True
        )


        flash(
            f"Welcome back, {user.full_name}!",
            "success"
        )


        # --------------------------------------------------
        # Redirect
        # --------------------------------------------------

        next_page = request.args.get(
            "next"
        )


        if next_page and next_page.startswith("/"):

            return redirect(
                next_page
            )


        return redirect(
            url_for("main.dashboard")
        )


    return render_template(
        "login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@auth_bp.route(
    "/logout"
)
@login_required
def logout():

    logout_user()


    flash(
        "You have been logged out successfully.",
        "success"
    )


    return redirect(
        url_for("main.index")
    )