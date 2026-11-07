"""Blueprint quản trị (/admin) – mọi route đều yêu cầu đăng nhập quản trị viên."""
from flask import Blueprint, g, redirect, request, url_for, flash

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
def require_admin():
    if g.get("admin") is None:
        flash("Bạn cần đăng nhập bằng tài khoản quản trị.", "warning")
        return redirect(url_for("auth.login", next=request.full_path))


@bp.context_processor
def admin_globals():
    from ...models import review
    try:
        return {"pending_reviews": review.count_pending()}
    except Exception:
        return {"pending_reviews": 0}


from . import dashboard, categories, products, orders, customers, reviews  # noqa: E402,F401
