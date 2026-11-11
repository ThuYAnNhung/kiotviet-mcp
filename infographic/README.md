# Infographic sản phẩm An Nhung

Bộ công cụ cho skill `mo-ta-va-infographic-thu-y`: dựng infographic 3:4 (1536x2048) cho KiotViet/Zalo.

- `scripts/chuan_bi.py` – tải font + logo, chép mẫu HTML vào thư mục làm việc
- `scripts/tao_nen_chim.py` – tạo nền chìm con vật + mầm bệnh
- `scripts/lay_mau_bao_bi.py` – lấy 4 màu ô + màu chủ đạo từ bao bì, tự điền vào HTML
- `scripts/xuat_anh_kiotviet.py` – chụp HTML ở 2x, xuất JPG 4:4:4 dưới 1,8 MB + bản xem thử điện thoại
- `assets/mau_infographic.html` – mẫu bố cục: logo trái, 4 ô thông tin màu theo bao bì, hotline ở chân trang

Phụ thuộc: Pillow, playwright (+ `playwright install chromium`).
