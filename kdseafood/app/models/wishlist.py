"""Bảng wishlists – sản phẩm yêu thích."""
from ..db import execute, query, scalar
from .product import CARD_COLUMNS, CARD_FROM


def ids(user_id):
    return {r["product_id"] for r in query("SELECT product_id FROM wishlists WHERE user_id=%s", (user_id,))}


def toggle(user_id, product_id):
    """Trả về True nếu sau thao tác sản phẩm đang được yêu thích."""
    if scalar("SELECT COUNT(*) FROM wishlists WHERE user_id=%s AND product_id=%s", (user_id, product_id)):
        execute("DELETE FROM wishlists WHERE user_id=%s AND product_id=%s", (user_id, product_id))
        return False
    execute("INSERT INTO wishlists (user_id, product_id) VALUES (%s,%s)", (user_id, product_id))
    return True


def products(user_id):
    return query(f"""SELECT {CARD_COLUMNS} {CARD_FROM} JOIN wishlists w ON w.product_id=p.id
                     WHERE w.user_id=%s AND p.is_active=1 ORDER BY w.created_at DESC""", (user_id,))
