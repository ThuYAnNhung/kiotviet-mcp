"""Xuất ảnh vuông cho KiotViet từ mau_kiotviet_vuong.html (khung bố cục 1080 x 1080).

KiotViet tự thu mọi ảnh sản phẩm về cạnh dài 600 px (đo 17/11/2026: ảnh 1080x1920 và 4K đều bị lưu
thành 338x600). Ảnh vuông 600x600 là cỡ lớn nhất KiotViet giữ nguyên. Anh muốn thêm 800 và 1080.

Cách dùng:
    python3 xuat_anh_vuong.py kv.html <ten>_kiotviet --co 600 800 1080
    → <ten>_kiotviet-600.jpg, <ten>_kiotviet-800.jpg, <ten>_kiotviet-1080.jpg

Chụp 3 lần (3240 px) rồi thu về từng cỡ bằng LANCZOS + làm nét nhẹ, JPG 4:4:4 chất lượng 95.
Báo lỗi nếu còn {{...}} chưa điền, ảnh không tải được, hoặc chữ tràn ô/tràn khung.
"""
import argparse
import io
import os
import re
import sys

from PIL import Image, ImageFilter

KHUNG = 1080
SCALE = 3


def chup(html):
    from playwright.sync_api import sync_playwright
    src = open(html, encoding="utf-8").read()
    con = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", re.sub(r"<!--.*?-->", "", src, flags=re.S))))
    if con:
        sys.exit(f"LỖI: còn chỗ chưa điền: {con}")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": KHUNG, "height": KHUNG}, device_scale_factor=SCALE)
        pg.goto("file://" + os.path.abspath(html))
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        hong = pg.evaluate("() => [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'))")
        if hong:
            sys.exit(f"LỖI: ảnh không tải được: {hong}")
        loi = pg.evaluate("""() => {
            const r = [];
            const chan = document.querySelector('.chan')?.getBoundingClientRect();
            document.querySelectorAll('h1, .phu, .y div, .chan div').forEach(e => {
                const b = e.getBoundingClientRect();
                if (e.scrollWidth > e.clientWidth + 2 || b.right > 1080 || b.left < 0) r.push('tràn ngang: ' + e.innerText.slice(0, 30));
            });
            const y = document.querySelector('.y')?.getBoundingClientRect();
            if (y && chan && y.bottom > chan.top - 8) r.push('3 ý chạm chân trang — rút ngắn chữ');
            const h1 = document.querySelector('h1')?.getBoundingClientRect(), phu = document.querySelector('.phu')?.getBoundingClientRect();
            if (h1 && phu && h1.bottom > phu.top + 4) r.push('tiêu đề 2 dòng đè dòng phụ — rút ngắn tiêu đề hoặc giảm cỡ');
            return r;
        }""")
        png = pg.screenshot(clip={"x": 0, "y": 0, "width": KHUNG, "height": KHUNG})
        b.close()
    for l in loi:
        print("CẢNH BÁO:", l)
    return Image.open(io.BytesIO(png)).convert("RGB")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("html")
    p.add_argument("ten", help="tên file ra, không đuôi (vd. vaq-nano-bac-dong_kiotviet)")
    p.add_argument("--co", type=int, nargs="+", default=[600, 800, 1080])
    a = p.parse_args()
    to = chup(a.html)
    for c in a.co:
        r = 0.6 if c <= 800 else 0.8
        im = to.resize((c, c), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=r, percent=60, threshold=2))
        out = f"{a.ten}-{c}.jpg"
        im.save(out, "JPEG", quality=95, subsampling=0, optimize=True)
        print(f"OK {out}: {c}x{c}, {os.path.getsize(out)/1024:.0f} KB")


if __name__ == "__main__":
    main()
