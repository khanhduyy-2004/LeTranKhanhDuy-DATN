"""Quản lý đơn hàng: tìm kiếm, lọc, xem chi tiết, cập nhật trạng thái."""
from flask import abort, current_app, flash, g, redirect, render_template, request, url_for

from . import bp
from ...models import order
from ...utils import ORDER_STATUS, Pagination, get_page


@bp.route("/don-hang")
def orders():
    per = current_app.config["ADMIN_PER_PAGE"]
    page = get_page()
    a = request.args
    rows, total = order.admin_search(a.get("q", "").strip(), a.get("trang-thai"), a.get("tu-ngay"),
                                     a.get("den-ngay"), per, (page - 1) * per)
    return render_template("admin/orders/index.html", orders=rows, pagination=Pagination(page, per, total),
                           total=total, counts=order.count_by_status(), args=a)


@bp.route("/don-hang/<int:oid>")
def order_detail(oid):
    o = order.get(oid)
    if not o:
        abort(404)
    return render_template("admin/orders/detail.html", o=o, items=order.items(oid), history=order.history(oid),
                           next_status=order.allowed_next(o["status"]))


@bp.route("/don-hang/<int:oid>/trang-thai", methods=["POST"])
def order_status(oid):
    new_status = request.form.get("status")
    if new_status not in ORDER_STATUS:
        abort(400)
    note = request.form.get("note", "").strip()[:255] or None
    if new_status == "cancelled" and not note:
        flash("Vui lòng nhập lý do hủy đơn.", "danger")
        return redirect(url_for("admin.order_detail", oid=oid))
    try:
        order.change_status(oid, new_status, note=note, admin_id=g.admin["id"])
        flash(f"Đã chuyển đơn sang “{ORDER_STATUS[new_status][0]}”.", "success")
    except order.OrderError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.order_detail", oid=oid))
