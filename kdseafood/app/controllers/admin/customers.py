"""Quản lý tài khoản khách hàng: xem, tìm kiếm, khóa/mở khóa, đặt lại mật khẩu."""
import secrets

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from . import bp
from ...models import address, order, user
from ...utils import Pagination, get_page


@bp.route("/khach-hang")
def customers():
    per = current_app.config["ADMIN_PER_PAGE"]
    page = get_page()
    q, status = request.args.get("q", "").strip(), request.args.get("trang-thai")
    rows, total = user.admin_search(q, status, per, (page - 1) * per)
    return render_template("admin/customers/index.html", customers=rows, pagination=Pagination(page, per, total),
                           total=total, q=q, status=status)


@bp.route("/khach-hang/<int:uid>")
def customer_detail(uid):
    u = user.get(uid)
    if not u:
        abort(404)
    return render_template("admin/customers/detail.html", u=u, orders=order.list_by_user(uid),
                           addresses=address.list_for(uid), counts=order.count_by_status(uid))


@bp.route("/khach-hang/<int:uid>/khoa", methods=["POST"])
def customer_toggle(uid):
    u = user.get(uid)
    if not u:
        abort(404)
    user.toggle_active(uid)
    flash(f"Đã {'khóa' if u['is_active'] else 'mở khóa'} tài khoản {u['username']}.", "success")
    return redirect(request.referrer or url_for("admin.customers"))


@bp.route("/khach-hang/<int:uid>/dat-lai-mat-khau", methods=["POST"])
def customer_reset_password(uid):
    u = user.get(uid)
    if not u:
        abort(404)
    new_pw = secrets.token_urlsafe(6)[:8]
    user.set_password(uid, new_pw)
    flash(f"Mật khẩu mới của {u['username']} là: {new_pw} – hãy gửi cho khách và đề nghị đổi lại.", "success")
    return redirect(url_for("admin.customer_detail", uid=uid))
