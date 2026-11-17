"""Chuẩn bị thư mục làm infographic: tải font + logo An Nhung vào thư mục làm việc.

Cách dùng:
    python3 chuan_bi.py <thu_muc_lam_viec>

Kết quả trong <thu_muc_lam_viec>:
    fonts/Anton-Regular.ttf, fonts/BeVietnamPro-*.ttf, fonts/NotoEmoji.ttf
    logo_annhung.png   (logo gốc nền trong, bản 1600px từ GitHub dự án)
    an_nhung.css + 5 mẫu HTML khung 9:16 (1536 x 2731):
        mau_infographic.html                  ảnh 1 đầy đủ thông tin (KiotViet, Zalo, website)
        mau_mxh_2_bia.html                    ảnh 2 MXH bìa
        mau_mxh_3_thanh_phan_cong_dung.html   ảnh 3 MXH thành phần & công dụng
        mau_mxh_4_doi_tuong_lieu_dung.html    ảnh 4 MXH đối tượng & liều dùng
        mau_mxh_5_tu_van.html                 ảnh 5 MXH tư vấn sử dụng
        mau_video_30s.html                    video 30 giây có giọng đọc + phụ đề (tao_video_30s.py)
        mau_video.html                        video ~35 giây kiểu cũ (dự phòng)
    (Không còn mã QR trên ảnh — anh bỏ 17/11/2026; hàm tao_qr giữ lại nếu sau này cần.)

Tải một lần rồi lưu đệm ở ~/.annhung/ để lần sau không tải lại.
"""
import os
import shutil
import sys
import urllib.request

CACHE = os.path.expanduser("~/.annhung")
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
TAI_NGUYEN = {
    "fonts/Anton-Regular.ttf": GF + "anton/Anton-Regular.ttf",
    "fonts/BeVietnamPro-Regular.ttf": GF + "bevietnampro/BeVietnamPro-Regular.ttf",
    "fonts/BeVietnamPro-SemiBold.ttf": GF + "bevietnampro/BeVietnamPro-SemiBold.ttf",
    "fonts/BeVietnamPro-Bold.ttf": GF + "bevietnampro/BeVietnamPro-Bold.ttf",
    "fonts/BeVietnamPro-ExtraBold.ttf": GF + "bevietnampro/BeVietnamPro-ExtraBold.ttf",
    "fonts/NotoEmoji.ttf": GF + "notoemoji/NotoEmoji%5Bwght%5D.ttf",
    "logo_annhung.png": "https://raw.githubusercontent.com/ThuYAnNhung/kiotviet-mcp/main/brand/AnNhung_logo_1600px_nen-trong.png",
}
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
WEBSITE = "https://www.thuyannhung.com"


def lay(ten, url):
    """Trả về đường dẫn file trong bộ đệm, tải nếu chưa có."""
    dich = os.path.join(CACHE, ten)
    if os.path.exists(dich) and os.path.getsize(dich) > 10_000:
        return dich
    os.makedirs(os.path.dirname(dich), exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dich)
    except Exception as e:
        sys.exit(f"LỖI: không tải được {ten} từ {url} ({e}). Dừng lại, không dựng ảnh thiếu font/logo.")
    if os.path.getsize(dich) < 10_000:
        sys.exit(f"LỖI: file {ten} tải về quá nhỏ, có thể hỏng.")
    return dich


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    tm = sys.argv[1]
    os.makedirs(os.path.join(tm, "fonts"), exist_ok=True)
    for ten, url in TAI_NGUYEN.items():
        shutil.copy(lay(ten, url), os.path.join(tm, ten))
    # Mẫu HTML + CSS: chỉ chép khi chưa có, để không ghi đè file đang điền dở
    for ten in sorted(os.listdir(ASSETS)):
        if ten.endswith((".html", ".css")) and not os.path.exists(os.path.join(tm, ten)):
            shutil.copy(os.path.join(ASSETS, ten), os.path.join(tm, ten))
    print(f"OK: đã chuẩn bị font + logo + 6 mẫu HTML trong {tm}")


def tao_qr(dich):
    """Mã QR website cho chân trang ảnh 1 (đầy đủ thông tin)."""
    if os.path.exists(dich):
        return
    try:
        import qrcode
    except ImportError:
        print("CẢNH BÁO: thiếu thư viện qrcode, chưa tạo qr_web.png. Chạy: pip install qrcode --break-system-packages")
        return
    q = qrcode.QRCode(border=1, box_size=20, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(WEBSITE)
    q.make()
    q.make_image(fill_color="black", back_color="white").save(dich)


if __name__ == "__main__":
    main()
