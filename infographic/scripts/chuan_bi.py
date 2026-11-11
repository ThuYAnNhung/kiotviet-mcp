"""Chuẩn bị thư mục làm infographic: tải font + logo An Nhung vào thư mục làm việc.

Cách dùng:
    python3 chuan_bi.py <thu_muc_lam_viec>

Kết quả trong <thu_muc_lam_viec>:
    fonts/Anton-Regular.ttf, fonts/BeVietnamPro-*.ttf, fonts/NotoEmoji.ttf
    logo_annhung.png   (logo gốc nền trong, bản 1600px từ GitHub dự án)
    mau_infographic.html (bản sao mẫu để điền nội dung)

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
MAU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "mau_infographic.html")


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
    if os.path.exists(MAU) and not os.path.exists(os.path.join(tm, "mau_infographic.html")):
        shutil.copy(MAU, os.path.join(tm, "mau_infographic.html"))
    print(f"OK: đã chuẩn bị font + logo + mẫu HTML trong {tm}")


if __name__ == "__main__":
    main()
