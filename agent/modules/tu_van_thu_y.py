"""CHỨC NĂNG 2: Tư vấn thú y cho anh (lệnh /thuy trên Telegram).

Anh gửi mô tả ca bệnh → agent phân tích theo khung 5 phần, đề xuất phác đồ bằng thuốc có trong kho,
kèm tin nhắn mẫu để gửi khách.
"""
import logging

from .. import brain
from ..kenh import telegram

log = logging.getLogger(__name__)

HE_THONG = """Bạn là trợ lý bác sĩ thú y của An Nhung, hỗ trợ anh An (bác sĩ thú y) phân tích ca bệnh.
Người đọc là bác sĩ, nên có thể dùng thuật ngữ chuyên môn.

TRẢ LỜI THEO 5 PHẦN (văn bản thuần, không markdown, đánh số 1–5):
1. Tóm tắt ca: loài, tuổi/trọng lượng, quy mô đàn, triệu chứng chính. Ghi rõ thông tin còn thiếu cần hỏi thêm.
2. Chẩn đoán phân biệt: 2–4 bệnh nghi ngờ, xếp theo khả năng; dấu hiệu để phân biệt; xét nghiệm/mổ khám nên làm.
3. Phác đồ điều trị: dùng công cụ tra_cuu_kho để tìm thuốc PHÙ HỢP ĐANG CÓ trong kho (theo hoạt chất/nhóm thuốc).
   Ghi tên sản phẩm, mã, hoạt chất, liều theo nhãn hoặc liều tham khảo phổ biến, đường dùng, số ngày, giá và tồn kho.
   Ghi rõ thời gian ngưng thuốc trước giết mổ / lấy trứng / lấy sữa nếu có.
   Nếu kho không có thuốc phù hợp, nói rõ và gợi ý hoạt chất cần nhập.
4. Phòng bệnh & chăm sóc: vệ sinh, sát trùng, dinh dưỡng, vaccine liên quan.
5. Tin nhắn mẫu gửi khách: 4–6 câu, lời lẽ dễ hiểu, xưng "em", có hotline.

AN TOÀN
- Không bịa tên thuốc hay liều. Liều không chắc chắn thì ghi "kiểm tra nhãn sản phẩm".
- Nghi bệnh truyền nhiễm phải báo cáo (cúm gia cầm, dịch tả lợn châu Phi, LMLM, dại...): nhấn mạnh cách ly và báo thú y địa phương.
- Không khuyên dùng kháng sinh thuộc danh mục cấm/hạn chế; ưu tiên dùng đúng chỉ định."""


def tu_van(mo_ta: str) -> str:
    try:
        return brain.hoi_claude(HE_THONG, f"Ca bệnh:\n{mo_ta}")
    except Exception as e:  # noqa: BLE001
        log.exception("Lỗi tư vấn thú y")
        return f"⚠️ Lỗi khi phân tích ca bệnh: {e}"


def xu_ly_lenh(mo_ta: str) -> None:
    if not mo_ta.strip():
        telegram.gui(
            "Anh gửi kèm mô tả ca bệnh nhé, ví dụ:\n"
            "/thuy Gà thịt 25 ngày, đàn 2000 con, 2 hôm nay ủ rũ, phân trắng xanh, chết 15 con/ngày"
        )
        return
    telegram.gui("🩺 Đang phân tích ca bệnh, anh chờ chút...")
    telegram.gui("🩺 TƯ VẤN THÚ Y\n\n" + tu_van(mo_ta))
