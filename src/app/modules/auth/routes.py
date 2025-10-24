from __future__ import annotations

from urllib.parse import urlparse

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length

from ..users.models import User, Group
from sqlalchemy import select


auth_bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    display_name = StringField("Display Name", validators=[DataRequired(), Length(min=2, max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])


def _is_safe_url(target: str) -> bool:
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urlparse(target).geturl())
    return (test_url.scheme in ("http", "https")) and (ref_url.netloc == test_url.netloc)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        sess = current_app.session
        user = sess.scalar(select(User).where(User.email == form.email.data))
        if user and user.check_password(form.password.data):
            login_user(user)
            next_url = request.args.get("next")
            if next_url and _is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for("index"))
        flash("Invalid credentials", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        sess = current_app.session
        existing = sess.scalar(select(User).where(User.email == form.email.data))
        if existing:
            flash("User already exists", "warning")
            return render_template("auth/register.html", form=form)
        user = User(email=form.email.data, display_name=form.display_name.data, password_hash="")
        user.set_password(form.password.data)
        # attach default groups
        groups = {g.name: g for g in sess.scalars(select(Group)).all()}
        for name in ("user",):
            if name not in groups:
                g = Group(name=name, description=name)
                sess.add(g)
                sess.flush()
                groups[name] = g
            user.groups.append(groups[name])
        sess.add(user)
        sess.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)
