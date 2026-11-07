"""Trang tổng quan & thống kê doanh thu."""
from flask import current_app, flash, g, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash

from . import bp
from ...models import admin as admin_model, order, product, stats, user


@bp.route("/")
def dashboard():
    return render_template("admin/dashboard.html",
                           s=stats.summary(),
                           counts=order.count_by_status(),
                           monthly=stats.monthly_revenue(12),
                           best=stats.best_sellers(5),
                           low=stats.low_stock(current_app.config["LOW_STOCK_THRESHOLD"]),
                           recent=stats.recent_orders(8),
                           by_cat=stats.revenue_by_category(),
                           total_products=product.count_all(),
                           total_customers=user.count_all())


@bp.route("/doi-mat-khau", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        if not check_password_hash(g.admin["password_hash"], request.form.get("old_password", "")):
            flash("Mật khẩu hiện tại không đúng.", "danger")
        elif len(request.form.get("new_password", "")) < 6:
            flash("Mật khẩu mới tối thiểu 6 ký tự.", "danger")
        elif request.form.get("new_password") != request.form.get("confirm_password"):
            flash("Xác nhận mật khẩu không khớp.", "danger")
        else:
            admin_model.set_password(g.admin["id"], request.form["new_password"])
            flash("Đổi mật khẩu thành công.", "success")
            return redirect(url_for("admin.dashboard"))
    return render_template("admin/change_password.html")
