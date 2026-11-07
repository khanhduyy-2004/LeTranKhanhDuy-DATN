"""Cấu hình ứng dụng KDSeaFood (đọc từ biến môi trường / file .env)."""
import os
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "kdseafood-dev-secret-change-me")

    # --- MySQL ---
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "kdseafood")
    DB_UNIX_SOCKET = os.getenv("DB_UNIX_SOCKET") or None

    # --- Phiên đăng nhập & bảo mật ---
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = None

    # --- Tải ảnh ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB / request
    ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png", "webp", "gif"}

    # --- Nghiệp vụ ---
    PER_PAGE = 12                 # sản phẩm / trang
    ADMIN_PER_PAGE = 15
    SHIPPING_FEE = 30000          # phí giao hàng (VNĐ)
    FREE_SHIP_FROM = 1000000      # miễn phí giao hàng từ 1.000.000đ
    LOW_STOCK_THRESHOLD = 10      # cảnh báo sắp hết hàng
