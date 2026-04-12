from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    FloatField, IntegerField, TextAreaField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, NumberRange,
    Optional, ValidationError
)
import re


class LoginForm(FlaskForm):
    email    = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit   = SubmitField("Sign In")


class StudentRegisterForm(FlaskForm):
    name            = StringField("Full Name",      validators=[DataRequired(), Length(2, 150)])
    email           = StringField("Email",          validators=[DataRequired(), Email()])
    student_id      = StringField("Student ID",     validators=[DataRequired(), Length(3, 50)])
    phone           = StringField("Phone Number",   validators=[Optional(), Length(max=20)])
    branch          = StringField("Branch / Dept",  validators=[DataRequired(), Length(2, 100)])
    graduation_year = IntegerField("Graduation Year", validators=[DataRequired(), NumberRange(2024, 2035)])
    cgpa            = FloatField("CGPA",            validators=[DataRequired(), NumberRange(0.0, 10.0)])
    skills          = TextAreaField("Skills (comma separated)", validators=[Optional(), Length(max=500)])
    resume_link     = StringField("Resume Drive Link", validators=[DataRequired()])
    password        = PasswordField("Password",     validators=[DataRequired(), Length(8, 128)])
    confirm         = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", "Passwords must match")])
    submit          = SubmitField("Create Account")

    def validate_password(self, field):
        pwd = field.data
        if not re.search(r"[A-Z]", pwd):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", pwd):
            raise ValidationError("Password must contain at least one number.")


class CompanyRegisterForm(FlaskForm):
    company_name = StringField("Company Name",   validators=[DataRequired(), Length(2, 150)])
    email        = StringField("Login Email",    validators=[DataRequired(), Email()])
    hr_contact   = StringField("HR Contact Name", validators=[DataRequired(), Length(2, 100)])
    hr_email     = StringField("HR Email",       validators=[DataRequired(), Email()])
    website      = StringField("Website URL",    validators=[Optional(), Length(max=200)])
    description  = TextAreaField("About Company", validators=[Optional(), Length(max=1000)])
    password     = PasswordField("Password",     validators=[DataRequired(), Length(8, 128)])
    confirm      = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", "Passwords must match")])
    submit       = SubmitField("Register Company")

    def validate_password(self, field):
        pwd = field.data
        if not re.search(r"[A-Z]", pwd):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", pwd):
            raise ValidationError("Password must contain at least one number.")