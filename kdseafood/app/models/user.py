"""Bảng users – khách hàng."""
from werkzeug.security import generate_password_hash

from ..db import execute, query, scalar


def get(user_id):
    return query("SELECT * FROM users WHERE id=%s", (user_id,), one=True)


def get_by_login(login):
    return query("SELECT * FROM users WHERE username=%s OR email=%s", (login, login), one=True)


def exists(username=None, email=None, exclude_id=0):
    return scalar("SELECT COUNT(*) FROM users WHERE (username=%s OR email=%s) AND id<>%s",
                  (username or "", email or "", exclude_id)) > 0


def create(username, email, password, full_name, phone):
    return execute("""INSERT INTO users (username, email, password_hash, full_name, phone)
                      VALUES (%s,%s,%s,%s,%s)""",
                   (username, email, generate_password_hash(password), full_name, phone))


def update_profile(user_id, full_name, email, phone, avatar_url=None):
    if avatar_url:
        execute("UPDATE users SET full_name=%s, email=%s, phone=%s, avatar_url=%s WHERE id=%s",
                (full_name, email, phone, avatar_url, user_id))
    else:
        execute("UPDATE users SET full_name=%s, email=%s, phone=%s WHERE id=%s",
                (full_name, email, phone, user_id))


def set_password(user_id, password):
    execute("UPDATE users SET password_hash=%s WHERE id=%s", (generate_password_hash(password), user_id))


def touch_login(user_id):
    execute("UPDATE users SET last_login_at=NOW() WHERE id=%s", (user_id,))


# ---------------- Quản trị ----------------
def admin_search(keyword, status, limit, offset):
    where, args = ["1=1"], []
    if keyword:
        where.append("(u.full_name LIKE %s OR u.email LIKE %s OR u.phone LIKE %s OR u.username LIKE %s)")
        args += [f"%{keyword}%"] * 4
    if status in ("0", "1"):
        where.append("u.is_active=%s")
        args.append(int(status))
    w = " AND ".join(where)
    total = scalar(f"SELECT COUNT(*) FROM users u WHERE {w}", args)
    rows = query(f"""
        SELECT u.*,
               (SELECT COUNT(*) FROM orders o WHERE o.user_id=u.id) AS order_count,
               (SELECT COALESCE(SUM(total_amount),0) FROM orders o
                 WHERE o.user_id=u.id AND o.status='delivered') AS total_spent
        FROM users u WHERE {w} ORDER BY u.created_at DESC LIMIT %s OFFSET %s""", args + [limit, offset])
    return rows, total


def toggle_active(user_id):
    execute("UPDATE users SET is_active = 1 - is_active WHERE id=%s", (user_id,))


def count_all():
    return scalar("SELECT COUNT(*) FROM users")
