"""Đọc cấu hình từ biến môi trường (đặt trên Render/VPS hoặc file .env)."""
import os
from pathlib import Path

try:  # cho phép chạy local với file .env
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# --- Claude ---
CLAUDE_MODEL = _env("CLAUDE_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = _env("CLAUDE_EFFORT", "medium")  # low | medium | high

# --- KiotViet ---
KIOTVIET_CLIENT_ID = _env("KIOTVIET_CLIENT_ID")
KIOTVIET_CLIENT_SECRET = _env("KIOTVIET_CLIENT_SECRET")
KIOTVIET_RETAILER = _env("KIOTVIET_RETAILER")

# --- Telegram (kênh điều khiển của anh) ---
TELEGRAM_BOT_TOKEN = _env("TELEGRAM_BOT_TOKEN")
TELEGRAM_OWNER_CHAT_ID = _env("TELEGRAM_OWNER_CHAT_ID")  # chỉ người này được ra lệnh/duyệt
TELEGRAM_WEBHOOK_SECRET = _env("TELEGRAM_WEBHOOK_SECRET")

# --- Facebook Page / Messenger ---
FB_PAGE_ID = _env("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = _env("FB_PAGE_ACCESS_TOKEN")
FB_APP_SECRET = _env("FB_APP_SECRET")
FB_VERIFY_TOKEN = _env("FB_VERIFY_TOKEN", "annhung-verify")
FB_GRAPH_VERSION = _env("FB_GRAPH_VERSION", "v21.0")

# --- Zalo OA ---
ZALO_APP_ID = _env("ZALO_APP_ID")
ZALO_APP_SECRET = _env("ZALO_APP_SECRET")
ZALO_OA_SECRET_KEY = _env("ZALO_OA_SECRET_KEY")  # dùng kiểm tra chữ ký webhook
ZALO_ACCESS_TOKEN = _env("ZALO_ACCESS_TOKEN")
ZALO_REFRESH_TOKEN = _env("ZALO_REFRESH_TOKEN")

# --- Lịch đăng bài ---
TIMEZONE = _env("TIMEZONE", "Asia/Ho_Chi_Minh")
DANG_BAI_GIO = int(_env("DANG_BAI_GIO", "8"))  # giờ soạn bài mỗi ngày
DANG_BAI_PHUT = int(_env("DANG_BAI_PHUT", "0"))

# --- Lưu trữ ---
DATA_DIR = Path(_env("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "agent.db"

KIEN_THUC_DIR = Path(__file__).resolve().parent / "kien_thuc"


def kiem_tra_cau_hinh() -> list[str]:
    """Trả về danh sách cấu hình còn thiếu (để báo khi khởi động)."""
    thieu = []
    bat_buoc = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_OWNER_CHAT_ID": TELEGRAM_OWNER_CHAT_ID,
        "KIOTVIET_CLIENT_ID": KIOTVIET_CLIENT_ID,
        "KIOTVIET_CLIENT_SECRET": KIOTVIET_CLIENT_SECRET,
        "KIOTVIET_RETAILER": KIOTVIET_RETAILER,
    }
    for ten, gia_tri in bat_buoc.items():
        if not gia_tri:
            thieu.append(ten)
    return thieu
