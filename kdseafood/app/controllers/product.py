"""Danh sách (lọc / sắp xếp / phân trang), chi tiết sản phẩm, gửi đánh giá."""
from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for)

from ..models import category, order, product, review
from ..utils import Pagination, get_page, login_required, to_float, to_int

bp = Blueprint("product", __name__, url_prefix="/san-pham")


@bp.route("/")
def listing():
    args = request.args
    cat = category.get_by_slug(args.get("danh-muc")) if args.get("danh-muc") else None
    keyword = (args.get("q") or "").strip()
    min_price = to_float(args.get("min"), None) if args.get("min") else None
    max_price = to_float(args.get("max"), None) if args.get("max") else None
    rating = to_int(args.get("sao"), 0) or 0
    in_stock = args.get("con-hang") == "1"
    sort = args.get("sap-xep", "newest")
    if sort not in product.SORTS:
        sort = "newest"
    per_page = current_app.config["PER_PAGE"]
    page = get_page()
    items, total = product.search(cat["id"] if cat else None, keyword, min_price, max_price, rating,
                                  in_stock, sort, per_page, (page - 1) * per_page)
    lo, hi = product.price_bounds()
    return render_template("product/list.html", products=items, total=total,
                           pagination=Pagination(page, per_page, total), current_cat=cat, keyword=keyword,
                           min_price=min_price, max_price=max_price, rating=rating, in_stock=in_stock,
                           sort=sort, sorts=product.SORTS, categories=category.all_active(),
                           price_lo=lo, price_hi=hi)


@bp.route("/<slug>")
def detail(slug):
    p = product.get_by_slug(slug)
    if not p:
        abort(404)
    can_review = my_review = None
    if g.user:
        my_review = review.of_user(g.user["id"], p["id"])
        can_review = not my_review and order.has_delivered_product(g.user["id"], p["id"])
    return render_template("product/detail.html", p=p, images=product.images(p["id"]),
                           related=product.related(p), reviews=review.approved_for(p["id"]),
                           dist=review.distribution(p["id"]), can_review=can_review, my_review=my_review)


@bp.route("/<slug>/danh-gia", methods=["POST"])
@login_required
def add_review(slug):
    p = product.get_by_slug(slug)
    if not p:
        abort(404)
    rating = to_int(request.form.get("rating"), 0)
    if review.of_user(g.user["id"], p["id"]):
        flash("Bạn đã đánh giá sản phẩm này.", "info")
    elif not order.has_delivered_product(g.user["id"], p["id"]):
        flash("Chỉ khách hàng đã mua và nhận sản phẩm mới có thể đánh giá.", "warning")
    elif not 1 <= rating <= 5:
        flash("Vui lòng chọn số sao từ 1 đến 5.", "danger")
    else:
        review.create(p["id"], g.user["id"], rating, request.form.get("title", "").strip()[:150] or None,
                      request.form.get("content", "").strip() or None)
        flash("Cảm ơn bạn! Đánh giá sẽ hiển thị sau khi được cửa hàng duyệt.", "success")
    return redirect(url_for("product.detail", slug=slug) + "#danh-gia")
