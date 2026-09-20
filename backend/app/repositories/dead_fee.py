import sqlite3
from datetime import datetime, timezone


class DeadRateConflict(Exception):
    """只允许一条启用：提交标识与已启用标识互斥。"""

    def __init__(self, incoming_code: str, existing_code: str):
        self.incoming_code = incoming_code
        self.existing_code = existing_code
        super().__init__(
            f"只允许一条启用的空驶单价：已启用「{existing_code}」，与本次提交的「{incoming_code}」冲突"
        )


class DeadRateCodeExists(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"空驶单价标识「{code}」已存在")


class DeadRateNotFound(Exception):
    def __init__(self, rate_id: int):
        self.rate_id = rate_id
        super().__init__(f"空驶单价 #{rate_id} 不存在")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(conn: sqlite3.Connection, rate_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM dead_km_rates WHERE id=?", (rate_id,)).fetchone()


def get(conn: sqlite3.Connection, rate_id: int) -> dict | None:
    row = _row(conn, rate_id)
    return dict(row) if row else None


def get_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute("SELECT * FROM dead_km_rates WHERE code=?", (code,)).fetchone()
    return dict(row) if row else None


def list_all(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM dead_km_rates ORDER BY id").fetchall()]


def get_active(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM dead_km_rates WHERE active=1 ORDER BY id LIMIT 1").fetchone()
    return dict(row) if row else None


def _assert_no_other_active(conn: sqlite3.Connection, incoming_code: str, exclude_id: int | None = None) -> None:
    sql = "SELECT code FROM dead_km_rates WHERE active=1"
    args: tuple = ()
    if exclude_id is not None:
        sql += " AND id<>?"
        args = (exclude_id,)
    row = conn.execute(sql + " LIMIT 1", args).fetchone()
    if row:
        raise DeadRateConflict(incoming_code, row["code"])


def create(conn: sqlite3.Connection, code: str, name: str, price_per_km: float, active: bool) -> dict:
    if not code or not str(code).strip():
        raise ValueError("空驶单价标识不能为空")
    if float(price_per_km) <= 0:
        raise ValueError("空驶单价必须为正数")
    if get_by_code(conn, code):
        raise DeadRateCodeExists(code)
    if active:
        _assert_no_other_active(conn, code)
    now = _now()
    cur = conn.execute(
        "INSERT INTO dead_km_rates(code,name,price_per_km,active,created_at,updated_at) VALUES (?,?,?,?,?,?)",
        (code, name, float(price_per_km), 1 if active else 0, now, now),
    )
    conn.commit()
    return get(conn, int(cur.lastrowid))


def update(
    conn: sqlite3.Connection,
    rate_id: int,
    name: str | None = None,
    price_per_km: float | None = None,
    active: bool | None = None,
) -> dict:
    row = _row(conn, rate_id)
    if not row:
        raise DeadRateNotFound(rate_id)
    if price_per_km is not None and float(price_per_km) <= 0:
        raise ValueError("空驶单价必须为正数")

    fields, args = [], []
    if name is not None:
        fields.append("name=?")
        args.append(name)
    if price_per_km is not None:
        fields.append("price_per_km=?")
        args.append(float(price_per_km))
    if active is not None:
        if active:
            _assert_no_other_active(conn, row["code"], rate_id)
        fields.append("active=?")
        args.append(1 if active else 0)
    if not fields:
        return dict(row)
    fields.append("updated_at=?")
    args.append(_now())
    args.append(rate_id)
    conn.execute(f"UPDATE dead_km_rates SET {', '.join(fields)} WHERE id=?", args)
    conn.commit()
    return get(conn, rate_id)
