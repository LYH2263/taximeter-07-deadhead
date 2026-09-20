import sqlite3
from datetime import datetime, timezone


class EmptyRateConflict(Exception):
    """启用冲突：已有一条启用中的空驶单价。"""

    def __init__(self, active_id: int, incoming: str):
        self.active_id = active_id
        self.incoming = incoming
        super().__init__(f"空驶单价只允许一条启用：已启用 #{active_id}，与 {incoming} 冲突")


def _row(r) -> dict:
    return {"id": r["id"], "per_km": r["per_km"], "active": bool(r["active"]), "created_at": r["created_at"]}


def list_all(conn: sqlite3.Connection) -> list[dict]:
    return [_row(r) for r in conn.execute("SELECT * FROM empty_rate ORDER BY id").fetchall()]


def get_active(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM empty_rate WHERE active=1 ORDER BY id LIMIT 1").fetchone()
    return _row(row) if row else None


def create(conn: sqlite3.Connection, per_km: float, active: bool) -> dict:
    if active:
        cur = get_active(conn)
        if cur:
            raise EmptyRateConflict(cur["id"], f"新单价({per_km}/km)")
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute("INSERT INTO empty_rate(per_km,active,created_at) VALUES (?,?,?)", (per_km, 1 if active else 0, now))
    conn.commit()
    return _row(conn.execute("SELECT * FROM empty_rate WHERE id=?", (cur.lastrowid,)).fetchone())


def update(conn: sqlite3.Connection, rid: int, per_km: float) -> dict | None:
    conn.execute("UPDATE empty_rate SET per_km=? WHERE id=?", (per_km, rid))
    conn.commit()
    row = conn.execute("SELECT * FROM empty_rate WHERE id=?", (rid,)).fetchone()
    return _row(row) if row else None


def set_active(conn: sqlite3.Connection, rid: int, active: bool) -> dict | None:
    row = conn.execute("SELECT * FROM empty_rate WHERE id=?", (rid,)).fetchone()
    if not row:
        return None
    if active:
        cur = get_active(conn)
        if cur and cur["id"] != rid:
            raise EmptyRateConflict(cur["id"], f"#{rid}")
    conn.execute("UPDATE empty_rate SET active=? WHERE id=?", (1 if active else 0, rid))
    conn.commit()
    return _row(conn.execute("SELECT * FROM empty_rate WHERE id=?", (rid,)).fetchone())
