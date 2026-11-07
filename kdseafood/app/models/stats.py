"""Thống kê cho trang quản trị (doanh thu chỉ tính đơn đã giao)."""
from datetime import date

from ..db import query, scalar


def summary():
    rev = lambda cond: scalar(f"SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status='delivered' AND {cond}")
    return {
        "revenue_today": rev("DATE(delivered_at)=CURDATE()"),
        "revenue_month": rev("DATE_FORMAT(delivered_at,'%Y-%m')=DATE_FORMAT(CURDATE(),'%Y-%m')"),
        "revenue_last_month": rev("DATE_FORMAT(delivered_at,'%Y-%m')="
                                  "DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH,'%Y-%m')"),
        "revenue_total": rev("1=1"),
        "orders_today": scalar("SELECT COUNT(*) FROM orders WHERE DATE(created_at)=CURDATE()"),
        "orders_month": scalar("""SELECT COUNT(*) FROM orders
                                  WHERE DATE_FORMAT(created_at,'%Y-%m')=DATE_FORMAT(CURDATE(),'%Y-%m')"""),
        "sold_quantity": scalar("SELECT COALESCE(SUM(sold_quantity),0) FROM products"),
    }


def monthly_revenue(months=12):
    """Doanh thu 12 tháng gần nhất (tháng không có đơn = 0)."""
    rows = query("SELECT month, revenue, order_count FROM v_revenue_by_month")
    data = {r["month"]: r for r in rows}
    today = date.today()
    out = []
    for i in range(months - 1, -1, -1):
        y, m = today.year, today.month - i
        while m <= 0:
            m += 12; y -= 1
        key = f"{y}-{m:02d}"
        r = data.get(key)
        out.append({"label": f"{m:02d}/{y}", "revenue": int(r["revenue"]) if r else 0,
                    "orders": int(r["order_count"]) if r else 0})
    return out


def best_sellers(limit=5):
    return query("SELECT * FROM v_best_selling_products ORDER BY total_sold DESC LIMIT %s", (limit,))


def low_stock(threshold=10):
    return query("""SELECT p.id, p.name, p.unit, p.stock_quantity, c.name AS category_name
                    FROM products p JOIN categories c ON c.id=p.category_id
                    WHERE p.is_active=1 AND p.stock_quantity<%s ORDER BY p.stock_quantity""", (threshold,))


def recent_orders(limit=8):
    return query("""SELECT o.*, u.full_name AS customer_name FROM orders o JOIN users u ON u.id=o.user_id
                    ORDER BY o.created_at DESC LIMIT %s""", (limit,))


def revenue_by_category():
    return query("""SELECT c.name, COALESCE(SUM(oi.line_total),0) AS revenue
                    FROM categories c
                    LEFT JOIN products p ON p.category_id=c.id
                    LEFT JOIN order_items oi ON oi.product_id=p.id
                    LEFT JOIN orders o ON o.id=oi.order_id
                    WHERE o.status='delivered' GROUP BY c.id, c.name ORDER BY revenue DESC""")
