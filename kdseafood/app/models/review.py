"""Bảng reviews – đánh giá sản phẩm (cần quản trị viên duyệt)."""
from ..db import execute, query, scalar


def approved_for(product_id):
    return query("""SELECT r.*, u.full_name, u.avatar_url FROM reviews r JOIN users u ON u.id=r.user_id
                    WHERE r.product_id=%s AND r.status='approved' ORDER BY r.created_at DESC""", (product_id,))


def distribution(product_id):
    rows = query("""SELECT rating, COUNT(*) AS n FROM reviews WHERE product_id=%s AND status='approved'
                    GROUP BY rating""", (product_id,))
    data = {i: 0 for i in range(5, 0, -1)}
    data.update({r["rating"]: r["n"] for r in rows})
    return data


def of_user(user_id, product_id):
    return query("SELECT * FROM reviews WHERE user_id=%s AND product_id=%s", (user_id, product_id), one=True)


def create(product_id, user_id, rating, title, content):
    execute("""INSERT INTO reviews (product_id, user_id, rating, title, content) VALUES (%s,%s,%s,%s,%s)""",
            (product_id, user_id, rating, title, content))


def admin_search(status, limit, offset):
    where, args = "1=1", []
    if status in ("pending", "approved", "rejected"):
        where, args = "r.status=%s", [status]
    total = scalar(f"SELECT COUNT(*) FROM reviews r WHERE {where}", args)
    rows = query(f"""SELECT r.*, u.full_name, p.name AS product_name, p.slug
                     FROM reviews r JOIN users u ON u.id=r.user_id JOIN products p ON p.id=r.product_id
                     WHERE {where} ORDER BY r.created_at DESC LIMIT %s OFFSET %s""", args + [limit, offset])
    return rows, total


def set_status(review_id, status):
    execute("UPDATE reviews SET status=%s WHERE id=%s", (status, review_id))


def delete(review_id):
    execute("DELETE FROM reviews WHERE id=%s", (review_id,))


def count_pending():
    return scalar("SELECT COUNT(*) FROM reviews WHERE status='pending'")
