# Infographic sản phẩm An Nhung

Bộ công cụ cho skill `mo-ta-va-infographic-thu-y`: mỗi sản phẩm dựng bộ 5 ảnh dọc 9:16 (1536 x 2731) + 1 video trình chiếu.

| Ảnh | Mẫu | Dùng ở đâu |
|---|---|---|
| 1 | `assets/mau_infographic.html` | KiotViet, gửi khách Zalo, website — chân trang đầy đủ: địa chỉ, hotline, website, mã QR |
| 2 | `assets/mau_mxh_2_bia.html` | Mạng xã hội — bìa, ảnh sản phẩm lớn + 3 điểm nổi bật |
| 3 | `assets/mau_mxh_3_thanh_phan_cong_dung.html` | Mạng xã hội — thành phần & công dụng |
| 4 | `assets/mau_mxh_4_doi_tuong_lieu_dung.html` | Mạng xã hội — đối tượng & liều dùng |
| 5 | `assets/mau_mxh_5_tu_van.html` | Mạng xã hội — tư vấn sử dụng, quy cách, SĐK, bảo quản |

Ảnh 2–5 chỉ có logo An Nhung: không số điện thoại, địa chỉ, website, mã QR. Cả 5 ảnh có câu cam kết chính hãng `{{CAM_KET}}` ở chân trang.
Kiểu chữ, cỡ chữ (tiêu đề 168 px, chữ trong ô 56 px), màu ô, chân trang nằm chung trong `assets/an_nhung.css`.

Script:
- `scripts/chuan_bi.py <thu_muc>` – tải font + logo, chép `an_nhung.css` + 5 mẫu, tạo `qr_web.png` (https://www.thuyannhung.com)
- `scripts/lay_mau_bao_bi.py <anh_san_pham.png> --html <các file>` – lấy màu chủ đạo + 4 màu ô từ bao bì, điền cho cả bộ
- `scripts/tao_nen_chim.py` – nền chìm con vật + mầm bệnh (mặc định 1536 x 2731)
- `scripts/xuat_anh_kiotviet.py <file.html> <ra.jpg>` – chụp 2x, JPG 4:4:4 dưới 1,8 MB + bản xem thử điện thoại; báo chữ tràn, chân trang bị cắt, chỗ `{{...}}` chưa điền, ảnh MXH lỡ có liên hệ; ảnh có QR thì quét lại
- `scripts/tao_video.py <ảnh 2..5> --out <ra.mp4>` – video trình chiếu 1080 x 1920, ~16,5 giây, chưa có nhạc

Phụ thuộc: Pillow, playwright (+ `playwright install chromium`), qrcode, opencv-python-headless (quét QR), ffmpeg (video).
