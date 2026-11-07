"""Bảng banners – slider trang chủ."""
from ..db import query


def active():
    return query("SELECT * FROM banners WHERE is_active=1 ORDER BY sort_order, id")
