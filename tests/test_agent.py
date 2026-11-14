"""Kiểm thử toàn bộ luồng agent mà không gọi API thật.

Chạy:  python -m pytest tests/ -q
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["ANTHROPIC_API_KEY"] = "test"
os.environ["TELEGRAM_OWNER_CHAT_ID"] = "111"
os.environ["FB_PAGE_ID"] = "999"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from agent import brain, kiotviet, storage  # noqa: E402
from agent.kenh import facebook, telegram  # noqa: E402
from agent.modules import dang_bai, dieu_khien  # noqa: E402

SP = {"code": "SP01", "fullName": "Thuốc cầu trùng ABC", "basePrice": 85000, "onHand": 12,
      "unit": "chai", "categoryName": "Gà", "description": "Trị cầu trùng", "images": ["https://img/1.jpg"]}


def _block(**kw):
    return SimpleNamespace(**kw)


def _res(stop, content):
    return SimpleNamespace(stop_reason=stop, content=content)


@pytest.fixture(autouse=True)
def moi_truong():
    storage.khoi_tao()
    gui_tg = []
    with patch.object(telegram, "_api", side_effect=lambda m, p: gui_tg.append((m, p)) or {"ok": True}), \
         patch.object(kiotviet, "_get", return_value={"data": [SP]}):
        yield gui_tg


def _tin_tg(gui_tg):
    return [p["text"] for m, p in gui_tg if m == "sendMessage"]


def _nut_ok(gui_tg):
    for m, p in reversed(gui_tg):
        if m == "sendMessage" and "reply_markup" in p:
            return p["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    raise AssertionError("không có nút duyệt")


def test_tra_loi_messenger_cho_duyet_roi_gui(moi_truong):
    # Claude gọi công cụ tra kho trước, rồi mới trả lời
    tra_loi = [
        _res("tool_use", [_block(type="tool_use", id="t1", name="tra_cuu_kho", input={"tu_khoa": "cầu trùng"})]),
        _res("end_turn", [_block(type="text", text="Dạ thuốc cầu trùng ABC giá 85.000đ, còn hàng ạ.")]),
    ]
    with patch.object(brain._client.beta.messages, "create", side_effect=tra_loi) as goi:
        payload = {"object": "page", "entry": [{"messaging": [
            {"sender": {"id": "khach1"}, "message": {"text": "thuốc cầu trùng giá sao shop"}}]}]}
        for sk in facebook.tach_su_kien(payload):
            from agent.modules import tra_loi_khach
            tra_loi_khach.xu_ly_tin_khach(sk["kenh"], sk["khach_id"], sk["text"])
    # Lần gọi thứ 2 phải mang kết quả tra kho
    kq_tool = goi.call_args_list[1].kwargs["messages"][-1]["content"][0]
    assert "85,000đ" in kq_tool["content"]

    # Chưa được gửi cho khách khi anh chưa duyệt
    with patch.object(facebook, "_post", return_value={"ok": 1}) as fb:
        cb = _nut_ok(moi_truong)
        assert fb.call_count == 0
        update = {"callback_query": {"id": "c", "data": cb, "message": {"message_id": 5, "chat": {"id": 111}}}}
        dieu_khien.xu_ly_update(update)
        dieu_khien.xu_ly_update(update)  # bấm 2 lần không được gửi trùng
    assert fb.call_count == 1
    assert fb.call_args.args[0] == "me/messages"
    assert fb.call_args.args[1]["recipient"]["id"] == "khach1"


def test_sua_ban_nhap(moi_truong):
    with patch.object(brain._client.beta.messages, "create",
                      return_value=_res("end_turn", [_block(type="text", text="Bản cũ")])):
        from agent.modules import tra_loi_khach
        tra_loi_khach.xu_ly_tin_khach("zalo", "z1", "alo shop")
    bn_id = _nut_ok(moi_truong).split(":")[1]
    msg = {"message_id": 1, "chat": {"id": 111}}
    dieu_khien.xu_ly_update({"callback_query": {"id": "c", "data": f"sua:{bn_id}", "message": msg}})
    dieu_khien.xu_ly_update({"message": {"chat": {"id": 111}, "text": "Bản mới anh tự viết"}})
    assert storage.lay_ban_nhap(bn_id)["noi_dung"] == "Bản mới anh tự viết"
    with patch("agent.kenh.zalo.gui_tin") as zl:
        dieu_khien.xu_ly_update({"callback_query": {"id": "c", "data": f"ok:{bn_id}", "message": msg}})
    zl.assert_called_once_with("z1", "Bản mới anh tự viết")


def test_dang_bai_facebook(moi_truong):
    bai = json.dumps({"noi_dung": "Cầu trùng là nỗi lo...", "hashtag": ["#annhung"]})
    with patch.object(brain._client.beta.messages, "create",
                      return_value=_res("end_turn", [_block(type="text", text=bai)])):
        dang_bai.soan_bai()
    cb = _nut_ok(moi_truong)
    with patch.object(facebook, "_post", return_value={"post_id": "p1"}) as fb:
        dieu_khien.xu_ly_update({"callback_query": {"id": "c", "data": cb,
                                                    "message": {"message_id": 2, "chat": {"id": 111}}}})
    assert fb.call_args.args[0] == "999/photos"
    assert "SP01" in storage.da_dang_gan_day()


def test_nguoi_la_khong_dieu_khien_duoc(moi_truong):
    with patch.object(brain._client.beta.messages, "create") as goi:
        dieu_khien.xu_ly_update({"message": {"chat": {"id": 222}, "text": "/thuy gà ốm"}})
    goi.assert_not_called()


def test_lenh_thuy(moi_truong):
    with patch.object(brain._client.beta.messages, "create",
                      return_value=_res("end_turn", [_block(type="text", text="1. Tóm tắt ca...")])):
        dieu_khien.xu_ly_update({"message": {"chat": {"id": 111}, "text": "/thuy gà 20 ngày phân máu"}})
    assert any("TƯ VẤN THÚ Y" in t for t in _tin_tg(moi_truong))
