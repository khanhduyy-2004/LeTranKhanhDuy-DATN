"""Bảng products, product_images – sản phẩm và hình ảnh."""
from ..db import execute, query, scalar
from ..utils import slugify

# Cột dùng chung khi hiển thị thẻ sản phẩm: ảnh đại diện + điểm đánh giá trung bình
CARD_COLUMNS = """
    p.id, p.name, p.slug, p.price, p.unit, p.origin, p.short_desc, p.stock_quantity, p.sold_quantity,
    p.is_featured, p.created_at, p.category_id, c.name AS category_name, c.slug AS category_slug,
    (SELECT image_url FROM product_images i WHERE i.product_id=p.id
      ORDER BY i.is_primary DESC, i.sort_order, i.id LIMIT 1) AS image,
    COALESCE(r.avg_rating, 0) AS avg_rating, COALESCE(r.review_count, 0) AS review_count
"""
CARD_FROM = """
    FROM products p
    JOIN categories c ON c.id=p.category_id
    LEFT JOIN v_product_rating r ON r.product_id=p.id
"""

SORTS = {
    "newest": ("Mới nhất", "p.created_at DESC, p.id DESC"),
    "price_asc": ("Giá tăng dần", "p.price ASC"),
    "price_desc": ("Giá giảm dần", "p.price DESC"),
    "best_selling": ("Bán chạy", "p.sold_quantity DESC"),
    "rating": ("Đánh giá cao", "avg_rating DESC, review_count DESC"),
    "name": ("Tên A → Z", "p.name ASC"),
}


def search(category_id=None, keyword=None, min_price=None, max_price=None, min_rating=None,
           in_stock=False, sort="newest", limit=12, offset=0):
    """Lọc sản phẩm cho cửa hàng: danh mục, từ khóa, khoảng giá, số sao, còn hàng; sắp xếp & phân trang."""
    where = ["p.is_active=1", "c.is_active=1"]
    args = []
    if category_id:
        where.append("p.category_id=%s"); args.append(category_id)
    if keyword:
        where.append("(p.name LIKE %s OR p.origin LIKE %s)"); args += [f"%{keyword}%"] * 2
    if min_price is not None:
        where.append("p.price>=%s"); args.append(min_price)
    if max_price is not None:
        where.append("p.price<=%s"); args.append(max_price)
    if min_rating:
        where.append("COALESCE(r.avg_rating,0)>=%s"); args.append(min_rating)
    if in_stock:
        where.append("p.stock_quantity>0")
    w = " AND ".join(where)
    total = scalar(f"SELECT COUNT(*) {CARD_FROM} WHERE {w}", args)
    order_by = SORTS.get(sort, SORTS["newest"])[1]
    rows = query(f"SELECT {CARD_COLUMNS} {CARD_FROM} WHERE {w} ORDER BY {order_by} LIMIT %s OFFSET %s",
                 args + [limit, offset])
    return rows, total


def price_bounds():
    row = query("SELECT MIN(price) AS lo, MAX(price) AS hi FROM products WHERE is_active=1", one=True)
    return int(row["lo"] or 0), int(row["hi"] or 0)


def featured(limit=8):
    return query(f"""SELECT {CARD_COLUMNS} {CARD_FROM} WHERE p.is_active=1 AND p.is_featured=1
                     ORDER BY p.created_at DESC LIMIT %s""", (limit,))


def newest(limit=8):
    return query(f"SELECT {CARD_COLUMNS} {CARD_FROM} WHERE p.is_active=1 ORDER BY p.created_at DESC, p.id DESC LIMIT %s",
                 (limit,))


def best_selling(limit=8):
    return query(f"""SELECT {CARD_COLUMNS} {CARD_FROM} WHERE p.is_active=1 AND p.sold_quantity>0
                     ORDER BY p.sold_quantity DESC LIMIT %s""", (limit,))


def related(product, limit=4):
    return query(f"""SELECT {CARD_COLUMNS} {CARD_FROM} WHERE p.is_active=1 AND p.category_id=%s AND p.id<>%s
                     ORDER BY p.sold_quantity DESC LIMIT %s""", (product["category_id"], product["id"], limit))


def by_ids(ids):
    if not ids:
        return []
    marks = ",".join(["%s"] * len(ids))
    return query(f"SELECT {CARD_COLUMNS} {CARD_FROM} WHERE p.id IN ({marks})", list(ids))


def suggest(keyword, limit=6):
    """Gợi ý tìm kiếm tức thời (AJAX)."""
    return query(f"""SELECT p.name, p.slug, p.price, p.unit,
                     (SELECT image_url FROM product_images i WHERE i.product_id=p.id
                       ORDER BY i.is_primary DESC, i.sort_order LIMIT 1) AS image
                     FROM products p WHERE p.is_active=1 AND p.name LIKE %s
                     ORDER BY p.sold_quantity DESC LIMIT %s""", (f"%{keyword}%", limit))


def get_by_slug(slug):
    return query(f"""SELECT {CARD_COLUMNS}, p.description, p.is_active {CARD_FROM}
                     WHERE p.slug=%s AND p.is_active=1""", (slug,), one=True)


def get(product_id):
    return query("SELECT * FROM products WHERE id=%s", (product_id,), one=True)


def images(product_id):
    return query("SELECT * FROM product_images WHERE product_id=%s ORDER BY is_primary DESC, sort_order, id",
                 (product_id,))


# ---------------- Quản trị ----------------
def admin_search(keyword, category_id, status, limit, offset):
    where, args = ["1=1"], []
    if keyword:
        where.append("p.name LIKE %s"); args.append(f"%{keyword}%")
    if category_id:
        where.append("p.category_id=%s"); args.append(category_id)
    if status == "active":
        where.append("p.is_active=1")
    elif status == "hidden":
        where.append("p.is_active=0")
    elif status == "low":
        where.append("p.stock_quantity<10")
    w = " AND ".join(where)
    total = scalar(f"SELECT COUNT(*) FROM products p WHERE {w}", args)
    rows = query(f"""SELECT p.*, c.name AS category_name,
                     (SELECT image_url FROM product_images i WHERE i.product_id=p.id
                       ORDER BY i.is_primary DESC, i.sort_order LIMIT 1) AS image
                     FROM products p JOIN categories c ON c.id=p.category_id
                     WHERE {w} ORDER BY p.created_at DESC, p.id DESC LIMIT %s OFFSET %s""", args + [limit, offset])
    return rows, total


def _unique_slug(name, exclude_id=0):
    base = slug = slugify(name)
    n = 2
    while scalar("SELECT COUNT(*) FROM products WHERE slug=%s AND id<>%s", (slug, exclude_id)):
        slug = f"{base}-{n}"
        n += 1
    return slug


FIELDS = ("category_id", "name", "price", "unit", "origin", "short_desc", "description",
          "stock_quantity", "is_active", "is_featured")


def create(data):
    cols = list(FIELDS) + ["slug"]
    values = [data[f] for f in FIELDS] + [_unique_slug(data["name"])]
    return execute(f"INSERT INTO products ({','.join(cols)}) VALUES ({','.join(['%s'] * len(cols))})", values)


def update(product_id, data):
    sets = ",".join(f"{f}=%s" for f in FIELDS) + ",slug=%s"
    execute(f"UPDATE products SET {sets} WHERE id=%s",
            [data[f] for f in FIELDS] + [_unique_slug(data["name"], product_id), product_id])


def toggle(product_id, field):
    if field in ("is_active", "is_featured"):
        execute(f"UPDATE products SET {field}=1-{field} WHERE id=%s", (product_id,))


def delete(product_id):
    """Xóa sản phẩm. Chi tiết đơn cũ vẫn giữ tên & giá (product_id → NULL)."""
    imgs = images(product_id)
    execute("DELETE FROM products WHERE id=%s", (product_id,))
    return imgs


def add_image(product_id, url):
    has_primary = scalar("SELECT COUNT(*) FROM product_images WHERE product_id=%s AND is_primary=1", (product_id,))
    order = scalar("SELECT COALESCE(MAX(sort_order),0)+1 FROM product_images WHERE product_id=%s", (product_id,))
    execute("INSERT INTO product_images (product_id, image_url, is_primary, sort_order) VALUES (%s,%s,%s,%s)",
            (product_id, url, 0 if has_primary else 1, order))


def get_image(image_id):
    return query("SELECT * FROM product_images WHERE id=%s", (image_id,), one=True)


def delete_image(image_id):
    img = get_image(image_id)
    if img:
        execute("DELETE FROM product_images WHERE id=%s", (image_id,))
        if img["is_primary"]:
            execute("""UPDATE product_images SET is_primary=1 WHERE product_id=%s
                       ORDER BY sort_order, id LIMIT 1""", (img["product_id"],))
    return img


def set_primary_image(image_id):
    img = get_image(image_id)
    if img:
        execute("UPDATE product_images SET is_primary=(id=%s) WHERE product_id=%s", (image_id, img["product_id"]))
    return img


def count_all():
    return scalar("SELECT COUNT(*) FROM products")
