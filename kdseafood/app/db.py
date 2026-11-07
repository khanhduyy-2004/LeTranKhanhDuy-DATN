"""Kết nối MySQL bằng PyMySQL – mỗi request dùng một kết nối (lưu trong flask.g)."""
from contextlib import contextmanager

import pymysql
from flask import current_app, g


def get_db():
    if "db" not in g:
        cfg = current_app.config
        params = dict(
            user=cfg["DB_USER"], password=cfg["DB_PASSWORD"], database=cfg["DB_NAME"],
            charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, autocommit=True,
        )
        if cfg.get("DB_UNIX_SOCKET"):
            params["unix_socket"] = cfg["DB_UNIX_SOCKET"]
        else:
            params.update(host=cfg["DB_HOST"], port=cfg["DB_PORT"])
        g.db = pymysql.connect(**params)
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=None, one=False):
    """SELECT – trả về list[dict] hoặc 1 dict (one=True). Luôn dùng tham số %s để chống SQL Injection."""
    with get_db().cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone() if one else cur.fetchall()


def scalar(sql, args=None, default=0):
    row = query(sql, args, one=True)
    if not row:
        return default
    value = next(iter(row.values()))
    return default if value is None else value


def execute(sql, args=None):
    """INSERT / UPDATE / DELETE – trả về lastrowid."""
    with get_db().cursor() as cur:
        cur.execute(sql, args)
        return cur.lastrowid


@contextmanager
def transaction():
    """Thực hiện nhiều câu lệnh trong 1 giao dịch: lỗi ở bất kỳ bước nào sẽ rollback toàn bộ."""
    conn = get_db()
    conn.begin()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def init_app(app):
    app.teardown_appcontext(close_db)
