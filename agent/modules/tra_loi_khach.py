"""CHỨC NĂNG 1: Trả lời khách tự động (Messenger, bình luận Fanpage, Zalo OA, hoặc dán qua Telegram).

Luồng: tin khách → Claude soạn (tự tra giá/tồn kho) → gửi bản nháp về Telegram → anh bấm ✅ mới gửi khách.
"""
import logging

from .. import brain, storage
from ..kenh import telegram

log = logging.getLogger(__name__)

HE_THONG = """Bạn là nhân viên tư vấn bán hàng của An Nhung (thuốc thú y), nhắn tin thay anh An.

CÁCH TRẢ LỜI
- Xưng "em", gọi khách là "anh/chị" (hoặc "cô/chú" nếu khách lớn tuổi). Thân thiện, ngắn gọn như nhắn tin Zalo: 2–5 câu.
- Không dùng markdown, không gạch đầu dòng dài; có thể dùng 1–2 emoji.
- Hỏi giá / còn hàng: BẮT BUỘC dùng công cụ tra_cuu_kho trước. Chỉ báo giá và tồn kho đúng như kết quả tra cứu.
  Không tìm thấy thì nói sẽ kiểm tra lại và báo khách sau, không tự bịa giá.
- Hỏi về bệnh vật nuôi: hỏi thêm thông tin còn thiếu (loài, tuổi/cân nặng, số con bệnh, triệu chứng, bao lâu rồi).
  Có thể gợi ý sản phẩm có trong kho, nhưng liều dùng phải theo nhãn và luôn khuyên khách gọi hotline để bác sĩ tư vấn kỹ.
  Ca nặng (chết nhiều, bỏ ăn hoàn toàn, nghi dịch bệnh nguy hiểm) → khuyên báo thú y địa phương và gọi hotline ngay.
- Khiếu nại / đổi trả / giao hàng chậm: xin lỗi, ghi nhận, nói anh An sẽ liên hệ trực tiếp. Không hứa bồi thường.
- Kết thúc bằng lời mời mua hàng hoặc hotline khi phù hợp.

CHỈ TRẢ VỀ đúng nội dung tin nhắn sẽ gửi cho khách, không thêm giải thích."""

TEN_KENH = {
    "messenger": "Messenger",
    "fb_comment": "Bình luận Fanpage",
    "zalo": "Zalo OA",
    "telegram": "Dán từ Telegram",
}


def xu_ly_tin_khach(kenh: str, khach_id: str, text: str, ten: str = "") -> str:
    """Soạn trả lời cho một tin khách và gửi bản nháp về Telegram. Trả về mã nháp."""
    lich_su = storage.lay_chat(kenh, khach_id) if kenh != "telegram" else []
    storage.luu_chat(kenh, khach_id, "khach", text)

    if lich_su:
        hoi_thoai = "\n".join(f"{'Khách' if m['vai_tro'] == 'khach' else 'Shop'}: {m['noi_dung']}" for m in lich_su)
        yeu_cau = f"Hội thoại trước đó:\n{hoi_thoai}\n\nTin mới của khách:\n{text}"
    else:
        yeu_cau = f"Tin nhắn của khách:\n{text}"
    if kenh == "fb_comment":
        yeu_cau += "\n\n(Đây là bình luận công khai: trả lời ngắn 1–2 câu, mời khách nhắn tin Page để tư vấn kỹ, không nêu giá chi tiết.)"

    try:
        nhap = brain.hoi_claude(HE_THONG, yeu_cau)
    except Exception as e:  # noqa: BLE001
        log.exception("Lỗi soạn trả lời")
        telegram.gui(f"⚠️ Không soạn được trả lời cho khách ({TEN_KENH.get(kenh, kenh)}): {e}\n\nTin khách: {text}")
        return ""

    bn_id = storage.tao_ban_nhap(
        "tra_loi_khach", kenh, khach_id, nhap, {"tin_khach": text, "ten": ten}
    )
    ai = f" — {ten}" if ten else ""
    if kenh == "telegram":
        # Chế độ dán tay: anh tự copy gửi khách, không cần nút gửi
        telegram.gui(f"💬 Gợi ý trả lời:\n\n{nhap}")
        storage.cap_nhat_ban_nhap(bn_id, trang_thai="da_gui")
    else:
        telegram.gui_ban_nhap(f"📩 {TEN_KENH.get(kenh, kenh)}{ai}\nKhách: {text}", nhap, bn_id)
    return bn_id
