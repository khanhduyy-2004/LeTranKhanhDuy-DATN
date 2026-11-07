"""Đăng ký, đăng nhập (phân quyền khách hàng / quản trị viên), đăng xuất."""
import re

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from ..models import admin as admin_model, user as user_model

bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^0\d{9}$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{4,30}$")


def _safe_next(target):
    return target if target and target.startswith("/") and not target.startswith("//") else None


@bp.route("/dang-ky", methods=["GET", "POST"])
def register():
    if g.user or g.admin:
        return redirect(url_for("main.home"))
    form = request.form
    if request.method == "POST":
        username = form.get("username", "").strip()
        email = form.get("email", "").strip().lower()
        full_name = form.get("full_name", "").strip()
        phone = form.get("phone", "").strip()
        password = form.get("password", "")
        errors = []
        if not full_name:
            errors.append("Vui lòng nhập họ tên.")
        if not USERNAME_RE.match(username):
            errors.append("Tên đăng nhập 4–30 ký tự, chỉ gồm chữ không dấu, số, dấu chấm, gạch dưới.")
        if not EMAIL_RE.match(email):
            errors.append("Email không hợp lệ.")
        if phone and not PHONE_RE.match(phone):
            errors.append("Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.")
        if len(password) < 6:
            errors.append("Mật khẩu tối thiểu 6 ký tự.")
        if password != form.get("confirm_password"):
            errors.append("Xác nhận mật khẩu không khớp.")
        if not errors and (user_model.exists(username, email) or admin_model.get_by_login(username)):
            errors.append("Tên đăng nhập hoặc email đã được sử dụng.")
        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            user_id = user_model.create(username, email, password, full_name, phone or None)
            session.clear()
            session["user_id"] = user_id
            session.permanent = True
            flash(f"Chào mừng {full_name} đến với KDSeaFood!", "success")
            return redirect(url_for("main.home"))
    return render_template("auth/register.html", form=form)


@bp.route("/dang-nhap", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("main.home"))
    if g.admin:
        return redirect(url_for("admin.dashboard"))
    next_url = _safe_next(request.args.get("next") or request.form.get("next"))
    if request.method == "POST":
        login_name = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        session.clear()
        # 1) quản trị viên
        adm = admin_model.get_by_login(login_name)
        if adm and check_password_hash(adm["password_hash"], password):
            if not adm["is_active"]:
                flash("Tài khoản quản trị đã bị vô hiệu hóa.", "danger")
            else:
                session["admin_id"] = adm["id"]
                session.permanent = True
                admin_model.touch_login(adm["id"])
                flash(f"Xin chào {adm['full_name']}!", "success")
                return redirect(next_url if next_url and next_url.startswith("/admin") else url_for("admin.dashboard"))
        else:
            # 2) khách hàng
            usr = user_model.get_by_login(login_name.lower()) or user_model.get_by_login(login_name)
            if usr and check_password_hash(usr["password_hash"], password):
                if not usr["is_active"]:
                    flash("Tài khoản của bạn đã bị khóa. Vui lòng liên hệ cửa hàng.", "danger")
                else:
                    session["user_id"] = usr["id"]
                    session.permanent = True
                    user_model.touch_login(usr["id"])
                    flash(f"Xin chào {usr['full_name']}!", "success")
                    if next_url and next_url.startswith("/admin"):
                        next_url = None
                    return redirect(next_url or url_for("main.home"))
            else:
                flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")
    return render_template("auth/login.html", next=next_url or "")


@bp.route("/dang-xuat", methods=["POST"])
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("main.home"))
