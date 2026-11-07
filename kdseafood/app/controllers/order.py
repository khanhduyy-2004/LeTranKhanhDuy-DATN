"""Thanh toán, đặt hàng, thanh toán sandbox, theo dõi & hủy đơn hàng của khách."""
import re
import uuid

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from ..models import address as address_model, cart, order
from ..utils import PAYMENT_METHOD, login_required, to_int

bp = Blueprint("order", __name__)
PHONE_RE = re.compile(r"^0\d{9}$")


@bp.route("/thanh-toan", methods=["GET", "POST"])
@login_required
def checkout():
    uid = g.user["id"]
    rows = cart.items(uid)
    if not rows:
        flash("Giỏ hàng đang trống.", "warning")
        return redirect(url_for("product.listing"))
    cfg = current_app.config
    summary = cart.summary(rows, cfg["SHIPPING_FEE"], cfg["FREE_SHIP_FROM"])
    addresses = address_model.list_for(uid)
    form = request.form

    if request.method == "POST":
        method = form.get("payment_method")
        addr_id = to_int(form.get("address_id"))
        errors = []
        if method not in PAYMENT_METHOD:
            errors.append("Vui lòng chọn phương thức thanh toán.")
        if addr_id:
            addr = address_model.get(addr_id, uid)
            if not addr:
                errors.append("Địa chỉ không hợp lệ.")
        else:  # nhập địa chỉ mới
            addr = {f: form.get(f, "").strip() for f in address_model.FIELDS}
            if not (addr["receiver_name"] and addr["address_line"] and addr["province"]):
                errors.append("Vui lòng nhập đầy đủ họ tên, địa chỉ, tỉnh/thành phố người nhận.")
            if not PHONE_RE.match(addr["phone"]):
                errors.append("Số điện thoại người nhận gồm 10 chữ số, bắt đầu bằng 0.")
        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            try:
                code = order.place(uid, addr, method, form.get("note", "").strip()[:500],
                                   cfg["SHIPPING_FEE"], cfg["FREE_SHIP_FROM"])
            except order.OrderError as e:
                flash(str(e), "danger")
                return redirect(url_for("cart.view"))
            if not addr_id and form.get("save_address"):
                address_model.create(uid, addr)
            if method == "vnpay_sandbox":
                return redirect(url_for("order.sandbox_pay", code=code))
            return redirect(url_for("order.success", code=code))
    return render_template("order/checkout.html", items=rows, summary=summary, addresses=addresses, form=form)


@bp.route("/thanh-toan/sandbox/<code>", methods=["GET", "POST"])
@login_required
def sandbox_pay(code):
    """Cổng thanh toán mô phỏng (sandbox) – không phát sinh giao dịch thật."""
    o = order.get_by_code(code, g.user["id"])
    if not o or o["payment_method"] != "vnpay_sandbox":
        abort(404)
    if request.method == "POST":
        if request.form.get("result") == "success":
            order.mark_paid_sandbox(o["id"], f"VNP{uuid.uuid4().hex[:12].upper()}")
            flash("Thanh toán thành công (môi trường thử nghiệm).", "success")
        else:
            flash("Bạn đã hủy thanh toán. Đơn hàng vẫn được giữ, bạn có thể thanh toán khi nhận hàng.", "warning")
        return redirect(url_for("order.success", code=code))
    return render_template("order/sandbox.html", o=o)


@bp.route("/dat-hang-thanh-cong/<code>")
@login_required
def success(code):
    o = order.get_by_code(code, g.user["id"])
    if not o:
        abort(404)
    return render_template("order/success.html", o=o, items=order.items(o["id"]))


@bp.route("/don-hang")
@login_required
def my_orders():
    status = request.args.get("trang-thai")
    return render_template("order/history.html", orders=order.list_by_user(g.user["id"], status),
                           counts=order.count_by_status(g.user["id"]), status=status)


@bp.route("/don-hang/<code>")
@login_required
def tracking(code):
    o = order.get_by_code(code, g.user["id"])
    if not o:
        abort(404)
    return render_template("order/tracking.html", o=o, items=order.items(o["id"]), history=order.history(o["id"]))


@bp.route("/don-hang/<code>/huy", methods=["POST"])
@login_required
def cancel(code):
    o = order.get_by_code(code, g.user["id"])
    if not o:
        abort(404)
    reason = request.form.get("reason", "").strip()[:255] or "Khách hàng hủy đơn"
    try:
        order.change_status(o["id"], "cancelled", note=reason, user_id=g.user["id"])
        flash(f"Đã hủy đơn hàng {code}.", "success")
    except order.OrderError as e:
        flash(str(e), "danger")
    return redirect(url_for("order.tracking", code=code))
