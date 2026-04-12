from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Company, Student, PlacementDrive, Application
from forms import LoginForm, StudentRegisterForm, CompanyRegisterForm
import os
from datetime import date


app = Flask(__name__)
app.config["SECRET_KEY"] = "placement-portal-secret-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def seed_admin():
    if not User.query.filter_by(role="admin").first():
        admin = User(email="admin@placement.edu", role="admin", is_active=True)
        admin.set_password("Admin@1234")
        db.session.add(admin)
        db.session.commit()
        print("Admin seeded: admin@placement.edu / Admin@1234")

# routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form)

        if user.is_blacklisted:
            flash("Your account has been blacklisted. Contact the admin.", "danger")
            return render_template("login.html", form=form)

        if not user.is_active:
            flash("Your account is inactive.", "danger")
            return render_template("login.html", form=form)

        if user.role == "company":
            company = Company.query.filter_by(user_id=user.id).first()
            if not company or company.approval_status != "Approved":
                flash("Your company registration is pending admin approval.", "warning")
                return render_template("login.html", form=form)
            if company and company.approval_status == "Rejected":
                flash("Your company registration was rejected. Contact admin.", "danger")
                return render_template("login.html", form=form)
            if company and company.approval_status == "Blacklisted":
                flash("Your company has been blacklisted.", "danger")
                return render_template("login.html", form=form)

        login_user(user, remember=form.remember.data)
        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard"))

    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("register_choice.html")


@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = StudentRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash("Email already registered.", "danger")
            return render_template("register_student.html", form=form)

        # check duplicate student ID
        if Student.query.filter_by(student_id=form.student_id.data.strip()).first():
            flash("Student ID already registered.", "danger")
            return render_template("register_student.html", form=form)

        # handle resume upload
        resume_link = form.resume_link.data.strip()

        user = User(email=form.email.data.strip().lower(), role="student")
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # get user.id

        student = Student(
            user_id=user.id,
            name=form.name.data.strip(),
            student_id=form.student_id.data.strip(),
            branch=form.branch.data.strip(),
            graduation_year=form.graduation_year.data,
            cgpa=form.cgpa.data,
            phone=form.phone.data.strip(),
            skills=form.skills.data.strip(),
            resume_link=resume_link,
        )
        db.session.add(student)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register_student.html", form=form)


@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = CompanyRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash("Email already registered.", "danger")
            return render_template("register_company.html", form=form)

        user = User(email=form.email.data.strip().lower(), role="company")
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.id,
            name=form.company_name.data.strip(),
            hr_contact=form.hr_contact.data.strip(),
            hr_email=form.hr_email.data.strip().lower(),
            website=form.website.data.strip(),
            description=form.description.data.strip(),
            approval_status="Pending",
        )
        db.session.add(company)
        db.session.commit()

        flash("Company registered! Await admin approval before logging in.", "info")
        return redirect(url_for("login"))

    return render_template("register_company.html", form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif current_user.role == "company":
        return redirect(url_for("company_dashboard"))
    else:
        return redirect(url_for("student_dashboard"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))
    from models import PlacementDrive, Application
    stats = {
        "students": Student.query.count(),
        "companies": Company.query.count(),
        "drives": PlacementDrive.query.count(),
        "applications": Application.query.count(),
        "pending_companies": Company.query.filter_by(approval_status="Pending").count(),
    }
    return render_template("dashboard_admin.html", stats=stats)


@app.route("/company/dashboard")
@login_required
def company_dashboard():
    if current_user.role != "company":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))
    company = Company.query.filter_by(user_id=current_user.id).first()
    return render_template("dashboard_company.html", company=company)


@app.route("/student/dashboard")
@login_required
def student_dashboard():
    if current_user.role != "student":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))
    student = Student.query.filter_by(user_id=current_user.id).first()
    return render_template("dashboard_student.html", student=student)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/drives")
@login_required
def drives():
    if current_user.role != "student":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    student = Student.query.filter_by(user_id=current_user.id).first()

    drives = PlacementDrive.query.filter_by(status="Approved").all()

    return render_template("drives.html", drives=drives, student=student)


@app.route("/apply/<int:drive_id>")
@login_required
def apply_drive(drive_id):
    if current_user.role != "student":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    student = Student.query.filter_by(user_id=current_user.id).first()
    drive = PlacementDrive.query.get_or_404(drive_id)

    existing = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive.id
    ).first()

    if existing:
        flash("You have already applied to this drive.", "warning")
        return redirect(url_for("view_drives"))

    if drive.deadline < date.today():
        flash("Application deadline has passed.", "danger")
        return redirect(url_for("view_drives"))

    if student.cgpa < drive.min_cgpa:
        flash("You do not meet the CGPA requirement.", "danger")
        return redirect(url_for("view_drives"))

    if drive.status != "Approved":
        flash("This drive is not open for applications.", "danger")
        return redirect(url_for("view_drives"))

    application = Application(
        student_id=student.id,
        drive_id=drive.id,
        status="Applied"
    )

    db.session.add(application)
    db.session.commit()

    flash("Application submitted successfully!", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/company/create-drive", methods=["GET", "POST"])
@login_required
def create_drive():
    if current_user.role != "company":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    company = Company.query.filter_by(user_id=current_user.id).first()

    if not company.is_approved:
        flash("Your company is not approved yet.", "warning")
        return redirect(url_for("company_dashboard"))

    if request.method == "POST":
        drive = PlacementDrive(
            company_id=company.id,
            job_title=request.form.get("job_title"),
            job_type=request.form.get("job_type"),
            description=request.form.get("description"),
            eligibility=request.form.get("eligibility"),
            min_cgpa=float(request.form.get("min_cgpa") or 0),
            location=request.form.get("location"),
            salary_range=request.form.get("salary_range"),
            deadline=date.fromisoformat(request.form.get("deadline")),
            status="Pending"
        )

        db.session.add(drive)
        db.session.commit()

        flash("Drive created and sent for admin approval.", "success")
        return redirect(url_for("company_dashboard"))

    return render_template("create_drive.html")



@app.route("/admin/approve-drive/<int:drive_id>")
@login_required
def approve_drive(drive_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "Approved"

    db.session.commit()

    flash("Drive approved successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject-drive/<int:drive_id>")
@login_required
def reject_drive(drive_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "Rejected"

    db.session.commit()

    flash("Drive rejected.", "danger")
    return redirect(url_for("admin_dashboard"))

@app.route("/company/applications/<int:drive_id>")
@login_required
def view_applications(drive_id):
    if current_user.role != "company":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    drive = PlacementDrive.query.get_or_404(drive_id)

    applications = drive.applications.all()

    return render_template("applications.html", drive=drive, applications=applications)


@app.route("/application/<int:app_id>/update/<status>")
@login_required
def update_application(app_id, status):
    if current_user.role != "company":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    application = Application.query.get_or_404(app_id)

    valid_status = ["Shortlisted", "Selected", "Rejected"]

    if status not in valid_status:
        flash("Invalid status.", "danger")
        return redirect(url_for("company_dashboard"))

    application.status = status
    db.session.commit()

    flash(f"Application marked as {status}.", "success")
    return redirect(request.referrer)


@app.route("/my-applications")
@login_required
def my_applications():
    if current_user.role != "student":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    student = Student.query.filter_by(user_id=current_user.id).first()
    applications = student.applications.all()

    return render_template("my_applications.html", applications=applications)


@app.route("/admin/companies")
@login_required
def admin_companies():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    query = request.args.get("q")

    if query:
        companies = Company.query.filter(
            Company.name.ilike(f"%{query}%")
        ).all()
    else:
        companies = Company.query.all()

    return render_template("admin_companies.html", companies=companies)


@app.route("/admin/approve-company/<int:company_id>")
@login_required
def approve_company(company_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    company = Company.query.get_or_404(company_id)
    company.approval_status = "Approved"

    db.session.commit()

    flash("Company approved successfully.", "success")
    return redirect(url_for("admin_companies"))

@app.route("/admin/reject-company/<int:company_id>")
@login_required
def reject_company(company_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    company = Company.query.get_or_404(company_id)
    company.approval_status = "Rejected"

    db.session.commit()

    flash("Company rejected.", "danger")
    return redirect(url_for("admin_companies"))


@app.route("/admin/students")
@login_required
def admin_students():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    query = request.args.get("q")

    if query:
        students = Student.query.filter(
            (Student.name.ilike(f"%{query}%")) |
            (Student.student_id.ilike(f"%{query}%")) |
            (Student.phone.ilike(f"%{query}%"))
        ).all()
    else:
        students = Student.query.all()

    return render_template("admin_students.html", students=students)


@app.route("/admin/drives")
@login_required
def admin_drives():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    drives = PlacementDrive.query.all()
    return render_template("admin_drives.html", drives=drives)

@app.route("/admin/applications")
@login_required
def admin_applications():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    applications = Application.query.all()
    return render_template("admin_applications.html", applications=applications)


@app.route("/admin/blacklist-company/<int:company_id>")
@login_required
def blacklist_company(company_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    company = Company.query.get_or_404(company_id)
    company.approval_status = "Blacklisted"
    company.user.is_blacklisted = True

    db.session.commit()

    flash("Company blacklisted.", "danger")
    return redirect(url_for("admin_companies"))

@app.route("/admin/unblacklist-company/<int:company_id>")
@login_required
def unblacklist_company(company_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    company = Company.query.get_or_404(company_id)

    company.approval_status = "Approved"
    company.user.is_blacklisted = False

    db.session.commit()

    flash("Company restored successfully.", "success")
    return redirect(url_for("admin_companies"))

@app.route("/admin/blacklist-student/<int:student_id>")
@login_required
def blacklist_student(student_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = True
    student.user.is_blacklisted = True

    db.session.commit()

    flash("Student blacklisted.", "danger")
    return redirect(url_for("admin_students"))

@app.route("/admin/unblacklist-student/<int:student_id>")
@login_required
def unblacklist_student(student_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    student = Student.query.get_or_404(student_id)

    student.is_blacklisted = False
    student.user.is_blacklisted = False

    db.session.commit()

    flash("Student restored successfully.", "success")
    return redirect(url_for("admin_students"))

@app.route("/admin/search")
@login_required
def admin_search():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    query = request.args.get("q")

    students = []
    companies = []

    if query:
        students = Student.query.filter(
            (Student.name.ilike(f"%{query}%")) |
            (Student.student_id.ilike(f"%{query}%")) |
            (Student.phone.ilike(f"%{query}%"))
        ).all()

        companies = Company.query.filter(
            Company.name.ilike(f"%{query}%")
        ).all()

    return render_template(
        "admin_search.html",
        query=query,
        students=students,
        companies=companies
    )

@app.route("/admin/delete-student/<int:student_id>")
@login_required
def delete_student(student_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    student = Student.query.get_or_404(student_id)
    db.session.delete(student.user)
    db.session.commit()

    flash("Student deleted successfully.", "danger")
    return redirect(url_for("admin_students"))

@app.route("/admin/delete-company/<int:company_id>")
@login_required
def delete_company(company_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    company = Company.query.get_or_404(company_id)

    db.session.delete(company.user)
    db.session.commit()

    flash("Company deleted successfully.", "danger")
    return redirect(url_for("admin_companies"))

@app.route("/admin/edit-student/<int:student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    student = Student.query.get_or_404(student_id)

    if request.method == "POST":
        student.name = request.form.get("name")
        student.branch = request.form.get("branch")
        student.cgpa = float(request.form.get("cgpa") or 0)
        student.phone = request.form.get("phone")
        student.skills = request.form.get("skills")

        db.session.commit()

        flash("Student updated successfully.", "success")
        return redirect(url_for("admin_students"))

    return render_template("edit_student.html", student=student)


@app.route("/admin/edit-company/<int:company_id>", methods=["GET", "POST"])
@login_required
def edit_company(company_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    company = Company.query.get_or_404(company_id)

    if request.method == "POST":
        company.name = request.form.get("name")
        company.hr_contact = request.form.get("hr_contact")
        company.hr_email = request.form.get("hr_email")
        company.website = request.form.get("website")
        company.description = request.form.get("description")

        db.session.commit()

        flash("Company updated successfully.", "success")
        return redirect(url_for("admin_companies"))

    return render_template("edit_company.html", company=company)

@app.route("/company/drives")
@login_required
def company_drives():
    if current_user.role != "company":
        return redirect(url_for("home"))

    company = Company.query.filter_by(user_id=current_user.id).first()
    drives = company.drives.all()

    return render_template("company_drives.html", drives=drives)

@app.route("/company/all-applications")
@login_required
def company_all_applications():
    if current_user.role != "company":
        return redirect(url_for("home"))

    company = Company.query.filter_by(user_id=current_user.id).first()

    applications = Application.query.join(PlacementDrive).filter(
        PlacementDrive.company_id == company.id
    ).all()

    return render_template("company_all_applications.html", applications=applications)


@app.route("/company/edit-profile", methods=["GET", "POST"])
@login_required
def edit_company_profile():
    if current_user.role != "company":
        return redirect(url_for("home"))

    company = Company.query.filter_by(user_id=current_user.id).first()

    if request.method == "POST":
        company.name = request.form.get("name")
        company.hr_contact = request.form.get("hr_contact")
        company.hr_email = request.form.get("hr_email")
        company.website = request.form.get("website")
        company.description = request.form.get("description")

        db.session.commit()
        flash("Profile updated successfully", "success")
        return redirect(url_for("company_dashboard"))

    return render_template("edit_company.html", company=company)


@app.route("/company/edit-drive/<int:drive_id>", methods=["GET","POST"])
@login_required
def edit_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)

    if request.method == "POST":
        drive.job_title = request.form.get("job_title")
        drive.description = request.form.get("description")
        db.session.commit()
        return redirect(url_for("company_drives"))

    return render_template("create_drive.html", drive=drive)

@app.route("/company/close-drive/<int:drive_id>")
@login_required
def close_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "Closed"
    db.session.commit()

    return redirect(url_for("company_drives"))

@app.route("/company/delete-drive/<int:drive_id>")
@login_required
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)

    db.session.delete(drive)
    db.session.commit()

    return redirect(url_for("company_drives"))

@app.route("/student/edit-student", methods=["GET", "POST"])
@login_required
def edit_profile():
    if current_user.role != "student":
        return redirect(url_for("home"))

    student = Student.query.filter_by(user_id=current_user.id).first()
    student.resume_link = request.form.get("resume_link")

    if request.method == "POST":
        student.name = request.form.get("name")
        student.branch = request.form.get("branch")
        student.cgpa = float(request.form.get("cgpa") or 0)
        student.phone = request.form.get("phone")
        student.skills = request.form.get("skills")

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("student_dashboard"))

    return render_template("edit_student.html", student=student)

@app.route("/placement-history")
@login_required
def placement_history():
    student = Student.query.filter_by(user_id=current_user.id).first()
    applications = student.applications.filter(
        Application.status == "Selected"
    ).all()

    return render_template("placement_history.html", applications=applications)

@app.route("/admin/delete-application/<int:app_id>")
@login_required
def delete_application(app_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))

    app_obj = Application.query.get_or_404(app_id)
    db.session.delete(app_obj)
    db.session.commit()

    flash("Application deleted", "danger")
    return redirect(url_for("admin_applications"))

@app.route("/withdraw/<int:app_id>")
@login_required
def withdraw_application(app_id):
    if current_user.role != "student":
        return redirect(url_for("home"))

    app_obj = Application.query.get_or_404(app_id)

    db.session.delete(app_obj)
    db.session.commit()

    flash("Application withdrawn", "warning")
    return redirect(url_for("my_applications"))

with app.app_context():
    db.create_all()
    seed_admin()

if __name__ == "__main__":
    app.run(debug=True)