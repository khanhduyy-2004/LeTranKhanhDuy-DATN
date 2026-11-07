"""Bảng orders, order_items, order_status_history – đặt hàng và xử lý đơn hàng."""
from datetime import datetime

from ..db import query, scalar, transaction
from ..utils import ORDER_FLOW, ORDER_STATUS


class OrderError(Exception):
    """Lỗi nghiệp vụ hiển thị được cho người dùng."""


# ---------------- Đặt hàng ----------------
def place(user_id, address, payment_method, note, shipping_fee, free_from):
    """Tạo đơn hàng từ giỏ trong MỘT giao dịch:
    khóa dòng sản phẩm (FOR UPDATE) → kiểm tra tồn kho → tạo đơn + chi tiết → trừ kho → ghi lịch sử → xóa giỏ."""
    with transaction() as cur:
        cur.execute("""SELECT ci.product_id, ci.quantity, p.name, p.unit, p.price, p.stock_quantity, p.is_active
                       FROM cart_items ci JOIN products p ON p.id=ci.product_id
                       WHERE ci.user_id=%s FOR UPDATE""", (user_id,))
        rows = cur.fetchall()
        if not rows:
            raise OrderError("Giỏ hàng đang trống.")
        for r in rows:
            if not r["is_active"]:
                raise OrderError(f"Sản phẩm “{r['name']}” đã ngừng kinh doanh, vui lòng xóa khỏi giỏ.")
            if float(r["quantity"]) > float(r["stock_quantity"]):
                raise OrderError(f"“{r['name']}” chỉ còn {float(r['stock_quantity']):g} {r['unit']}.")

        subtotal = sum(round(float(r["price"]) * float(r["quantity"])) for r in rows)
        ship = 0 if subtotal >= free_from else shipping_fee
        addr_text = ", ".join(x for x in (address["address_line"], address.get("ward"), address.get("district"),
                                          address["province"]) if x)
        cur.execute("""INSERT INTO orders (order_code, user_id, receiver_name, receiver_phone, shipping_address,
                          subtotal, shipping_fee, total_amount, payment_method, note)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    ("TMP", user_id, address["receiver_name"], address["phone"], addr_text,
                     subtotal, ship, subtotal + ship, payment_method, note or None))
        order_id = cur.lastrowid
        code = f"KD{datetime.now():%y%m%d}{order_id:04d}"
        cur.execute("UPDATE orders SET order_code=%s WHERE id=%s", (code, order_id))
        for r in rows:
            cur.execute("""INSERT INTO order_items (order_id, product_id, product_name, unit, unit_price, quantity)
                           VALUES (%s,%s,%s,%s,%s,%s)""",
                        (order_id, r["product_id"], r["name"], r["unit"], r["price"], r["quantity"]))
            cur.execute("UPDATE products SET stock_quantity=stock_quantity-%s WHERE id=%s",
                        (r["quantity"], r["product_id"]))
        cur.execute("""INSERT INTO order_status_history (order_id, old_status, new_status, changed_by_user_id, note)
                       VALUES (%s,NULL,'pending',%s,'Khách hàng đặt hàng')""", (order_id, user_id))
        cur.execute("DELETE FROM cart_items WHERE user_id=%s", (user_id,))
    return code


def mark_paid_sandbox(order_id, ref):
    with transaction() as cur:
        cur.execute("""UPDATE orders SET payment_status='paid', transaction_ref=%s
                       WHERE id=%s AND payment_status='unpaid' AND status<>'cancelled'""", (ref, order_id))


# ---------------- Truy vấn ----------------
def get_by_code(code, user_id=None):
    sql, args = "SELECT * FROM orders WHERE order_code=%s", [code]
    if user_id is not None:
        sql += " AND user_id=%s"; args.append(user_id)
    return query(sql, args, one=True)


def get(order_id):
    return query("""SELECT o.*, u.full_name AS customer_name, u.email AS customer_email, u.phone AS customer_phone
                    FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=%s""", (order_id,), one=True)


def items(order_id):
    return query("""SELECT oi.*, p.slug,
                    (SELECT image_url FROM product_images i WHERE i.product_id=oi.product_id
                      ORDER BY i.is_primary DESC, i.sort_order LIMIT 1) AS image
                    FROM order_items oi LEFT JOIN products p ON p.id=oi.product_id
                    WHERE oi.order_id=%s ORDER BY oi.id""", (order_id,))


def history(order_id):
    return query("""SELECT h.*, a.full_name AS admin_name, u.full_name AS user_name
                    FROM order_status_history h
                    LEFT JOIN admins a ON a.id=h.changed_by_admin_id
                    LEFT JOIN users  u ON u.id=h.changed_by_user_id
                    WHERE h.order_id=%s ORDER BY h.created_at, h.id""", (order_id,))


def list_by_user(user_id, status=None):
    sql = """SELECT o.*, (SELECT COUNT(*) FROM order_items i WHERE i.order_id=o.id) AS item_count,
             (SELECT product_name FROM order_items i WHERE i.order_id=o.id ORDER BY i.id LIMIT 1) AS first_item
             FROM orders o WHERE o.user_id=%s"""
    args = [user_id]
    if status in ORDER_STATUS:
        sql += " AND o.status=%s"; args.append(status)
    return query(sql + " ORDER BY o.created_at DESC", args)


def count_by_status(user_id=None):
    sql, args = "SELECT status, COUNT(*) AS n FROM orders", []
    if user_id:
        sql += " WHERE user_id=%s"; args.append(user_id)
    rows = query(sql + " GROUP BY status", args)
    data = {s: 0 for s in ORDER_STATUS}
    data.update({r["status"]: r["n"] for r in rows})
    data["all"] = sum(data.values())
    return data


def admin_search(keyword, status, date_from, date_to, limit, offset):
    where, args = ["1=1"], []
    if keyword:
        where.append("(o.order_code LIKE %s OR o.receiver_name LIKE %s OR o.receiver_phone LIKE %s OR u.full_name LIKE %s)")
        args += [f"%{keyword}%"] * 4
    if status in ORDER_STATUS:
        where.append("o.status=%s"); args.append(status)
    if date_from:
        where.append("DATE(o.created_at)>=%s"); args.append(date_from)
    if date_to:
        where.append("DATE(o.created_at)<=%s"); args.append(date_to)
    w = " AND ".join(where)
    total = scalar(f"SELECT COUNT(*) FROM orders o JOIN users u ON u.id=o.user_id WHERE {w}", args)
    rows = query(f"""SELECT o.*, u.full_name AS customer_name,
                     (SELECT COUNT(*) FROM order_items i WHERE i.order_id=o.id) AS item_count
                     FROM orders o JOIN users u ON u.id=o.user_id WHERE {w}
                     ORDER BY o.created_at DESC LIMIT %s OFFSET %s""", args + [limit, offset])
    return rows, total


# ---------------- Chuyển trạng thái ----------------
def allowed_next(status):
    """Đơn chỉ đi tiến theo luồng; được hủy khi chưa giao xong."""
    if status in ("delivered", "cancelled"):
        return []
    nxt = [ORDER_FLOW[ORDER_FLOW.index(status) + 1]]
    return nxt + ["cancelled"]


def change_status(order_id, new_status, note=None, admin_id=None, user_id=None):
    with transaction() as cur:
        cur.execute("SELECT * FROM orders WHERE id=%s FOR UPDATE", (order_id,))
        order = cur.fetchone()
        if not order:
            raise OrderError("Không tìm thấy đơn hàng.")
        old = order["status"]
        if user_id is not None:  # khách hàng chỉ được hủy đơn chờ xác nhận của chính mình
            if order["user_id"] != user_id or new_status != "cancelled" or old != "pending":
                raise OrderError("Chỉ có thể hủy đơn hàng đang ở trạng thái “Chờ xác nhận”.")
        elif new_status not in allowed_next(old):
            raise OrderError(f"Không thể chuyển từ “{ORDER_STATUS[old][0]}” sang “{ORDER_STATUS[new_status][0]}”.")

        if new_status == "cancelled":
            # hoàn lại tồn kho
            cur.execute("""UPDATE products p JOIN order_items oi ON oi.product_id=p.id
                           SET p.stock_quantity=p.stock_quantity+oi.quantity WHERE oi.order_id=%s""", (order_id,))
            pay = "refunded" if order["payment_status"] == "paid" else order["payment_status"]
            cur.execute("UPDATE orders SET status='cancelled', payment_status=%s, cancel_reason=%s WHERE id=%s",
                        (pay, note, order_id))
        elif new_status == "delivered":
            cur.execute("""UPDATE orders SET status='delivered', payment_status='paid', delivered_at=NOW()
                           WHERE id=%s""", (order_id,))
            cur.execute("""UPDATE products p JOIN order_items oi ON oi.product_id=p.id
                           SET p.sold_quantity=p.sold_quantity+oi.quantity WHERE oi.order_id=%s""", (order_id,))
        else:
            cur.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))

        cur.execute("""INSERT INTO order_status_history
                       (order_id, old_status, new_status, changed_by_admin_id, changed_by_user_id, note)
                       VALUES (%s,%s,%s,%s,%s,%s)""", (order_id, old, new_status, admin_id, user_id, note))


def has_delivered_product(user_id, product_id):
    return scalar("""SELECT COUNT(*) FROM orders o JOIN order_items oi ON oi.order_id=o.id
                     WHERE o.user_id=%s AND oi.product_id=%s AND o.status='delivered'""", (user_id, product_id)) > 0
