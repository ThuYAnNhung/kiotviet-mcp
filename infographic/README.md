# Infographic sản phẩm An Nhung

Bộ công cụ cho skill `mo-ta-va-infographic-thu-y`: mỗi sản phẩm dựng bộ 5 ảnh vuông 800 x 800 (anh chốt 17/11/2026: chỉ một cỡ duy nhất; JPG chất lượng cao nhất, vài trăm KB, up thẳng KiotViet/MXH) + 1 video 9:16 1080 x 1920 ~35 giây.

Ảnh vuông: bố cục khung 1200 x 1200 (`assets/an_nhung_800.css` + `assets/an_nhung_800.js` tự thu gọn khi nhiều chữ), logo + tên sản phẩm ở đầu, ảnh sản phẩm bên trái, ô thông tin bên phải, chụp 2x rồi thu về 800 x 800. Nền ảnh vuông là `nen_vuong.png`; video vẫn dùng `an_nhung.css` + `nen_chim.png`.

| Ảnh | Mẫu | Dùng ở đâu |
|---|---|---|
| 1 | `assets/mau_infographic.html` | KiotViet, gửi khách Zalo, website — sản phẩm trái, 3 ô Thành phần / Công dụng / Liều dùng xếp dọc bên phải, ô Đối tượng thu nhỏ góc dưới trái + Quy cách / SĐK, chân trang đầy đủ (không QR) |
| 2 | `assets/mau_mxh_2_bia.html` | Mạng xã hội — bìa, ảnh sản phẩm lớn + 3 điểm nổi bật |
| 3 | `assets/mau_mxh_3_thanh_phan_cong_dung.html` | Mạng xã hội — thành phần & công dụng |
| 4 | `assets/mau_mxh_4_doi_tuong_lieu_dung.html` | Mạng xã hội — liều dùng + ô Đối tượng thu nhỏ, đường dùng, ngừng thuốc |
| 5 | `assets/mau_mxh_5_tu_van.html` | Mạng xã hội — tư vấn sử dụng, quy cách, SĐK, bảo quản |
| video | `assets/mau_video.html` | TikTok, YouTube Shorts, Reels — mở bài (tên + slogan), thân bài (công dụng, dùng cho con gì, đường dùng), kết bài (nhắn tin, Follow, Like) |

Ảnh 2–5 chỉ có logo An Nhung: không số điện thoại, địa chỉ, website, mã QR. Chân trang cả 5 ảnh: "✔ Hàng chính hãng từ công ty `{{NHA_SAN_XUAT}}`" / "Số đăng ký lưu hành: `{{SDK}}`" (không có SĐK thì bỏ dòng này); ảnh MXH thêm dòng "NPP Thú Y An Nhung · slogan".

Nền mặc định là màu chính của bao bì (`<body class="nen-mau">` + `tao_nen_chim.py --kieu-nen mau --mau-dam <MAU_DAM>`): chữ tiêu đề trắng, logo trên thẻ trắng, quầng sáng trắng sau sản phẩm để sản phẩm không chìm. Bỏ class `nen-mau` + `--kieu-nen nhat` để dùng nền nhạt. Ảnh 2 (bìa) phóng to ảnh sản phẩm lấp khoảng trống.
Kiểu chữ, cỡ chữ ảnh vuông (khung 1200: tiêu đề 76 px, chữ trong ô 30 px; ảnh ra bằng 2/3), màu ô, chân trang nằm chung trong `assets/an_nhung_800.css`.

Script:
- `scripts/chuan_bi.py <thu_muc>` – tải font + logo, chép `an_nhung_800.css`, `an_nhung_800.js`, `an_nhung.css` + 6 mẫu (không còn mã QR)
- `scripts/lay_mau_bao_bi.py <anh_san_pham.png> --html <các file>` – lấy màu chủ đạo + 4 màu ô từ bao bì, điền cho cả bộ
- `scripts/tao_nen_chim.py` – nền màu bao bì + biểu tượng chìm con vật, mầm bệnh. Ảnh vuông: `--w 1200 --h 1200 --scale 2 --out nen_vuong.png`; video: mặc định 1536 x 2731 `--out nen_chim.png`
- `scripts/xuat_anh_kiotviet.py <file.html> <ra.jpg>` – chụp 2x, thu về 800 x 800, JPG 4:4:4 chất lượng cao nhất (chặn trên 1,9 MB); báo chữ tràn, chân trang bị cắt, ảnh sản phẩm gốc quá nhỏ so với chỗ hiển thị, chỗ `{{...}}` chưa điền, ảnh MXH lỡ có liên hệ; ảnh có QR thì quét lại
- `scripts/tao_video.py video.html --out <ra.mp4>` – chụp từng cảnh của mau_video.html, ghép video 1080 x 1920 ~35 giây (ảnh sản phẩm phóng to dần, công dụng hiện từng ý, chuyển cảnh mờ), chưa có nhạc

Phụ thuộc: Pillow, playwright (+ `playwright install chromium`), qrcode, opencv-python-headless (quét QR), ffmpeg (video).
