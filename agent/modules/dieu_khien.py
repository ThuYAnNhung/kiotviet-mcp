"""Điều khiển qua Telegram: lệnh của anh + xử lý nút ✅ Gửi / ✏️ Sửa / ❌ Bỏ."""
import logging

from .. import config, kiotviet, storage
from ..kenh import facebook, telegram, zalo
from . import dang_bai, tra_loi_khach, tu_van_thu_y

log = logging.getLogger(__name__)

HUONG_DAN = """🤖 Agent An Nhung đang chạy.

LỆNH:
/thuy <mô tả ca bệnh> — tư vấn thú y, phác đồ bằng thuốc trong kho
/khach <tin nhắn khách> — soạn câu trả lời để anh copy gửi khách
/dangbai [tên sp hoặc chủ đề] — soạn bài Facebook ngay (bỏ trống = agent tự chọn sp)
/ton <tên sp> — tra giá & tồn kho
/huy — hủy chế độ đang sửa nháp

TỰ ĐỘNG:
• Tin Messenger, bình luận Fanpage, Zalo OA → agent soạn trả lời, gửi anh duyệt
• Mỗi ngày {gio:02d}:{phut:02d} → soạn 1 bài Facebook, gửi anh duyệt

Bấm ✅ Gửi để gửi/đăng, ✏️ Sửa rồi gõ nội dung mới, ❌ Bỏ để hủy."""


def _la_chu(chat_id) -> bool:
    return str(chat_id) == str(config.TELEGRAM_OWNER_CHAT_ID)


def xu_ly_update(update: dict) -> None:
    if "callback_query" in update:
        _xu_ly_nut(update["callback_query"])
    elif "message" in update:
        _xu_ly_tin(update["message"])


# ---------- Tin nhắn / lệnh ----------
def _xu_ly_tin(msg: dict) -> None:
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()
    if not _la_chu(chat_id):
        telegram.gui(f"Bot riêng của An Nhung. Chat ID của bạn: {chat_id}", chat_id=str(chat_id))
        return
    if not text:
        return

    lenh, _, tham_so = text.partition(" ")
    lenh = lenh.split("@")[0].lower()
    tham_so = tham_so.strip()

    if lenh in ("/start", "/help", "/trogiup"):
        telegram.gui(HUONG_DAN.format(gio=config.DANG_BAI_GIO, phut=config.DANG_BAI_PHUT))
    elif lenh == "/thuy":
        tu_van_thu_y.xu_ly_lenh(tham_so)
    elif lenh == "/khach":
        if not tham_so:
            telegram.gui("Anh dán tin của khách sau lệnh, ví dụ: /khach Thuốc trị cầu trùng gà giá bao nhiêu em?")
        else:
            tra_loi_khach.xu_ly_tin_khach("telegram", "owner", tham_so)
    elif lenh == "/dangbai":
        telegram.gui("📝 Đang soạn bài...")
        dang_bai.soan_bai(tham_so)
    elif lenh == "/ton":
        try:
            telegram.gui(kiotviet.dinh_dang_sp(kiotviet.tim_san_pham(tham_so or "", 10)))
        except Exception as e:  # noqa: BLE001
            telegram.gui(f"⚠️ Lỗi tra KiotViet: {e}")
    elif lenh == "/huy":
        storage.kv_set("dang_sua", None)
        telegram.gui("Đã hủy chế độ sửa.")
    elif storage.kv_get("dang_sua"):
        _luu_ban_sua(text)
    else:
        telegram.gui("Em chưa hiểu lệnh. Gõ /help để xem hướng dẫn.")


def _luu_ban_sua(text: str) -> None:
    bn_id = storage.kv_get("dang_sua")
    storage.kv_set("dang_sua", None)
    bn = storage.lay_ban_nhap(bn_id)
    if not bn or bn["trang_thai"] != "dang_sua":
        telegram.gui("Bản nháp này không còn chờ sửa.")
        return
    storage.cap_nhat_ban_nhap(bn_id, noi_dung=text, trang_thai="cho_duyet")
    telegram.gui_ban_nhap("✏️ Bản đã sửa — anh kiểm tra lại:", text, bn_id)


# ---------- Nút duyệt ----------
def _xu_ly_nut(cq: dict) -> None:
    chat_id = cq.get("message", {}).get("chat", {}).get("id")
    if not _la_chu(chat_id):
        telegram.tra_loi_nut(cq["id"], "Không có quyền")
        return
    hanh_dong, _, bn_id = (cq.get("data") or "").partition(":")
    bn = storage.lay_ban_nhap(bn_id)
    if not bn:
        telegram.tra_loi_nut(cq["id"], "Không tìm thấy bản nháp")
        return
    message_id = cq["message"]["message_id"]

    if hanh_dong == "bo":
        if storage.chuyen_trang_thai(bn_id, "cho_duyet", "da_bo"):
            telegram.bo_nut(chat_id, message_id)
            telegram.tra_loi_nut(cq["id"], "Đã bỏ")
        else:
            telegram.tra_loi_nut(cq["id"], f"Nháp đang ở trạng thái: {bn['trang_thai']}")

    elif hanh_dong == "sua":
        if storage.chuyen_trang_thai(bn_id, "cho_duyet", "dang_sua"):
            storage.kv_set("dang_sua", bn_id)
            telegram.bo_nut(chat_id, message_id)
            telegram.tra_loi_nut(cq["id"])
            telegram.gui(f"✏️ Anh gõ nội dung mới cho nháp {bn_id} (hoặc /huy):\n\n{bn['noi_dung']}")
        else:
            telegram.tra_loi_nut(cq["id"], f"Nháp đang ở trạng thái: {bn['trang_thai']}")

    elif hanh_dong == "ok":
        # Khóa trước khi gửi để bấm 2 lần không gửi trùng
        if not storage.chuyen_trang_thai(bn_id, "cho_duyet", "dang_gui"):
            telegram.tra_loi_nut(cq["id"], f"Nháp đang ở trạng thái: {bn['trang_thai']}")
            return
        telegram.tra_loi_nut(cq["id"], "Đang gửi...")
        try:
            ket_qua = gui_ban_nhap(bn)
            storage.cap_nhat_ban_nhap(bn_id, trang_thai="da_gui")
            telegram.bo_nut(chat_id, message_id)
            telegram.gui(f"✅ {ket_qua}")
        except Exception as e:  # noqa: BLE001
            log.exception("Gửi nháp lỗi")
            storage.cap_nhat_ban_nhap(bn_id, trang_thai="cho_duyet")
            telegram.gui(f"⚠️ Gửi thất bại: {e}\nAnh có thể bấm ✅ thử lại.")


def gui_ban_nhap(bn: dict) -> str:
    """Thực sự gửi nội dung ra ngoài — chỉ được gọi sau khi anh bấm ✅."""
    kenh, nguoi_nhan, noi_dung = bn["kenh"], bn["nguoi_nhan"], bn["noi_dung"]
    if bn["loai"] == "tra_loi_khach":
        if kenh == "messenger":
            facebook.gui_messenger(nguoi_nhan, noi_dung)
        elif kenh == "fb_comment":
            facebook.tra_loi_binh_luan(nguoi_nhan, noi_dung)
        elif kenh == "zalo":
            zalo.gui_tin(nguoi_nhan, noi_dung)
        else:
            raise RuntimeError(f"Kênh không hỗ trợ gửi tự động: {kenh}")
        storage.luu_chat(kenh, nguoi_nhan, "shop", noi_dung)
        return f"Đã gửi trả lời khách qua {tra_loi_khach.TEN_KENH.get(kenh, kenh)}."

    if bn["loai"] == "dang_bai":
        kq = facebook.dang_bai(noi_dung, bn["du_lieu"].get("anh"))
        if bn["du_lieu"].get("ma_sp"):
            storage.danh_dau_da_dang(bn["du_lieu"]["ma_sp"])
        return f"Đã đăng bài lên Facebook (id: {kq.get('post_id') or kq.get('id')})."

    raise RuntimeError(f"Loại nháp không rõ: {bn['loai']}")
