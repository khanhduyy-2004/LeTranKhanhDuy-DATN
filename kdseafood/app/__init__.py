"""Khởi tạo ứng dụng Flask KDSeaFood (Application Factory + Blueprint, mô hình MVC)."""
from datetime import datetime

from flask import Flask, g, render_template, session
from flask_wtf.csrf import CSRFError, CSRFProtect

from config import Config

from . import db
from .utils import (ORDER_FLOW, ORDER_STATUS, PAYMENT_METHOD, PAYMENT_STATUS, REVIEW_STATUS,
                    format_qty, format_vnd, image_url)

csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    csrf.init_app(app)

    # ---- Controllers (Blueprint) ----
    from .controllers.main import bp as main_bp
    from .controllers.auth import bp as auth_bp
    from .controllers.product import bp as product_bp
    from .controllers.cart import bp as cart_bp
    from .controllers.order import bp as order_bp
    from .controllers.account import bp as account_bp
    from .controllers.admin import bp as admin_bp
    for bp in (main_bp, auth_bp, product_bp, cart_bp, order_bp, account_bp, admin_bp):
        app.register_blueprint(bp)

    # ---- Nạp người dùng đang đăng nhập ----
    from .models import admin as admin_model, user as user_model

    @app.before_request
    def load_logged_in():
        g.user = g.admin = None
        if session.get("user_id"):
            u = user_model.get(session["user_id"])
            if u and u["is_active"]:
                g.user = u
            else:
                session.clear()
        elif session.get("admin_id"):
            a = admin_model.get(session["admin_id"])
            if a and a["is_active"]:
                g.admin = a
            else:
                session.clear()

    # ---- Dữ liệu dùng chung cho mọi template ----
    from .models import cart as cart_model, category as category_model, wishlist as wishlist_model

    @app.context_processor
    def inject_globals():
        data = dict(ORDER_STATUS=ORDER_STATUS, ORDER_FLOW=ORDER_FLOW, PAYMENT_METHOD=PAYMENT_METHOD,
                    PAYMENT_STATUS=PAYMENT_STATUS, REVIEW_STATUS=REVIEW_STATUS,
                    current_year=datetime.now().year, cart_count=0, wish_ids=set(), nav_categories=[])
        try:
            data["nav_categories"] = category_model.all_active()
            if g.get("user"):
                data["cart_count"] = cart_model.count(g.user["id"])
                data["wish_ids"] = wishlist_model.ids(g.user["id"])
        except Exception:  # CSDL chưa sẵn sàng → vẫn hiển thị trang lỗi
            pass
        return data

    app.jinja_env.filters["vnd"] = format_vnd
    app.jinja_env.filters["qty"] = format_qty
    app.jinja_env.filters["img"] = image_url
    app.jinja_env.filters["dt"] = lambda v, f="%d/%m/%Y %H:%M": v.strftime(f) if v else ""

    # ---- Trang lỗi ----
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(CSRFError)
    def csrf_error(_e):
        return render_template("errors/400.html", message="Phiên làm việc đã hết hạn, vui lòng thử lại."), 400

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("errors/400.html", message="Ảnh tải lên vượt quá 5MB."), 413

    return app
