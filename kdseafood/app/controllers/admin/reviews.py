"""Duyệt đánh giá sản phẩm."""
from flask import current_app, flash, redirect, render_template, request, url_for

from . import bp
from ...models import review
from ...utils import Pagination, get_page


@bp.route("/danh-gia")
def reviews():
    per = current_app.config["ADMIN_PER_PAGE"]
    page = get_page()
    status = request.args.get("trang-thai", "pending")
    rows, total = review.admin_search(status, per, (page - 1) * per)
    return render_template("admin/reviews/index.html", reviews=rows, pagination=Pagination(page, per, total),
                           total=total, status=status)


@bp.route("/danh-gia/<int:rid>/<action>", methods=["POST"])
def review_action(rid, action):
    if action == "duyet":
        review.set_status(rid, "approved"); flash("Đã duyệt đánh giá.", "success")
    elif action == "tu-choi":
        review.set_status(rid, "rejected"); flash("Đã từ chối đánh giá.", "info")
    elif action == "xoa":
        review.delete(rid); flash("Đã xóa đánh giá.", "info")
    return redirect(request.referrer or url_for("admin.reviews"))
