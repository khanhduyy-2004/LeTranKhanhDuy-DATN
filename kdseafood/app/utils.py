"""Hàm tiện ích dùng chung: decorator phân quyền, slug tiếng Việt, định dạng, tải ảnh."""
import math
import os
import re
import unicodedata
import uuid
from functools import wraps

from flask import current_app, flash, g, redirect, request, url_for
from werkzeug.utils import secure_filename

# ---------------- Trạng thái đơn hàng ----------------
ORDER_STATUS = {
    "pending":   ("Chờ xác nhận", "warning"),
    "confirmed": ("Đã xác nhận", "info"),
    "preparing": ("Đang chuẩn bị", "primary"),
    "shipping":  ("Đang giao", "primary"),
    "delivered": ("Đã giao", "success"),
    "cancelled": ("Đã hủy", "secondary"),
}
ORDER_FLOW = ["pending", "confirmed", "preparing", "shipping", "delivered"]
PAYMENT_METHOD = {
    "cod": "Thanh toán khi nhận hàng (COD)",
    "bank_transfer": "Chuyển khoản ngân hàng",
    "vnpay_sandbox": "VNPay (môi trường thử nghiệm)",
}
PAYMENT_STATUS = {"unpaid": ("Chưa thanh toán", "warning"), "paid": ("Đã thanh toán", "success"),
                  "refunded": ("Đã hoàn tiền", "secondary")}
REVIEW_STATUS = {"pending": ("Chờ duyệt", "warning"), "approved": ("Đã duyệt", "success"),
                 "rejected": ("Từ chối", "danger")}


# ---------------- Phân quyền ----------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return {"ok": False, "login": url_for("auth.login", next=request.referrer or "/")}, 401
            flash("Vui lòng đăng nhập để tiếp tục.", "warning")
            return redirect(url_for("auth.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("admin") is None:
            flash("Bạn cần đăng nhập bằng tài khoản quản trị.", "warning")
            return redirect(url_for("auth.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped


# ---------------- Chuỗi / số ----------------
def slugify(text):
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or uuid.uuid4().hex[:8]


def format_vnd(value):
    try:
        return f"{int(round(float(value or 0))):,}".replace(",", ".") + "₫"
    except (TypeError, ValueError):
        return "0₫"


def format_qty(value):
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        return value
    return str(int(v)) if v == int(v) else f"{v:g}".replace(".", ",")


def to_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Pagination:
    def __init__(self, page, per_page, total):
        self.page, self.per_page, self.total = page, per_page, total
        self.pages = max(1, math.ceil(total / per_page)) if per_page else 1

    @property
    def offset(self):
        return (self.page - 1) * self.per_page

    def iter_pages(self, window=2):
        last = 0
        for n in range(1, self.pages + 1):
            if n <= 1 or n > self.pages - 1 or abs(n - self.page) <= window:
                if last + 1 != n:
                    yield None
                yield n
                last = n


def get_page():
    return max(1, to_int(request.args.get("page"), 1) or 1)


# ---------------- Ảnh ----------------
def save_image(file_storage, folder):
    """Lưu ảnh tải lên vào static/uploads/<folder>, trả về đường dẫn /static/... hoặc None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in current_app.config["ALLOWED_IMAGE_EXT"]:
        raise ValueError("Chỉ chấp nhận ảnh JPG, PNG, WEBP hoặc GIF.")
    name = f"{uuid.uuid4().hex[:12]}-{secure_filename(file_storage.filename.rsplit('.', 1)[0])[:40]}.{ext}"
    target_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], folder)
    os.makedirs(target_dir, exist_ok=True)
    file_storage.save(os.path.join(target_dir, name))
    return f"/static/uploads/{folder}/{name}"


def remove_image(url):
    if url and url.startswith("/static/uploads/"):
        path = os.path.join(current_app.root_path, url.lstrip("/"))
        if os.path.isfile(path):
            os.remove(path)


def image_url(url, kind="product"):
    """Trả về ảnh thật nếu tồn tại, ngược lại dùng ảnh minh họa mặc định."""
    if url:
        if url.startswith("http"):
            return url
        if os.path.isfile(os.path.join(current_app.root_path, url.lstrip("/"))):
            return url
    return url_for("static", filename=f"img/placeholder-{kind}.svg")
