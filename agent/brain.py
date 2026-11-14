"""Bộ não Claude dùng chung: gọi Claude, cho phép Claude tự tra kho KiotViet khi cần."""
import json
import logging

import anthropic

from . import config, kiotviet

log = logging.getLogger(__name__)

_client = anthropic.Anthropic()  # đọc ANTHROPIC_API_KEY từ biến môi trường

# Công cụ Claude được phép dùng (chỉ đọc, không thay đổi dữ liệu)
CONG_CU = [
    {
        "name": "tra_cuu_kho",
        "description": (
            "Tra cứu sản phẩm/thuốc trong kho KiotViet của An Nhung theo tên, hoạt chất hoặc mã. "
            "Trả về giá bán, số lượng tồn và mô tả. Luôn dùng công cụ này trước khi báo giá, "
            "báo còn/hết hàng hoặc đề xuất thuốc cho khách."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tu_khoa": {"type": "string", "description": "Tên, hoạt chất hoặc mã sản phẩm"},
            },
            "required": ["tu_khoa"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]


def _chay_cong_cu(ten: str, dau_vao: dict) -> tuple[str, bool]:
    try:
        if ten == "tra_cuu_kho":
            return kiotviet.dinh_dang_sp(kiotviet.tim_san_pham(dau_vao["tu_khoa"])), False
        return f"Công cụ không tồn tại: {ten}", True
    except Exception as e:  # noqa: BLE001
        log.exception("Lỗi công cụ %s", ten)
        return f"Lỗi khi tra cứu: {e}", True


def doc_kien_thuc() -> str:
    """Ghép các file .md trong agent/kien_thuc/ (thông tin cửa hàng, chính sách...)."""
    phan = []
    for f in sorted(config.KIEN_THUC_DIR.glob("*.md")):
        phan.append(f"## {f.stem}\n{f.read_text(encoding='utf-8')}")
    return "\n\n".join(phan)


def hoi_claude(he_thong: str, tin_nhan: str | list, *, dung_kho: bool = True, max_vong: int = 6) -> str:
    """Gửi yêu cầu tới Claude, tự xử lý vòng gọi công cụ, trả về câu trả lời cuối cùng."""
    messages = [{"role": "user", "content": tin_nhan}]
    system = [
        {
            "type": "text",
            "text": he_thong + "\n\n# KIẾN THỨC CỬA HÀNG\n" + doc_kien_thuc(),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    for _ in range(max_vong):
        try:
            res = _client.beta.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=16000,
                system=system,
                messages=messages,
                tools=CONG_CU if dung_kho else anthropic.omit,
                output_config={"effort": config.CLAUDE_EFFORT},
                # Nếu bị từ chối vì bộ lọc an toàn, tự chuyển sang model dự phòng
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.APIStatusError as e:
            log.error("Lỗi Claude API (%s): %s", e.status_code, e.message)
            raise
        except anthropic.APIConnectionError:
            log.error("Không kết nối được Claude API")
            raise

        if res.stop_reason == "refusal":
            return "(Claude không soạn được nội dung cho yêu cầu này — anh vui lòng tự trả lời.)"

        if res.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": res.content})
            continue

        if res.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": res.content})
            ket_qua = []
            for b in res.content:
                if b.type == "tool_use":
                    noi_dung, loi = _chay_cong_cu(b.name, b.input)
                    ket_qua.append(
                        {"type": "tool_result", "tool_use_id": b.id, "content": noi_dung, "is_error": loi}
                    )
            messages.append({"role": "user", "content": ket_qua})
            continue

        return "\n".join(b.text for b in res.content if b.type == "text").strip()

    return "(Agent tra cứu quá nhiều lần mà chưa xong — anh kiểm tra lại giúp.)"


def hoi_claude_json(he_thong: str, tin_nhan: str, schema: dict) -> dict:
    """Gọi Claude và nhận về JSON đúng cấu trúc (dùng cho bài đăng)."""
    res = _client.beta.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=16000,
        system=he_thong + "\n\n# KIẾN THỨC CỬA HÀNG\n" + doc_kien_thuc(),
        messages=[{"role": "user", "content": tin_nhan}],
        output_config={"effort": config.CLAUDE_EFFORT, "format": {"type": "json_schema", "schema": schema}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if res.stop_reason == "refusal":
        raise RuntimeError("Claude từ chối yêu cầu")
    text = next(b.text for b in res.content if b.type == "text")
    return json.loads(text)
