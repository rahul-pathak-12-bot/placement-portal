from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id             = db.Column(db.Integer, primary_key=True)
    email          = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash  = db.Column(db.String(256), nullable=False)
    role           = db.Column(db.String(20),  nullable=False) 
    _is_active     = db.Column("is_active", db.Boolean, default=True, nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company_profile = db.relationship("Company",      backref="user", uselist=False, cascade="all, delete-orphan")
    student_profile = db.relationship("Student",      backref="user", uselist=False, cascade="all, delete-orphan")
    notifications   = db.relationship("Notification", backref="user", lazy="dynamic",  cascade="all, delete-orphan")

    @property
    def is_active(self):
        return self._is_active and not self.is_blacklisted

    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"


class Company(db.Model):
    __tablename__ = "company"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    name             = db.Column(db.String(150), nullable=False, index=True)
    hr_contact       = db.Column(db.String(100))
    hr_email         = db.Column(db.String(150))
    website          = db.Column(db.String(200))
    description      = db.Column(db.Text)
    logo_path        = db.Column(db.String(255))
    approval_status  = db.Column(db.String(20), default="Pending", nullable=False)

    rejection_reason = db.Column(db.Text)
    approved_at      = db.Column(db.DateTime)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    drives = db.relationship("PlacementDrive", backref="company", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def is_approved(self):
        return self.approval_status == "Approved"

    @property
    def total_applicants(self):
        return sum(d.applications.count() for d in self.drives)

    def __repr__(self):
        return f"<Company {self.name} [{self.approval_status}]>"


class Student(db.Model):
    __tablename__ = "student"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    name             = db.Column(db.String(150), nullable=False)
    student_id       = db.Column(db.String(50),  unique=True, nullable=False, index=True)
    branch           = db.Column(db.String(100))
    graduation_year  = db.Column(db.Integer)
    cgpa             = db.Column(db.Float)
    skills           = db.Column(db.Text)
    phone            = db.Column(db.String(20))
    resume_link      = db.Column(db.String(500))
    is_blacklisted   = db.Column(db.Boolean, default=False)
    blacklist_reason = db.Column(db.Text)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = db.relationship("Application", backref="student", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def placed(self):
        return self.applications.filter_by(status="Selected").count() > 0

    @property
    def applied_drive_ids(self):
        return {a.drive_id for a in self.applications}

    def __repr__(self):
        return f"<Student {self.name} [{self.student_id}]>"


class PlacementDrive(db.Model):
    __tablename__ = "placement_drive"

    id                       = db.Column(db.Integer, primary_key=True)
    company_id               = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    job_title                = db.Column(db.String(150), nullable=False)
    job_type                 = db.Column(db.String(50))   
    description              = db.Column(db.Text, nullable=False)
    eligibility              = db.Column(db.String(255))
    min_cgpa                 = db.Column(db.Float, default=0.0)
    graduation_year_required = db.Column(db.Integer)
    location                 = db.Column(db.String(150))
    salary_range             = db.Column(db.String(100))
    deadline                 = db.Column(db.Date, nullable=False)
    status                   = db.Column(db.String(20), default="Pending", nullable=False, index=True)
    rejection_reason         = db.Column(db.Text)
    created_at               = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at               = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = db.relationship("Application", backref="drive", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def is_open(self):
        return self.status == "Approved" and self.deadline >= date.today()

    @property
    def applicant_count(self):
        return self.applications.count()

    def __repr__(self):
        return f"<Drive '{self.job_title}' [{self.status}]>"


class Application(db.Model):
    __tablename__ = "application"

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    drive_id   = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False, index=True)
    status     = db.Column(db.String(20), default="Applied", nullable=False, index=True)

    notes      = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )

    def __repr__(self):
        return f"<Application student={self.student_id} drive={self.drive_id} [{self.status}]>"


class Notification(db.Model):
    __tablename__ = "notification"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title      = db.Column(db.String(150), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Notification user={self.user_id} read={self.is_read}>"