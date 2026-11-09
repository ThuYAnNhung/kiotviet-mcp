"""Chèn logo An Nhung vào ảnh infographic (bước bắt buộc cuối cùng).

Cách dùng:
    python3 chen_logo.py <anh_vao.png> <anh_ra.png> [--vi-tri top|top-left|top-right] [--ty-le 0.05]

- Logo chiếm khoảng 5% diện tích ảnh (mặc định), đặt giữa phía trên.
- Tự tải logo gốc từ GitHub nếu chưa có trên máy.
- In ra vị trí, kích thước logo để kiểm tra.
"""
import argparse
import os
import sys
import urllib.request

from PIL import Image

LOGO_URL = "https://raw.githubusercontent.com/ThuYAnNhung/kiotviet-mcp/main/brand/AnNhung_logo_1600px_nen-trong.png"
LOGO_PATH = os.path.expanduser("~/.annhung/AnNhung_logo_1600px_nen-trong.png")


def lay_logo():
    """Trả về ảnh logo RGBA, tải về nếu chưa có."""
    try:
        if not os.path.exists(LOGO_PATH):
            os.makedirs(os.path.dirname(LOGO_PATH), exist_ok=True)
            urllib.request.urlretrieve(LOGO_URL, LOGO_PATH)
        logo = Image.open(LOGO_PATH).convert("RGBA")
        if logo.width < 1000:
            raise ValueError("File logo quá nhỏ, có thể tải lỗi")
        return logo
    except Exception as e:
        sys.exit(f"LỖI: không lấy được logo An Nhung ({e}). Dừng lại, không gửi ảnh thiếu logo.")


def chen_logo(anh_vao, anh_ra, vi_tri="top", ty_le=0.05):
    try:
        nen = Image.open(anh_vao).convert("RGBA")
    except Exception as e:
        sys.exit(f"LỖI: không mở được ảnh {anh_vao} ({e})")

    logo = lay_logo()
    W, H = nen.size
    # Diện tích logo ~ ty_le * diện tích ảnh, giữ đúng tỷ lệ logo
    r = logo.width / logo.height
    lw = int(((ty_le * W * H) * r) ** 0.5)
    lw = min(lw, int(W * 0.6))
    lh = round(lw / r)
    logo = logo.resize((lw, lh), Image.LANCZOS)

    le = int(W * 0.04)
    y = int(H * 0.02)
    x = {"top": (W - lw) // 2, "top-left": le, "top-right": W - lw - le}[vi_tri]

    nen.alpha_composite(logo, (x, y))
    nen.convert("RGB").save(anh_ra, quality=95, dpi=(300, 300))
    print(f"OK: logo {lw}x{lh}px tại ({x},{y}) trên ảnh {W}x{H} -> {anh_ra}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("anh_vao")
    p.add_argument("anh_ra")
    p.add_argument("--vi-tri", default="top", choices=["top", "top-left", "top-right"])
    p.add_argument("--ty-le", type=float, default=0.05)
    a = p.parse_args()
    chen_logo(a.anh_vao, a.anh_ra, a.vi_tri, a.ty_le)
