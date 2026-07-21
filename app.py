import os
import uuid

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename


# Load values from the .env file
load_dotenv()


# ---------------------------------------------------------
# Flask application configuration
# ---------------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "temporary-development-key",
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///interiorspace.db",
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "images",
)

# Maximum total size of one upload request: 20 MB
# This is increased because similar photos can be uploaded together.
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
}


# ---------------------------------------------------------
# Flask extensions
# ---------------------------------------------------------

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


# ---------------------------------------------------------
# Database models
# ---------------------------------------------------------

class User(db.Model, UserMixin):
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
    )

    password = db.Column(
        db.String(255),
        nullable=False,
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="user",
    )

    def __repr__(self):
        return f"<User {self.email}>"


class Design(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    title = db.Column(
        db.String(100),
        nullable=False,
    )

    category = db.Column(
        db.String(50),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    image = db.Column(
        db.String(255),
        nullable=False,
    )

    similar_images = db.relationship(
        "DesignImage",
        backref="design",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Design {self.title}>"


class DesignImage(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    image = db.Column(
        db.String(255),
        nullable=False,
    )

    design_id = db.Column(
        db.Integer,
        db.ForeignKey("design.id"),
        nullable=False,
    )

    def __repr__(self):
        return f"<DesignImage {self.image}>"



class RequestResponse(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    custom_request_id = db.Column(
        db.Integer,
        db.ForeignKey("custom_request.id"),
        unique=True,
        nullable=False,
    )

    admin_message = db.Column(
        db.Text,
        nullable=True,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    custom_request = db.relationship(
        "CustomRequest",
        backref=db.backref(
            "response",
            uselist=False,
            cascade="all, delete-orphan",
        ),
    )

    def __repr__(self):
        return f"<RequestResponse {self.custom_request_id}>"


class CustomRequest(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    email = db.Column(
        db.String(150),
        nullable=False,
    )

    room_type = db.Column(
        db.String(100),
        nullable=False,
    )

    preferred_style = db.Column(
        db.String(100),
        nullable=False,
    )

    budget = db.Column(
        db.String(100),
        nullable=True,
    )

    requirements = db.Column(
        db.Text,
        nullable=False,
    )

    suggestions = db.Column(
        db.Text,
        nullable=True,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Pending",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.current_timestamp(),
    )

    def __repr__(self):
        return f"<CustomRequest {self.name} - {self.room_type}>"


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def create_unique_filename(original_filename):
    """
    Creates a unique safe filename.

    Example:
    living-room.jpg becomes:
    8fabc123_living-room.jpg
    """

    safe_filename = secure_filename(original_filename)
    unique_value = uuid.uuid4().hex

    return f"{unique_value}_{safe_filename}"


def delete_image_file(filename):
    """
    Removes an image from static/images when it exists.
    """

    if not filename:
        return

    image_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename,
    )

    if os.path.isfile(image_path):
        try:
            os.remove(image_path)
        except OSError:
            pass


# ---------------------------------------------------------
# Flask-Login user loader
# ---------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(
        User,
        int(user_id),
    )


# ---------------------------------------------------------
# Public routes
# ---------------------------------------------------------
@app.route("/")
def home():

    featured_designs = (
        Design.query
        .order_by(Design.id.desc())
        .limit(3)
        .all()
    )

    return render_template(
        "index.html",
        featured_designs=featured_designs
    )

@app.route("/gallery")
def gallery():
    designs = Design.query.order_by(
        Design.id.desc(),
    ).all()

    return render_template(
        "gallery.html",
        designs=designs,
    )


@app.route("/design/<int:design_id>")
def design_details(design_id):
    design = db.get_or_404(
        Design,
        design_id,
    )

    return render_template(
        "design_details.html",
        design=design,
    )



@app.route(
    "/custom-request",
    methods=["GET", "POST"],
)
def custom_request():
    if request.method == "POST":
        name = request.form.get(
            "name",
            "",
        ).strip()

        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        room_type = request.form.get(
            "room_type",
            "",
        ).strip()

        preferred_style = request.form.get(
            "preferred_style",
            "",
        ).strip()

        budget = request.form.get(
            "budget",
            "",
        ).strip()

        requirements = request.form.get(
            "requirements",
            "",
        ).strip()

        suggestions = request.form.get(
            "suggestions",
            "",
        ).strip()

        if (
            not name
            or not email
            or not room_type
            or not preferred_style
            or not requirements
        ):
            flash(
                "Please complete all required fields.",
                "danger",
            )
            return redirect(url_for("custom_request"))

        new_request = CustomRequest(
            name=name,
            email=email,
            room_type=room_type,
            preferred_style=preferred_style,
            budget=budget,
            requirements=requirements,
            suggestions=suggestions,
        )

        db.session.add(new_request)
        db.session.commit()

        flash(
            "Your custom design request was submitted successfully.",
            "success",
        )

        return redirect(url_for("custom_request"))

    return render_template("custom_request.html")


# ---------------------------------------------------------
# Registration and login routes
# ---------------------------------------------------------

@app.route(
    "/register",
    methods=["GET", "POST"],
)
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get(
            "name",
            "",
        ).strip()

        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        password = request.form.get(
            "password",
            "",
        )

        confirm_password = request.form.get(
            "confirm_password",
            "",
        )

        if (
            not name
            or not email
            or not password
            or not confirm_password
        ):
            flash(
                "Please complete all required fields.",
                "danger",
            )
            return redirect(url_for("register"))

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "danger",
            )
            return redirect(url_for("register"))

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "danger",
            )
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(
            email=email,
        ).first()

        if existing_user:
            flash(
                "An account with that email already exists.",
                "warning",
            )
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(
            password,
        ).decode("utf-8")

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
        )

        db.session.add(new_user)
        db.session.commit()

        flash(
            "Account created successfully. You can now log in.",
            "success",
        )

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route(
    "/login",
    methods=["GET", "POST"],
)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        password = request.form.get(
            "password",
            "",
        )

        user = User.query.filter_by(
            email=email,
        ).first()

        if (
            user
            and bcrypt.check_password_hash(
                user.password,
                password,
            )
        ):
            login_user(user)

            flash(
                f"Welcome back, {user.name}!",
                "success",
            )

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email address or password.",
            "danger",
        )

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()

    flash(
        "You have been logged out successfully.",
        "success",
    )

    return redirect(url_for("home"))


# ---------------------------------------------------------
# User dashboard
# ---------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    customer_requests = CustomRequest.query.filter(
        db.func.lower(CustomRequest.email)
        == current_user.email.lower()
    ).order_by(
        CustomRequest.created_at.desc(),
    ).all()

    request_counts = {
        "total": len(customer_requests),
        "pending": sum(
            1
            for item in customer_requests
            if item.status == "Pending"
        ),
        "accepted": sum(
            1
            for item in customer_requests
            if item.status == "Accepted"
        ),
        "rejected": sum(
            1
            for item in customer_requests
            if item.status == "Rejected"
        ),
    }

    return render_template(
        "dashboard.html",
        customer_requests=customer_requests,
        request_counts=request_counts,
    )


# ---------------------------------------------------------
# Admin: view submitted customer requests
# ---------------------------------------------------------

@app.route("/admin/requests")
@login_required
def admin_requests():
    if current_user.role != "admin":
        flash(
            "You are not authorized to access this page.",
            "danger",
        )
        return redirect(url_for("dashboard"))

    custom_requests = CustomRequest.query.order_by(
        CustomRequest.created_at.desc(),
    ).all()

    return render_template(
        "admin_requests.html",
        custom_requests=custom_requests,
    )


# ---------------------------------------------------------
# Admin: accept or reject customer requests
# ---------------------------------------------------------

@app.route(
    "/admin/request/<int:request_id>/accept",
    methods=["POST"],
)
@login_required
def accept_custom_request(request_id):
    if current_user.role != "admin":
        flash(
            "You are not authorized to perform this action.",
            "danger",
        )
        return redirect(url_for("dashboard"))

    custom_request_record = db.get_or_404(
        CustomRequest,
        request_id,
    )

    admin_message = request.form.get(
        "admin_message",
        "",
    ).strip()

    custom_request_record.status = "Accepted"

    if custom_request_record.response:
        custom_request_record.response.admin_message = admin_message
    else:
        db.session.add(
            RequestResponse(
                custom_request_id=custom_request_record.id,
                admin_message=admin_message,
            )
        )

    db.session.commit()

    flash(
        f"Request from {custom_request_record.name} was accepted.",
        "success",
    )

    return redirect(url_for("admin_requests"))


@app.route(
    "/admin/request/<int:request_id>/reject",
    methods=["POST"],
)
@login_required
def reject_custom_request(request_id):
    if current_user.role != "admin":
        flash(
            "You are not authorized to perform this action.",
            "danger",
        )
        return redirect(url_for("dashboard"))

    custom_request_record = db.get_or_404(
        CustomRequest,
        request_id,
    )

    admin_message = request.form.get(
        "admin_message",
        "",
    ).strip()

    custom_request_record.status = "Rejected"

    if custom_request_record.response:
        custom_request_record.response.admin_message = admin_message
    else:
        db.session.add(
            RequestResponse(
                custom_request_id=custom_request_record.id,
                admin_message=admin_message,
            )
        )

    db.session.commit()

    flash(
        f"Request from {custom_request_record.name} was rejected.",
        "warning",
    )

    return redirect(url_for("admin_requests"))


# ---------------------------------------------------------
# Admin: create and list designs
# ---------------------------------------------------------

@app.route(
    "/admin",
    methods=["GET", "POST"],
)
@login_required
def admin():
    if current_user.role != "admin":
        flash(
            "You are not authorized to access the admin panel.",
            "danger",
        )
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get(
            "title",
            "",
        ).strip()

        category = request.form.get(
            "category",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        ).strip()

        image_file = request.files.get("image")

        if (
            not title
            or not category
            or not description
            or not image_file
        ):
            flash(
                "Please complete every design field.",
                "danger",
            )
            return redirect(url_for("admin"))

        if image_file.filename == "":
            flash(
                "Please select an image.",
                "danger",
            )
            return redirect(url_for("admin"))

        if not allowed_file(image_file.filename):
            flash(
                "Only PNG, JPG, JPEG, and WEBP images are allowed.",
                "danger",
            )
            return redirect(url_for("admin"))

        filename = create_unique_filename(
            image_file.filename,
        )

        os.makedirs(
            app.config["UPLOAD_FOLDER"],
            exist_ok=True,
        )

        image_file.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename,
            )
        )

        new_design = Design(
            title=title,
            category=category,
            description=description,
            image=filename,
        )

        db.session.add(new_design)
        db.session.commit()

        flash(
            "Interior design added successfully.",
            "success",
        )

        return redirect(url_for("admin"))

    designs = Design.query.order_by(
        Design.id.desc(),
    ).all()

    return render_template(
        "admin.html",
        designs=designs,
    )


# ---------------------------------------------------------
# Admin: upload similar photos
# ---------------------------------------------------------

@app.route(
    "/admin/design/<int:design_id>/images",
    methods=["POST"],
)
@login_required
def add_design_images(design_id):
    if current_user.role != "admin":
        flash(
            "You are not authorized to perform this action.",
            "danger",
        )
        return redirect(url_for("dashboard"))

    design = db.get_or_404(
        Design,
        design_id,
    )

    uploaded_images = request.files.getlist(
        "similar_images"
    )

    if not uploaded_images:
        flash(
            "Please select at least one similar photo.",
            "danger",
        )
        return redirect(url_for("admin"))

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True,
    )

    saved_count = 0
    invalid_count = 0

    for image_file in uploaded_images:
        if (
            not image_file
            or image_file.filename == ""
        ):
            continue

        if not allowed_file(image_file.filename):
            invalid_count += 1
            continue

        filename = create_unique_filename(
            image_file.filename,
        )

        image_file.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename,
            )
        )

        similar_image = DesignImage(
            image=filename,
            design_id=design.id,
        )

        db.session.add(similar_image)
        saved_count += 1

    if saved_count == 0:
        flash(
            "No valid photos were selected. "
            "Use PNG, JPG, JPEG, or WEBP files.",
            "danger",
        )
        return redirect(url_for("admin"))

    db.session.commit()

    if invalid_count > 0:
        flash(
            f"{saved_count} similar photo(s) uploaded. "
            f"{invalid_count} invalid file(s) were skipped.",
            "warning",
        )
    else:
        flash(
            f"{saved_count} similar photo(s) "
            "uploaded successfully.",
            "success",
        )

    return redirect(url_for("admin"))


# ---------------------------------------------------------
# Admin: delete one similar photo
# ---------------------------------------------------------

@app.route(
    "/admin/design-image/<int:image_id>/delete",
    methods=["POST"],
)
@login_required
def delete_design_image(image_id):
    if current_user.role != "admin":
        flash(
            "You are not authorized to perform this action.",
            "danger",
        )
        return redirect(url_for("dashboard"))

    similar_image = db.get_or_404(
        DesignImage,
        image_id,
    )

    delete_image_file(similar_image.image)

    db.session.delete(similar_image)
    db.session.commit()

    flash(
        "Similar photo deleted successfully.",
        "success",
    )

    return redirect(url_for("admin"))


# ---------------------------------------------------------
# Admin: edit a design
# ---------------------------------------------------------

@app.route(
    "/admin/design/<int:design_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit_design(design_id):
    if current_user.role != "admin":
        flash(
            "You are not authorized to access this page.",
            "danger",
        )
        return redirect(url_for("dashboard"))

    design = db.get_or_404(
        Design,
        design_id,
    )

    if request.method == "POST":
        title = request.form.get(
            "title",
            "",
        ).strip()

        category = request.form.get(
            "category",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        ).strip()

        # This supports an optional new image upload.
        new_image_file = request.files.get("image")

        if not title or not category or not description:
            flash(
                "Please complete every required field.",
                "danger",
            )

            return render_template(
                "edit_design.html",
                design=design,
            )

        design.title = title
        design.category = category
        design.description = description

        if (
            new_image_file
            and new_image_file.filename != ""
        ):
            if not allowed_file(new_image_file.filename):
                flash(
                    "Only PNG, JPG, JPEG, and WEBP images "
                    "are allowed.",
                    "danger",
                )

                return render_template(
                    "edit_design.html",
                    design=design,
                )

            new_filename = create_unique_filename(
                new_image_file.filename,
            )

            new_image_file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    new_filename,
                )
            )

            old_filename = design.image
            design.image = new_filename

            delete_image_file(old_filename)

        db.session.commit()

        flash(
            "Interior design updated successfully.",
            "success",
        )

        return redirect(url_for("admin"))

    return render_template(
        "edit_design.html",
        design=design,
    )


# ---------------------------------------------------------
# Admin: delete a complete design
# ---------------------------------------------------------

@app.route(
    "/admin/design/<int:design_id>/delete",
    methods=["POST"],
)
@login_required
def delete_design(design_id):
    if current_user.role != "admin":
        flash(
            "You are not authorized to perform this action.",
            "danger",
        )
        return redirect(url_for("dashboard"))

    design = db.get_or_404(
        Design,
        design_id,
    )

    # Remove the main image file.
    delete_image_file(design.image)

    # Remove all similar-image files.
    for similar_image in design.similar_images:
        delete_image_file(similar_image.image)

    # Related DesignImage database records are deleted
    # automatically because cascade is configured.
    db.session.delete(design)
    db.session.commit()

    flash(
        "Interior design and its photos deleted successfully.",
        "success",
    )

    return redirect(url_for("admin"))


# ---------------------------------------------------------
# Application startup
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False,
    )