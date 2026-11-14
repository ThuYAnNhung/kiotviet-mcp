"""Zalo Official Account API: nhận và gửi tin nhắn tư vấn."""
import hashlib
import hmac
import logging

import requests

from .. import config, storage

log = logging.getLogger(__name__)


def _token() -> str:
    return storage.kv_get("zalo_access_token") or config.ZALO_ACCESS_TOKEN


def lam_moi_token() -> bool:
    """Access token Zalo hết hạn sau ~25 giờ; dùng refresh token để lấy token mới."""
    refresh = storage.kv_get("zalo_refresh_token") or config.ZALO_REFRESH_TOKEN
    if not (refresh and config.ZALO_APP_ID and config.ZALO_APP_SECRET):
        return False
    res = requests.post(
        "https://oauth.zaloapp.com/v4/oa/access_token",
        headers={"secret_key": config.ZALO_APP_SECRET, "Content-Type": "application/x-www-form-urlencoded"},
        data={"refresh_token": refresh, "app_id": config.ZALO_APP_ID, "grant_type": "refresh_token"},
        timeout=20,
    )
    data = res.json()
    if "access_token" not in data:
        log.error("Làm mới token Zalo thất bại: %s", data)
        return False
    storage.kv_set("zalo_access_token", data["access_token"])
    storage.kv_set("zalo_refresh_token", data.get("refresh_token", refresh))
    log.info("Đã làm mới token Zalo")
    return True


def kiem_tra_chu_ky(body: bytes, timestamp: str, chu_ky: str | None) -> bool:
    """Header X-ZEvent-Signature = 'mac=' + sha256(appId + body + timestamp + OASecretKey)."""
    if not config.ZALO_OA_SECRET_KEY:
        log.warning("Chưa đặt ZALO_OA_SECRET_KEY — bỏ qua kiểm tra chữ ký Zalo")
        return True
    if not chu_ky:
        return False
    chuoi = config.ZALO_APP_ID + body.decode("utf-8") + str(timestamp) + config.ZALO_OA_SECRET_KEY
    mong_doi = hashlib.sha256(chuoi.encode("utf-8")).hexdigest()
    return hmac.compare_digest(mong_doi, chu_ky.removeprefix("mac="))


def gui_tin(user_id: str, text: str, _thu_lai: bool = True) -> dict:
    res = requests.post(
        "https://openapi.zalo.me/v3.0/oa/message/cs",
        headers={"access_token": _token(), "Content-Type": "application/json"},
        json={"recipient": {"user_id": user_id}, "message": {"text": text[:2000]}},
        timeout=20,
    )
    data = res.json()
    if data.get("error", 0) != 0:
        # -216: token hết hạn → làm mới rồi thử lại một lần
        if _thu_lai and data.get("error") in (-216, -124) and lam_moi_token():
            return gui_tin(user_id, text, _thu_lai=False)
        raise RuntimeError(f"Zalo lỗi: {data}")
    return data


def tach_su_kien(payload: dict) -> list[dict]:
    if payload.get("event_name") != "user_send_text":
        return []
    text = (payload.get("message") or {}).get("text")
    uid = (payload.get("sender") or {}).get("id")
    if not (text and uid):
        return []
    return [{"kenh": "zalo", "khach_id": uid, "text": text, "ten": ""}]
