"""CHỨC NĂNG 3: Đăng bài Facebook Page mỗi ngày.

Mỗi sáng: chọn 1 sản phẩm còn hàng (chưa đăng trong 30 ngày) từ KiotViet → Claude viết bài
→ gửi Telegram cho anh duyệt → bấm ✅ thì đăng lên Page (kèm ảnh sản phẩm nếu có).
"""
import logging
import random

from .. import brain, kiotviet, storage
from ..kenh import telegram

log = logging.getLogger(__name__)

HE_THONG = """Bạn là người viết nội dung Facebook cho An Nhung (thuốc thú y).
Viết bài bán hàng/giáo dục cho người chăn nuôi, giọng gần gũi, đáng tin, đúng chuyên môn.

CẤU TRÚC BÀI (150–250 chữ, văn bản thuần, xuống dòng rõ ràng, emoji vừa phải):
- Câu mở đầu đánh vào vấn đề người chăn nuôi hay gặp.
- Giới thiệu sản phẩm: công dụng chính, đối tượng dùng, điểm nổi bật. Chỉ dùng thông tin có trong dữ liệu sản phẩm
  và kiến thức chung chắc chắn. Không bịa thành phần, liều lượng, cam kết "khỏi 100%".
- Mẹo chăn nuôi ngắn liên quan.
- Lời kêu gọi: nhắn tin Page hoặc gọi hotline (lấy từ kiến thức cửa hàng).
- Không ghi giá trừ khi được yêu cầu."""

SCHEMA = {
    "type": "object",
    "properties": {
        "noi_dung": {"type": "string", "description": "Toàn bộ nội dung bài đăng"},
        "hashtag": {"type": "array", "items": {"type": "string"}, "description": "3–6 hashtag, có dấu #"},
    },
    "required": ["noi_dung", "hashtag"],
    "additionalProperties": False,
}


def chon_san_pham() -> dict | None:
    da_dang = storage.da_dang_gan_day()
    ung_vien = []
    for vi_tri in (0, 100, 200):
        ds = kiotviet.danh_sach_san_pham(100, vi_tri)
        ung_vien += [sp for sp in ds if (sp["ton"] or 0) > 0 and sp["ma"] not in da_dang]
        if len(ds) < 100:
            break
    return random.choice(ung_vien) if ung_vien else None


def soan_bai(chu_de: str = "") -> None:
    """Soạn 1 bài và gửi về Telegram chờ duyệt. Gọi theo lịch hoặc lệnh /dangbai."""
    try:
        if chu_de:
            ds = kiotviet.tim_san_pham(chu_de, 1)
            sp = ds[0] if ds else None
        else:
            sp = chon_san_pham()

        if sp:
            yeu_cau = (
                f"Viết bài giới thiệu sản phẩm sau:\n{kiotviet.dinh_dang_sp([sp])}"
                + (f"\nGóc độ anh muốn: {chu_de}" if chu_de else "")
            )
        elif chu_de:
            yeu_cau = f"Viết bài chia sẻ kiến thức chăn nuôi/thú y về chủ đề: {chu_de}"
        else:
            telegram.gui("⚠️ Hôm nay không tìm được sản phẩm còn hàng để đăng bài.")
            return

        bai = brain.hoi_claude_json(HE_THONG, yeu_cau, SCHEMA)
        noi_dung = bai["noi_dung"].strip() + "\n\n" + " ".join(bai["hashtag"])
        bn_id = storage.tao_ban_nhap(
            "dang_bai",
            "facebook_page",
            "",
            noi_dung,
            {"ma_sp": sp["ma"] if sp else None, "anh": sp["anh"] if sp else None},
        )
        tieu_de = "📝 BÀI ĐĂNG FACEBOOK" + (f" — {sp['ten']}" if sp else "")
        if sp and sp.get("anh"):
            tieu_de += f"\n🖼 Ảnh: {sp['anh']}"
        telegram.gui_ban_nhap(tieu_de, noi_dung, bn_id)
    except Exception as e:  # noqa: BLE001
        log.exception("Lỗi soạn bài")
        telegram.gui(f"⚠️ Lỗi khi soạn bài đăng: {e}")
