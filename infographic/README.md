# Infographic sản phẩm An Nhung

Bộ công cụ cho skill `mo-ta-va-infographic-thu-y`: mỗi sản phẩm dựng bộ 5 ảnh vuông 800 x 800 (anh chốt 17/11/2026: chỉ một cỡ duy nhất; JPG chất lượng cao nhất, vài trăm KB, up thẳng KiotViet/MXH) + 1 video 9:16 1080 x 1920 ~35 giây.

Ảnh vuông: bố cục khung 1200 x 1200 (`assets/an_nhung_800.css` + `assets/an_nhung_800.js` tự thu gọn khi nhiều chữ), logo + tên sản phẩm ở đầu, ảnh sản phẩm bên trái, ô thông tin bên phải, chụp 2x rồi thu về 800 x 800. Nền ảnh vuông là `nen_vuong.png`; video vẫn dùng `an_nhung.css` + `nen_chim.png`.

| Ảnh | Mẫu | Nội dung |
|---|---|---|
| 1 | `assets/mau_1_bia.html` | Bìa (có logo): sản phẩm lớn + 3 nhãn nổi bật — ảnh đại diện KiotViet, ảnh đầu album MXH |
| 2 | `assets/mau_2_cong_dung.html` | Công dụng (có logo): 3–5 bệnh/tác dụng + 1 dòng hoạt chất |
| 3 | `assets/mau_3_cach_dung.html` | Cách dùng (có logo): liều theo loài + Dùng cho + Đường dùng + Ngừng thuốc |
| 4 | `assets/mau_4_luu_y.html` | Lưu ý & bảo quản (có logo): 3–4 mẹo dùng + Quy cách / SĐK / Bảo quản |
| 5 | `assets/mau_5_phieu_thong_tin.html` | Phiếu thông tin KHÔNG thương hiệu: không logo, không thông tin An Nhung, chỉ giữ NSX + SĐK — để khách chuyển tiếp cho trại |
| video | `assets/mau_video.html` | TikTok, YouTube Shorts, Reels — mở bài (tên + slogan), thân bài (công dụng, dùng cho con gì, đường dùng), kết bài (nhắn tin, Follow, Like) |

Ảnh 1–4 có logo An Nhung, dùng chung KiotViet + MXH: không số điện thoại, địa chỉ, website, mã QR (hotline nằm ở mô tả KiotViet và caption). Ảnh 5 không logo, không chữ An Nhung. Chân trang cả 5 ảnh: "✔ Hàng chính hãng từ công ty `{{NHA_SAN_XUAT}}`" / "Số đăng ký lưu hành: `{{SDK}}`" (không có SĐK thì bỏ dòng này); ảnh 1–4 thêm dòng "NPP Thú Y An Nhung · slogan".

Nền mặc định là màu chính của bao bì (`<body class="nen-mau">` + `tao_nen_chim.py --kieu-nen mau --mau-dam <MAU_DAM>`): chữ tiêu đề trắng, logo trên thẻ trắng, quầng sáng trắng sau sản phẩm để sản phẩm không chìm. Bỏ class `nen-mau` + `--kieu-nen nhat` để dùng nền nhạt. Ảnh 1 (bìa) phóng to ảnh sản phẩm lấp khoảng trống.
Mỗi ảnh một ý, ít chữ để chữ to (gửi Zalo phóng to không rỗ). Kiểu chữ, cỡ chữ ảnh vuông (khung 1200: tiêu đề 84 px, chữ trong ô 40 px, tối thiểu 36; ảnh ra bằng 2/3), màu ô, chân trang nằm chung trong `assets/an_nhung_800.css`.

Script:
- `scripts/chuan_bi.py <thu_muc>` – tải font + logo, chép `an_nhung_800.css`, `an_nhung_800.js`, `an_nhung.css` + 6 mẫu (không còn mã QR)
- `scripts/lay_mau_bao_bi.py <anh_san_pham.png> --html <các file>` – lấy màu chủ đạo + 4 màu ô từ bao bì, điền cho cả bộ
- `scripts/tao_nen_chim.py` – nền màu bao bì + biểu tượng chìm con vật, mầm bệnh. Ảnh vuông: `--w 1200 --h 1200 --scale 2 --out nen_vuong.png`; video: mặc định 1536 x 2731 `--out nen_chim.png`
- `scripts/xuat_anh_kiotviet.py <file.html> <ra.jpg>` – chụp 2x, thu về 800 x 800, JPG 4:4:4 chất lượng cao nhất (chặn trên 1,9 MB); báo chữ tràn, chân trang bị cắt, ảnh sản phẩm gốc quá nhỏ so với chỗ hiển thị, chỗ `{{...}}` chưa điền, ảnh MXH lỡ có liên hệ; ảnh có QR thì quét lại
- `scripts/tao_video.py video.html --out <ra.mp4>` – chụp từng cảnh của mau_video.html, ghép video 1080 x 1920 ~35 giây (ảnh sản phẩm phóng to dần, công dụng hiện từng ý, chuyển cảnh mờ), chưa có nhạc

Phụ thuộc: Pillow, playwright (+ `playwright install chromium`), qrcode, opencv-python-headless (quét QR), ffmpeg (video).
