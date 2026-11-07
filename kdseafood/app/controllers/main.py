"""Trang chủ, trang thông tin, API gợi ý tìm kiếm."""
from flask import Blueprint, jsonify, render_template, request, url_for

from ..models import banner, category, product
from ..utils import format_vnd, image_url

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    return render_template("index.html",
                           banners=banner.active(),
                           categories=category.all_active(),
                           featured=product.featured(8),
                           newest=product.newest(8),
                           best=product.best_selling(4))


@bp.route("/gioi-thieu")
def about():
    return render_template("pages/about.html")


@bp.route("/lien-he")
def contact():
    return render_template("pages/contact.html")


@bp.route("/chinh-sach")
def policy():
    return render_template("pages/policy.html")


@bp.route("/api/search-suggest")
def search_suggest():
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify([])
    return jsonify([{
        "name": p["name"], "price": format_vnd(p["price"]) + "/" + p["unit"],
        "url": url_for("product.detail", slug=p["slug"]), "image": image_url(p["image"]),
    } for p in product.suggest(q)])
