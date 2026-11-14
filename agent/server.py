"""Máy chủ chính của Agent An Nhung.

Chạy:  uvicorn agent.server:app --host 0.0.0.0 --port 8000

Webhook:
  /webhook/telegram   — lệnh và nút duyệt của anh
  /webhook/facebook   — tin Messenger + bình luận Fanpage
  /webhook/zalo       — tin Zalo OA
Lịch:
  Mỗi ngày DANG_BAI_GIO:DANG_BAI_PHUT — soạn bài Facebook
  Mỗi 12 giờ — làm mới token Zalo
"""
import json
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from . import config, storage
from .kenh import facebook, telegram, zalo
from .modules import dang_bai, dieu_khien, tra_loi_khach

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("agent")

lich = BackgroundScheduler(timezone=config.TIMEZONE)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    storage.khoi_tao()
    thieu = config.kiem_tra_cau_hinh()
    if thieu:
        log.warning("Thiếu cấu hình: %s", ", ".join(thieu))

    lich.add_job(dang_bai.soan_bai, "cron", hour=config.DANG_BAI_GIO, minute=config.DANG_BAI_PHUT, id="dang_bai")
    if config.ZALO_APP_ID:
        lich.add_job(zalo.lam_moi_token, "interval", hours=12, id="zalo_token")
    lich.start()
    log.info("Agent đã khởi động. Đăng bài lúc %02d:%02d mỗi ngày.", config.DANG_BAI_GIO, config.DANG_BAI_PHUT)
    yield
    lich.shutdown(wait=False)


app = FastAPI(title="Agent An Nhung", lifespan=lifespan)


@app.get("/")
def suc_khoe():
    return {"status": "ok", "thieu_cau_hinh": config.kiem_tra_cau_hinh()}


# ---------- Telegram ----------
@app.post("/webhook/telegram")
async def webhook_telegram(
    request: Request,
    bg: BackgroundTasks,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if config.TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != config.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(403)
    update = await request.json()
    bg.add_task(dieu_khien.xu_ly_update, update)  # trả 200 ngay, xử lý sau để Telegram không gửi lại
    return {"ok": True}


@app.get("/setup/telegram")
def setup_telegram(url_goc: str = Query(..., description="VD: https://ten-app.onrender.com"), secret: str = ""):
    """Mở 1 lần trên trình duyệt để đăng ký webhook Telegram."""
    if config.TELEGRAM_WEBHOOK_SECRET and secret != config.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(403, "Sai secret")
    return telegram.dat_webhook(url_goc.rstrip("/") + "/webhook/telegram")


# ---------- Facebook ----------
@app.get("/webhook/facebook")
def facebook_xac_minh(
    mode: str = Query(alias="hub.mode", default=""),
    token: str = Query(alias="hub.verify_token", default=""),
    challenge: str = Query(alias="hub.challenge", default=""),
):
    if mode == "subscribe" and token == config.FB_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(403)


@app.post("/webhook/facebook")
async def webhook_facebook(request: Request, bg: BackgroundTasks):
    body = await request.body()
    if not facebook.kiem_tra_chu_ky(body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(403)
    for sk in facebook.tach_su_kien(json.loads(body)):
        bg.add_task(tra_loi_khach.xu_ly_tin_khach, sk["kenh"], sk["khach_id"], sk["text"], sk["ten"])
    return {"ok": True}


# ---------- Zalo ----------
@app.post("/webhook/zalo")
async def webhook_zalo(request: Request, bg: BackgroundTasks):
    body = await request.body()
    payload = json.loads(body)
    if not zalo.kiem_tra_chu_ky(body, payload.get("timestamp", ""), request.headers.get("x-zevent-signature")):
        raise HTTPException(403)
    for sk in zalo.tach_su_kien(payload):
        bg.add_task(tra_loi_khach.xu_ly_tin_khach, sk["kenh"], sk["khach_id"], sk["text"], sk["ten"])
    return {"ok": True}
