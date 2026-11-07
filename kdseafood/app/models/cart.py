"""Bảng cart_items – giỏ hàng (lưu theo tài khoản, không mất khi đăng xuất)."""
from ..db import execute, query, scalar


def items(user_id):
    return query("""
        SELECT ci.product_id, ci.quantity, p.name, p.slug, p.price, p.unit, p.stock_quantity, p.is_active,
               ROUND(p.price * ci.quantity) AS line_total,
               (SELECT image_url FROM product_images i WHERE i.product_id=p.id
                 ORDER BY i.is_primary DESC, i.sort_order LIMIT 1) AS image
        FROM cart_items ci JOIN products p ON p.id=ci.product_id
        WHERE ci.user_id=%s ORDER BY ci.added_at""", (user_id,))


def count(user_id):
    return int(scalar("SELECT COUNT(*) FROM cart_items WHERE user_id=%s", (user_id,)))


def get_qty(user_id, product_id):
    return float(scalar("SELECT quantity FROM cart_items WHERE user_id=%s AND product_id=%s",
                        (user_id, product_id), 0))


def set_qty(user_id, product_id, quantity):
    execute("""INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s,%s,%s)
               ON DUPLICATE KEY UPDATE quantity=VALUES(quantity)""", (user_id, product_id, quantity))


def remove(user_id, product_id):
    execute("DELETE FROM cart_items WHERE user_id=%s AND product_id=%s", (user_id, product_id))


def clear(user_id, cur=None):
    sql, args = "DELETE FROM cart_items WHERE user_id=%s", (user_id,)
    if cur:
        cur.execute(sql, args)
    else:
        execute(sql, args)


def summary(rows, shipping_fee, free_from):
    """Tính tạm tính, phí giao hàng, tổng cộng cho các dòng hợp lệ."""
    valid = [r for r in rows if r["is_active"] and float(r["stock_quantity"]) >= float(r["quantity"])]
    subtotal = sum(int(r["line_total"]) for r in valid)
    ship = 0 if (subtotal >= free_from or subtotal == 0) else shipping_fee
    return {"subtotal": subtotal, "shipping_fee": ship, "total": subtotal + ship,
            "invalid": len(rows) - len(valid), "free_from": free_from,
            "free_remaining": max(0, free_from - subtotal)}
