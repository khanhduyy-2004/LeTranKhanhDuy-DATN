"""Bảng addresses – sổ địa chỉ nhận hàng."""
from ..db import execute, query, scalar, transaction

FIELDS = ("receiver_name", "phone", "address_line", "ward", "district", "province")


def list_for(user_id):
    return query("SELECT * FROM addresses WHERE user_id=%s ORDER BY is_default DESC, id", (user_id,))


def get(address_id, user_id):
    return query("SELECT * FROM addresses WHERE id=%s AND user_id=%s", (address_id, user_id), one=True)


def create(user_id, data, make_default=False):
    first = scalar("SELECT COUNT(*) FROM addresses WHERE user_id=%s", (user_id,)) == 0
    with transaction() as cur:
        if make_default or first:
            cur.execute("UPDATE addresses SET is_default=0 WHERE user_id=%s", (user_id,))
        cur.execute(f"""INSERT INTO addresses (user_id, {','.join(FIELDS)}, is_default)
                        VALUES (%s,{','.join(['%s'] * len(FIELDS))},%s)""",
                    [user_id] + [data[f] for f in FIELDS] + [1 if (make_default or first) else 0])
        return cur.lastrowid


def update(address_id, user_id, data):
    execute(f"UPDATE addresses SET {','.join(f + '=%s' for f in FIELDS)} WHERE id=%s AND user_id=%s",
            [data[f] for f in FIELDS] + [address_id, user_id])


def set_default(address_id, user_id):
    with transaction() as cur:
        cur.execute("UPDATE addresses SET is_default=(id=%s) WHERE user_id=%s", (address_id, user_id))


def delete(address_id, user_id):
    addr = get(address_id, user_id)
    if not addr:
        return
    execute("DELETE FROM addresses WHERE id=%s AND user_id=%s", (address_id, user_id))
    if addr["is_default"]:
        execute("UPDATE addresses SET is_default=1 WHERE user_id=%s ORDER BY id LIMIT 1", (user_id,))
