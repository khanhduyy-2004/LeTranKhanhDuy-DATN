"""Tài khoản khách hàng: hồ sơ, đổi mật khẩu, sổ địa chỉ, sản phẩm yêu thích."""
import re

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash

from ..models import address as address_model, user as user_model, wishlist
from ..models import product as product_model
from ..utils import login_required, remove_image, save_image

bp = Blueprint("account", __name__, url_prefix="/tai-khoan")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^0\d{9}$")


@bp.route("/", methods=["GET", "POST"])
@login_required
def profile():
    u = g.user
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        if not full_name or not EMAIL_RE.match(email) or (phone and not PHONE_RE.match(phone)):
            flash("Thông tin không hợp lệ: kiểm tra họ tên, email và số điện thoại (10 số).", "danger")
        elif user_model.exists(email=email, exclude_id=u["id"]):
            flash("Email đã được tài khoản khác sử dụng.", "danger")
        else:
            try:
                avatar = save_image(request.files.get("avatar"), "avatars")
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("account.profile"))
            if avatar:
                remove_image(u["avatar_url"])
            user_model.update_profile(u["id"], full_name, email, phone or None, avatar)
            flash("Đã cập nhật thông tin cá nhân.", "success")
        return redirect(url_for("account.profile"))
    return render_template("account/profile.html")


@bp.route("/doi-mat-khau", methods=["POST"])
@login_required
def change_password():
    old, new = request.form.get("old_password", ""), request.form.get("new_password", "")
    if not check_password_hash(g.user["password_hash"], old):
        flash("Mật khẩu hiện tại không đúng.", "danger")
    elif len(new) < 6:
        flash("Mật khẩu mới tối thiểu 6 ký tự.", "danger")
    elif new != request.form.get("confirm_password"):
        flash("Xác nhận mật khẩu không khớp.", "danger")
    else:
        user_model.set_password(g.user["id"], new)
        flash("Đổi mật khẩu thành công.", "success")
    return redirect(url_for("account.profile") + "#mat-khau")


# ---------------- Sổ địa chỉ ----------------
def _address_form():
    data = {f: request.form.get(f, "").strip() for f in address_model.FIELDS}
    if not (data["receiver_name"] and data["address_line"] and data["province"]):
        return None, "Vui lòng nhập họ tên, địa chỉ và tỉnh/thành phố."
    if not PHONE_RE.match(data["phone"]):
        return None, "Số điện thoại gồm 10 chữ số, bắt đầu bằng 0."
    return data, None


@bp.route("/dia-chi")
@login_required
def addresses():
    return render_template("account/addresses.html", addresses=address_model.list_for(g.user["id"]))


@bp.route("/dia-chi/them", methods=["POST"])
@login_required
def address_add():
    data, err = _address_form()
    if err:
        flash(err, "danger")
    else:
        address_model.create(g.user["id"], data, bool(request.form.get("is_default")))
        flash("Đã thêm địa chỉ mới.", "success")
    return redirect(request.form.get("back") or url_for("account.addresses"))


@bp.route("/dia-chi/<int:aid>/sua", methods=["POST"])
@login_required
def address_edit(aid):
    data, err = _address_form()
    if err:
        flash(err, "danger")
    elif address_model.get(aid, g.user["id"]):
        address_model.update(aid, g.user["id"], data)
        if request.form.get("is_default"):
            address_model.set_default(aid, g.user["id"])
        flash("Đã cập nhật địa chỉ.", "success")
    return redirect(url_for("account.addresses"))


@bp.route("/dia-chi/<int:aid>/mac-dinh", methods=["POST"])
@login_required
def address_default(aid):
    address_model.set_default(aid, g.user["id"])
    return redirect(url_for("account.addresses"))


@bp.route("/dia-chi/<int:aid>/xoa", methods=["POST"])
@login_required
def address_delete(aid):
    address_model.delete(aid, g.user["id"])
    flash("Đã xóa địa chỉ.", "info")
    return redirect(url_for("account.addresses"))


# ---------------- Yêu thích ----------------
@bp.route("/yeu-thich")
@login_required
def wishlist_view():
    return render_template("account/wishlist.html", products=wishlist.products(g.user["id"]))


@bp.route("/yeu-thich/<int:pid>", methods=["POST"])
@login_required
def wishlist_toggle(pid):
    if not product_model.get(pid):
        return jsonify(ok=False), 404
    liked = wishlist.toggle(g.user["id"], pid)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(ok=True, liked=liked)
    flash("Đã thêm vào yêu thích." if liked else "Đã bỏ khỏi yêu thích.", "info")
    return redirect(request.referrer or url_for("account.wishlist_view"))
