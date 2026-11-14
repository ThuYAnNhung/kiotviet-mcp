"""Lưu trữ SQLite: bản nháp chờ duyệt, lịch sử chat khách, sản phẩm đã đăng, token Zalo."""
import json
import sqlite3
import threading
import time
import uuid

from . import config

_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def khoi_tao() -> None:
    with _lock, _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS ban_nhap (
                id TEXT PRIMARY KEY,
                loai TEXT NOT NULL,          -- tra_loi_khach | dang_bai
                kenh TEXT,                   -- messenger | fb_comment | zalo | telegram | facebook_page
                nguoi_nhan TEXT,             -- id khách / id bình luận
                noi_dung TEXT NOT NULL,
                du_lieu TEXT,                -- JSON phụ (tin gốc, ảnh, mã sp...)
                trang_thai TEXT NOT NULL DEFAULT 'cho_duyet',
                tao_luc REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lich_su_chat (
                kenh TEXT NOT NULL,
                khach_id TEXT NOT NULL,
                vai_tro TEXT NOT NULL,       -- khach | shop
                noi_dung TEXT NOT NULL,
                luc REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_chat ON lich_su_chat(kenh, khach_id, luc);
            CREATE TABLE IF NOT EXISTS da_dang (
                ma_sp TEXT PRIMARY KEY,
                luc REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS kv (
                khoa TEXT PRIMARY KEY,
                gia_tri TEXT
            );
            """
        )


# ---------- Bản nháp chờ duyệt ----------
def tao_ban_nhap(loai: str, kenh: str, nguoi_nhan: str, noi_dung: str, du_lieu: dict | None = None) -> str:
    bn_id = uuid.uuid4().hex[:10]
    with _lock, _conn() as c:
        c.execute(
            "INSERT INTO ban_nhap (id, loai, kenh, nguoi_nhan, noi_dung, du_lieu, tao_luc) VALUES (?,?,?,?,?,?,?)",
            (bn_id, loai, kenh, nguoi_nhan, noi_dung, json.dumps(du_lieu or {}, ensure_ascii=False), time.time()),
        )
    return bn_id


def lay_ban_nhap(bn_id: str) -> dict | None:
    with _lock, _conn() as c:
        row = c.execute("SELECT * FROM ban_nhap WHERE id=?", (bn_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["du_lieu"] = json.loads(d["du_lieu"] or "{}")
    return d


def cap_nhat_ban_nhap(bn_id: str, *, noi_dung: str | None = None, trang_thai: str | None = None) -> None:
    with _lock, _conn() as c:
        if noi_dung is not None:
            c.execute("UPDATE ban_nhap SET noi_dung=? WHERE id=?", (noi_dung, bn_id))
        if trang_thai is not None:
            c.execute("UPDATE ban_nhap SET trang_thai=? WHERE id=?", (trang_thai, bn_id))


def chuyen_trang_thai(bn_id: str, tu: str, sang: str) -> bool:
    """Đổi trạng thái nếu đang ở `tu`. Trả về True nếu đổi được (chống bấm duyệt 2 lần)."""
    with _lock, _conn() as c:
        cur = c.execute("UPDATE ban_nhap SET trang_thai=? WHERE id=? AND trang_thai=?", (sang, bn_id, tu))
        return cur.rowcount == 1


# ---------- Lịch sử chat ----------
def luu_chat(kenh: str, khach_id: str, vai_tro: str, noi_dung: str) -> None:
    with _lock, _conn() as c:
        c.execute(
            "INSERT INTO lich_su_chat (kenh, khach_id, vai_tro, noi_dung, luc) VALUES (?,?,?,?,?)",
            (kenh, khach_id, vai_tro, noi_dung, time.time()),
        )


def lay_chat(kenh: str, khach_id: str, so_tin: int = 10) -> list[dict]:
    with _lock, _conn() as c:
        rows = c.execute(
            "SELECT vai_tro, noi_dung FROM lich_su_chat WHERE kenh=? AND khach_id=? ORDER BY luc DESC LIMIT ?",
            (kenh, khach_id, so_tin),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


# ---------- Sản phẩm đã đăng ----------
def da_dang_gan_day(so_ngay: int = 30) -> set[str]:
    moc = time.time() - so_ngay * 86400
    with _lock, _conn() as c:
        rows = c.execute("SELECT ma_sp FROM da_dang WHERE luc>=?", (moc,)).fetchall()
    return {r["ma_sp"] for r in rows}


def danh_dau_da_dang(ma_sp: str) -> None:
    with _lock, _conn() as c:
        c.execute("INSERT OR REPLACE INTO da_dang (ma_sp, luc) VALUES (?,?)", (ma_sp, time.time()))


# ---------- Key-value (token Zalo, trạng thái chờ sửa...) ----------
def kv_get(khoa: str) -> str | None:
    with _lock, _conn() as c:
        row = c.execute("SELECT gia_tri FROM kv WHERE khoa=?", (khoa,)).fetchone()
    return row["gia_tri"] if row else None


def kv_set(khoa: str, gia_tri: str | None) -> None:
    with _lock, _conn() as c:
        if gia_tri is None:
            c.execute("DELETE FROM kv WHERE khoa=?", (khoa,))
        else:
            c.execute("INSERT OR REPLACE INTO kv (khoa, gia_tri) VALUES (?,?)", (khoa, gia_tri))
