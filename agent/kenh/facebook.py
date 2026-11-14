"""Facebook Graph API: nhắn Messenger, trả lời bình luận, đăng bài lên Page."""
import hashlib
import hmac
import logging

import requests

from .. import config

log = logging.getLogger(__name__)


def _url(path: str) -> str:
    return f"https://graph.facebook.com/{config.FB_GRAPH_VERSION}/{path}"


def _post(path: str, data: dict) -> dict:
    data = {**data, "access_token": config.FB_PAGE_ACCESS_TOKEN}
    res = requests.post(_url(path), json=data, timeout=30)
    kq = res.json()
    if res.status_code >= 400 or "error" in kq:
        raise RuntimeError(f"Facebook lỗi: {kq.get('error', kq)}")
    return kq


def kiem_tra_chu_ky(body: bytes, chu_ky: str | None) -> bool:
    """Xác thực webhook đúng là do Facebook gửi (header X-Hub-Signature-256)."""
    if not config.FB_APP_SECRET:
        log.warning("Chưa đặt FB_APP_SECRET — bỏ qua kiểm tra chữ ký Facebook")
        return True
    if not chu_ky or not chu_ky.startswith("sha256="):
        return False
    mong_doi = hmac.new(config.FB_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mong_doi, chu_ky.split("=", 1)[1])


def gui_messenger(psid: str, text: str) -> dict:
    # Messenger chỉ cho trả lời trong 24h kể từ tin cuối của khách
    return _post("me/messages", {"recipient": {"id": psid}, "messaging_type": "RESPONSE", "message": {"text": text}})


def tra_loi_binh_luan(comment_id: str, text: str) -> dict:
    return _post(f"{comment_id}/comments", {"message": text})


def dang_bai(noi_dung: str, anh_url: str | None = None) -> dict:
    if anh_url:
        return _post(f"{config.FB_PAGE_ID}/photos", {"url": anh_url, "caption": noi_dung})
    return _post(f"{config.FB_PAGE_ID}/feed", {"message": noi_dung})


def tach_su_kien(payload: dict) -> list[dict]:
    """Tách webhook Facebook thành danh sách tin khách: {kenh, khach_id, text, ten}."""
    ds = []
    if payload.get("object") != "page":
        return ds
    for entry in payload.get("entry", []):
        # Tin nhắn Messenger
        for m in entry.get("messaging", []):
            msg = m.get("message") or {}
            if msg.get("is_echo") or not msg.get("text"):
                continue
            ds.append({"kenh": "messenger", "khach_id": m["sender"]["id"], "text": msg["text"], "ten": ""})
        # Bình luận trên bài viết của Page
        for ch in entry.get("changes", []):
            v = ch.get("value") or {}
            if ch.get("field") != "feed" or v.get("item") != "comment" or v.get("verb") != "add":
                continue
            tu = v.get("from") or {}
            if tu.get("id") == config.FB_PAGE_ID or not v.get("message"):
                continue  # bỏ qua bình luận của chính Page
            ds.append(
                {"kenh": "fb_comment", "khach_id": v["comment_id"], "text": v["message"], "ten": tu.get("name", "")}
            )
    return ds
