"""Quản lý danh mục sản phẩm."""
from flask import flash, redirect, render_template, request, url_for

from . import bp
from ...models import category
from ...utils import save_image, to_int


def _form():
    return (request.form.get("name", "").strip(), request.form.get("description", "").strip() or None,
            to_int(request.form.get("sort_order"), 0) or 0, 1 if request.form.get("is_active") else 0)


@bp.route("/danh-muc")
def categories():
    edit = category.get(to_int(request.args.get("sua"))) if request.args.get("sua") else None
    return render_template("admin/categories/index.html", categories=category.all_with_count(), edit=edit)


@bp.route("/danh-muc/luu", methods=["POST"])
def category_save():
    cid = to_int(request.form.get("id"))
    name, desc, order, active = _form()
    if not name:
        flash("Vui lòng nhập tên danh mục.", "danger")
    elif category.name_exists(name, cid or 0):
        flash("Tên danh mục đã tồn tại.", "danger")
    else:
        try:
            img = save_image(request.files.get("image"), "categories")
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("admin.categories"))
        if cid:
            category.update(cid, name, desc, order, active, img)
            flash(f"Đã cập nhật danh mục “{name}”.", "success")
        else:
            category.create(name, desc, order, active, img)
            flash(f"Đã thêm danh mục “{name}”.", "success")
    return redirect(url_for("admin.categories"))


@bp.route("/danh-muc/<int:cid>/xoa", methods=["POST"])
def category_delete(cid):
    if category.delete(cid):
        flash("Đã xóa danh mục.", "success")
    else:
        flash("Không thể xóa: danh mục đang có sản phẩm. Hãy chuyển hoặc xóa sản phẩm trước.", "danger")
    return redirect(url_for("admin.categories"))
