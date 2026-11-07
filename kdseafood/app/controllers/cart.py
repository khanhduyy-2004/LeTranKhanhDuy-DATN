"""Giỏ hàng: xem, thêm (hỗ trợ AJAX), cập nhật số lượng, xóa."""
from flask import Blueprint, current_app, flash, g, jsonify, redirect, render_template, request, url_for

from ..models import cart, product
from ..utils import format_qty, login_required, to_float, to_int

bp = Blueprint("cart", __name__, url_prefix="/gio-hang")


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _validate_qty(p, qty):
    if not p or not p["is_active"]:
        return "Sản phẩm không tồn tại hoặc đã ngừng kinh doanh."
    if qty <= 0:
        return "Số lượng phải lớn hơn 0."
    if p["unit"] != "kg" and qty != int(qty):
        return f"Sản phẩm bán theo {p['unit']}, vui lòng nhập số nguyên."
    if qty > float(p["stock_quantity"]):
        return f"Chỉ còn {format_qty(p['stock_quantity'])} {p['unit']} trong kho."
    return None


@bp.route("/")
@login_required
def view():
    rows = cart.items(g.user["id"])
    cfg = current_app.config
    return render_template("cart/cart.html", items=rows,
                           summary=cart.summary(rows, cfg["SHIPPING_FEE"], cfg["FREE_SHIP_FROM"]))


@bp.route("/them", methods=["POST"])
@login_required
def add():
    pid = to_int(request.form.get("product_id"))
    qty = to_float(request.form.get("quantity"), 1)
    p = product.get(pid) if pid else None
    new_qty = round(cart.get_qty(g.user["id"], pid) + qty, 2) if p else qty
    error = _validate_qty(p, new_qty)
    if error:
        if _is_ajax():
            return jsonify(ok=False, message=error), 400
        flash(error, "danger")
        return redirect(request.referrer or url_for("product.listing"))
    cart.set_qty(g.user["id"], pid, new_qty)
    msg = f"Đã thêm {format_qty(qty)} {p['unit']} “{p['name']}” vào giỏ hàng."
    if _is_ajax():
        return jsonify(ok=True, message=msg, count=cart.count(g.user["id"]))
    flash(msg, "success")
    if request.form.get("buy_now"):
        return redirect(url_for("cart.view"))
    return redirect(request.referrer or url_for("cart.view"))


@bp.route("/cap-nhat", methods=["POST"])
@login_required
def update():
    pid = to_int(request.form.get("product_id"))
    qty = to_float(request.form.get("quantity"), 0)
    p = product.get(pid) if pid else None
    if qty <= 0:
        cart.remove(g.user["id"], pid)
    else:
        error = _validate_qty(p, qty)
        if error:
            flash(error, "danger")
        else:
            cart.set_qty(g.user["id"], pid, qty)
    return redirect(url_for("cart.view"))


@bp.route("/xoa/<int:pid>", methods=["POST"])
@login_required
def remove(pid):
    cart.remove(g.user["id"], pid)
    flash("Đã xóa sản phẩm khỏi giỏ hàng.", "info")
    return redirect(url_for("cart.view"))


@bp.route("/xoa-het", methods=["POST"])
@login_required
def clear():
    cart.clear(g.user["id"])
    flash("Đã làm trống giỏ hàng.", "info")
    return redirect(url_for("cart.view"))
