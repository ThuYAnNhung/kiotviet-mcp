"""Kết nối KiotViet Public API (dùng chung cho mọi module)."""
import logging
import time

import requests

from . import config

log = logging.getLogger(__name__)

_token = {"value": None, "het_han": 0.0}
BASE = "https://public.kiotviet.vn"


def _lay_token() -> str | None:
    if _token["value"] and time.time() < _token["het_han"] - 60:
        return _token["value"]
    try:
        res = requests.post(
            "https://id.kiotviet.vn/connect/token",
            data={
                "client_id": config.KIOTVIET_CLIENT_ID,
                "client_secret": config.KIOTVIET_CLIENT_SECRET,
                "grant_type": "client_credentials",
                "scopes": "PublicApi.Access",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        res.raise_for_status()
        data = res.json()
        _token["value"] = data.get("access_token")
        _token["het_han"] = time.time() + int(data.get("expires_in", 3600))
        return _token["value"]
    except Exception as e:  # noqa: BLE001
        log.error("Lỗi lấy token KiotViet: %s", e)
        return None


def _get(path: str, params: dict) -> dict:
    token = _lay_token()
    if not token:
        raise RuntimeError("Không lấy được token KiotViet")
    res = requests.get(
        f"{BASE}{path}",
        params=params,
        headers={"Retailer": config.KIOTVIET_RETAILER, "Authorization": f"Bearer {token}"},
        timeout=20,
    )
    res.raise_for_status()
    return res.json()


def _rut_gon_sp(item: dict) -> dict:
    return {
        "ma": item.get("code"),
        "ten": item.get("fullName") or item.get("name"),
        "gia": item.get("basePrice", 0),
        "ton": item.get("onHand", 0),
        "don_vi": item.get("unit"),
        "nhom": item.get("categoryName"),
        "mo_ta": (item.get("description") or "")[:500],
        "anh": (item.get("images") or [None])[0],
    }


def tim_san_pham(tu_khoa: str, so_luong: int = 5) -> list[dict]:
    data = _get("/products", {"kw": tu_khoa, "pageSize": so_luong, "includeInventory": "true"})
    return [_rut_gon_sp(i) for i in data.get("data", [])]


def danh_sach_san_pham(so_luong: int = 100, vi_tri: int = 0) -> list[dict]:
    data = _get("/products", {"pageSize": so_luong, "currentItem": vi_tri, "includeInventory": "true"})
    return [_rut_gon_sp(i) for i in data.get("data", [])]


def dinh_dang_sp(ds: list[dict]) -> str:
    if not ds:
        return "Không tìm thấy sản phẩm phù hợp trong kho."
    dong = []
    for sp in ds:
        dong.append(
            f"• [{sp['ma']}] {sp['ten']} | Giá: {sp['gia']:,.0f}đ | Tồn: {sp['ton']} {sp['don_vi'] or ''}".strip()
            + (f" | Nhóm: {sp['nhom']}" if sp.get("nhom") else "")
            + (f"\n  Mô tả: {sp['mo_ta']}" if sp.get("mo_ta") else "")
        )
    return "\n".join(dong)
