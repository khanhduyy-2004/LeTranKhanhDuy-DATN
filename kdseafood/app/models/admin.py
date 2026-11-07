"""Bảng admins – quản trị viên."""
from werkzeug.security import generate_password_hash

from ..db import execute, query


def get(admin_id):
    return query("SELECT * FROM admins WHERE id=%s", (admin_id,), one=True)


def get_by_login(login):
    return query("SELECT * FROM admins WHERE username=%s OR email=%s", (login, login), one=True)


def touch_login(admin_id):
    execute("UPDATE admins SET last_login_at=NOW() WHERE id=%s", (admin_id,))


def set_password(admin_id, password):
    execute("UPDATE admins SET password_hash=%s WHERE id=%s", (generate_password_hash(password), admin_id))
