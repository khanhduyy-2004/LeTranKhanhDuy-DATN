"""Quản lý sản phẩm: thêm, sửa, xóa, ẩn/hiện, nổi bật, ảnh, tồn kho."""
from flask import abort, current_app, flash, redirect, render_template, request, url_for

from . import bp
from ...models import category, product
from ...utils import Pagination, get_page, remove_image, save_image, to_float, to_int


@bp.route("/san-pham")
def products():
    per = current_app.config["ADMIN_PER_PAGE"]
    page = get_page()
    kw, cat, status = request.args.get("q", "").strip(), to_int(request.args.get("danh-muc")), request.args.get("loc")
    rows, total = product.admin_search(kw, cat, status, per, (page - 1) * per)
    return render_template("admin/products/index.html", products=rows, pagination=Pagination(page, per, total),
                           total=total, categories=category.all_with_count(), q=kw, cat=cat, status=status)


def _read_form():
    f = request.form
    data = {
        "category_id": to_int(f.get("category_id")),
        "name": f.get("name", "").strip(),
        "price": to_float(f.get("price"), -1),
        "unit": f.get("unit", "kg").strip() or "kg",
        "origin": f.get("origin", "").strip() or None,
        "short_desc": f.get("short_desc", "").strip()[:255] or None,
        "description": f.get("description", "").strip() or None,
        "stock_quantity": to_float(f.get("stock_quantity"), -1),
        "is_active": 1 if f.get("is_active") else 0,
        "is_featured": 1 if f.get("is_featured") else 0,
    }
    errors = []
    if not data["name"]:
        errors.append("Vui lòng nhập tên sản phẩm.")
    if not data["category_id"] or not category.get(data["category_id"]):
        errors.append("Vui lòng chọn danh mục.")
    if data["price"] < 0:
        errors.append("Giá bán không hợp lệ.")
    if data["stock_quantity"] < 0:
        errors.append("Số lượng tồn không hợp lệ.")
    return data, errors


def _save_uploads(pid):
    for fs in request.files.getlist("images"):
        if fs and fs.filename:
            try:
                product.add_image(pid, save_image(fs, "products"))
            except ValueError as e:
                flash(f"{fs.filename}: {e}", "warning")


@bp.route("/san-pham/them", methods=["GET", "POST"])
def product_add():
    data = {"is_active": 1, "unit": "kg"}
    if request.method == "POST":
        data, errors = _read_form()
        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            pid = product.create(data)
            _save_uploads(pid)
            flash(f"Đã thêm sản phẩm “{data['name']}”.", "success")
            return redirect(url_for("admin.product_edit", pid=pid))
    return render_template("admin/products/form.html", p=data, images=[], categories=category.all_with_count())


@bp.route("/san-pham/<int:pid>/sua", methods=["GET", "POST"])
def product_edit(pid):
    p = product.get(pid)
    if not p:
        abort(404)
    if request.method == "POST":
        data, errors = _read_form()
        if errors:
            for e in errors:
                flash(e, "danger")
            p = {**p, **data}
        else:
            product.update(pid, data)
            _save_uploads(pid)
            flash("Đã lưu thay đổi.", "success")
            return redirect(url_for("admin.product_edit", pid=pid))
    return render_template("admin/products/form.html", p=p, images=product.images(pid),
                           categories=category.all_with_count())


@bp.route("/san-pham/<int:pid>/bat-tat/<field>", methods=["POST"])
def product_toggle(pid, field):
    product.toggle(pid, field)
    return redirect(request.referrer or url_for("admin.products"))


@bp.route("/san-pham/<int:pid>/xoa", methods=["POST"])
def product_delete(pid):
    for img in product.delete(pid):
        remove_image(img["image_url"])
    flash("Đã xóa sản phẩm.", "success")
    return redirect(url_for("admin.products"))


@bp.route("/anh/<int:iid>/xoa", methods=["POST"])
def image_delete(iid):
    img = product.delete_image(iid)
    if not img:
        abort(404)
    remove_image(img["image_url"])
    return redirect(url_for("admin.product_edit", pid=img["product_id"]))


@bp.route("/anh/<int:iid>/dai-dien", methods=["POST"])
def image_primary(iid):
    img = product.set_primary_image(iid)
    if not img:
        abort(404)
    return redirect(url_for("admin.product_edit", pid=img["product_id"]))
