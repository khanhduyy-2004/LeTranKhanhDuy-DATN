"""Bảng categories – danh mục sản phẩm."""
from ..db import execute, query, scalar
from ..utils import slugify


def all_active():
    return query("SELECT * FROM categories WHERE is_active=1 ORDER BY sort_order, name")


def all_with_count():
    return query("""SELECT c.*, COUNT(p.id) AS product_count
                    FROM categories c LEFT JOIN products p ON p.category_id=c.id
                    GROUP BY c.id ORDER BY c.sort_order, c.name""")


def get(cat_id):
    return query("SELECT * FROM categories WHERE id=%s", (cat_id,), one=True)


def get_by_slug(slug):
    return query("SELECT * FROM categories WHERE slug=%s AND is_active=1", (slug,), one=True)


def name_exists(name, exclude_id=0):
    return scalar("SELECT COUNT(*) FROM categories WHERE name=%s AND id<>%s", (name, exclude_id)) > 0


def _unique_slug(name, exclude_id=0):
    base = slug = slugify(name)
    n = 2
    while scalar("SELECT COUNT(*) FROM categories WHERE slug=%s AND id<>%s", (slug, exclude_id)):
        slug = f"{base}-{n}"
        n += 1
    return slug


def create(name, description, sort_order, is_active, image_url=None):
    return execute("""INSERT INTO categories (name, slug, description, sort_order, is_active, image_url)
                      VALUES (%s,%s,%s,%s,%s,%s)""",
                   (name, _unique_slug(name), description, sort_order, is_active, image_url))


def update(cat_id, name, description, sort_order, is_active, image_url=None):
    execute("""UPDATE categories SET name=%s, slug=%s, description=%s, sort_order=%s, is_active=%s,
               image_url=COALESCE(%s, image_url) WHERE id=%s""",
            (name, _unique_slug(name, cat_id), description, sort_order, is_active, image_url, cat_id))


def product_count(cat_id):
    return scalar("SELECT COUNT(*) FROM products WHERE category_id=%s", (cat_id,))


def delete(cat_id):
    """Không cho xóa danh mục đang có sản phẩm (đồng bộ với ràng buộc ON DELETE RESTRICT)."""
    if product_count(cat_id):
        return False
    execute("DELETE FROM categories WHERE id=%s", (cat_id,))
    return True
