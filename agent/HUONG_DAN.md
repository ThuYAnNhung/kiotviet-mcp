# Agent An Nhung: hướng dẫn cài đặt

Agent chạy 24/7. Anh điều khiển và duyệt mọi thứ qua **Telegram**.

| # | Chức năng | File | Kích hoạt |
|---|-----------|------|-----------|
| 1 | Trả lời khách | `modules/tra_loi_khach.py` | Tự động khi có tin Messenger, bình luận Fanpage hoặc Zalo OA; hoặc lệnh `/khach` |
| 2 | Tư vấn thú y | `modules/tu_van_thu_y.py` | Lệnh `/thuy <mô tả ca bệnh>` |
| 3 | Đăng bài Facebook | `modules/dang_bai.py` | Tự động mỗi ngày lúc 8:00; hoặc lệnh `/dangbai` |

Cả 3 chức năng dùng Claude và **tự tra giá, tồn kho trên KiotViet** trước khi trả lời.
**Không có gì được gửi cho khách hay đăng lên Page khi anh chưa bấm ✅ Gửi.**

Muốn thêm chức năng mới: tạo file mới trong `modules/`, rồi thêm lệnh tương ứng vào `modules/dieu_khien.py`.

---

## Bước 1: Tạo bot Telegram (5 phút)
1. Trong Telegram, nhắn cho **@BotFather**, gõ `/newbot`, đặt tên. Bot trả về **token**, điền vào `TELEGRAM_BOT_TOKEN`.
2. Lấy Chat ID của anh: sau khi deploy (bước 4), nhắn cho bot bất kỳ câu nào, bot sẽ trả lời “Chat ID của bạn: …”.
   Điền số đó vào `TELEGRAM_OWNER_CHAT_ID` rồi khởi động lại. Chỉ chat ID này mới ra lệnh và duyệt được.

## Bước 2: Điền thông tin cửa hàng
Sửa file `agent/kien_thuc/thong_tin_cua_hang.md` (hotline, địa chỉ, giao hàng, đổi trả).
Agent đọc file này mỗi lần trả lời. Có thể thêm file `.md` khác như bảng câu hỏi hay gặp hay chính sách.

## Bước 3: Deploy lên Render (hoặc VPS)
Tạo **Web Service mới** trên Render từ repo này (không ảnh hưởng MCP server đang chạy):
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn agent.server:app --host 0.0.0.0 --port $PORT`
- Environment: điền các biến trong file `.env.example`.
- ⚠️ **Gói phải chạy liên tục.** Gói Free của Render tự ngủ sau 15 phút, khi đó lịch đăng bài không chạy được.
- ⚠️ Thêm **Persistent Disk** (VD mount `/var/data`) và đặt `DATA_DIR=/var/data`, nếu không thì mỗi lần deploy sẽ mất bản nháp và lịch sử chat.

Chạy thử trên máy: `cp .env.example .env`, điền khóa, rồi chạy `uvicorn agent.server:app --port 8000`.

## Bước 4: Đăng ký webhook Telegram
Mở trên trình duyệt (thay tên app và secret):
```
https://TEN-APP.onrender.com/setup/telegram?url_goc=https://TEN-APP.onrender.com&secret=TELEGRAM_WEBHOOK_SECRET
```
Thấy `"ok": true` là xong. Nhắn `/help` cho bot để xem các lệnh.

👉 **Đến đây đã dùng được ngay:** `/thuy`, `/khach`, `/ton`, `/dangbai` (xem bài nháp).

## Bước 5: Kết nối Facebook Page (Messenger, bình luận, đăng bài)
1. Vào developers.facebook.com, tạo App (loại Business) rồi thêm sản phẩm **Messenger** và **Webhooks**.
2. Tạo **Page Access Token** dài hạn cho Page An Nhung, với các quyền: `pages_messaging`, `pages_manage_posts`,
   `pages_read_engagement`, `pages_manage_engagement`. Điền vào `FB_PAGE_ACCESS_TOKEN`. Điền ID của Page vào `FB_PAGE_ID`.
3. Lấy **App Secret** (Settings → Basic) và điền vào `FB_APP_SECRET`.
4. Webhooks: Callback URL là `https://TEN-APP.onrender.com/webhook/facebook`, Verify token lấy giá trị `FB_VERIFY_TOKEN`.
   Đăng ký các trường **messages** và **feed** cho Page.
5. Lưu ý: Messenger chỉ cho trả lời trong **24 giờ** kể từ tin cuối của khách, nên anh cần duyệt kịp.
   Muốn khách ngoài admin dùng được thì App phải qua bước App Review của Meta.

## Bước 6: Kết nối Zalo OA
1. Vào developers.zalo.me, tạo App rồi liên kết với OA An Nhung.
2. Lấy `ZALO_APP_ID`, `ZALO_APP_SECRET`, và **OA Secret Key** (mục Webhook) để điền vào `ZALO_OA_SECRET_KEY`.
3. Cấp quyền OA để lấy **Access Token + Refresh Token**, điền vào `ZALO_ACCESS_TOKEN` / `ZALO_REFRESH_TOKEN`.
   Agent tự làm mới token mỗi 12 giờ.
4. Webhook URL: `https://TEN-APP.onrender.com/webhook/zalo`, bật sự kiện **user_send_text**.
5. Lưu ý: OA chỉ gửi tin tư vấn miễn phí trong khung thời gian Zalo cho phép sau khi khách nhắn.

---

## Chi phí Claude ước tính
Mặc định dùng model `claude-opus-5-5`, mức `medium`. Một lần trả lời khách tốn khoảng vài trăm đồng.
Muốn rẻ hơn thì đặt `CLAUDE_MODEL=claude-sonnet-5-5` (khoảng một nửa giá).

## Kiểm thử
```
pip install pytest && python -m pytest tests/ -q
```
