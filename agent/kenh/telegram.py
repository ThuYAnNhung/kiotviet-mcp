"""Telegram Bot API: gửi tin cho anh, gửi bản nháp kèm nút duyệt."""
import logging

import requests

from .. import config

log = logging.getLogger(__name__)

GIOI_HAN = 4000  # Telegram giới hạn 4096 ký tự/tin


def _api(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}"
    try:
        res = requests.post(url, json=payload, timeout=20)
        data = res.json()
        if not data.get("ok"):
            log.error("Telegram %s lỗi: %s", method, data)
        return data
    except Exception as e:  # noqa: BLE001
        log.error("Không gọi được Telegram %s: %s", method, e)
        return {"ok": False}


def gui(text: str, chat_id: str | None = None, nut: list | None = None) -> dict:
    chat_id = chat_id or config.TELEGRAM_OWNER_CHAT_ID
    phan = [text[i : i + GIOI_HAN] for i in range(0, len(text), GIOI_HAN)] or [""]
    kq = {}
    for i, p in enumerate(phan):
        payload = {"chat_id": chat_id, "text": p, "disable_web_page_preview": True}
        if nut and i == len(phan) - 1:  # nút gắn vào phần cuối
            payload["reply_markup"] = {"inline_keyboard": nut}
        kq = _api("sendMessage", payload)
    return kq


def nut_duyet(bn_id: str) -> list:
    return [
        [
            {"text": "✅ Gửi", "callback_data": f"ok:{bn_id}"},
            {"text": "✏️ Sửa", "callback_data": f"sua:{bn_id}"},
            {"text": "❌ Bỏ", "callback_data": f"bo:{bn_id}"},
        ]
    ]


def gui_ban_nhap(tieu_de: str, noi_dung: str, bn_id: str) -> None:
    gui(f"{tieu_de}\n\n━━━━━━━━━━\n{noi_dung}\n━━━━━━━━━━\nMã nháp: {bn_id}", nut=nut_duyet(bn_id))


def tra_loi_nut(callback_id: str, text: str = "") -> None:
    _api("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})


def bo_nut(chat_id, message_id) -> None:
    _api("editMessageReplyMarkup", {"chat_id": chat_id, "message_id": message_id, "reply_markup": {"inline_keyboard": []}})


def dat_webhook(url: str) -> dict:
    payload = {"url": url, "allowed_updates": ["message", "callback_query"]}
    if config.TELEGRAM_WEBHOOK_SECRET:
        payload["secret_token"] = config.TELEGRAM_WEBHOOK_SECRET
    return _api("setWebhook", payload)
