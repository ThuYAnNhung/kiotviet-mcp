"""Chụp infographic HTML ra ảnh JPG nét, nhẹ, đúng chuẩn up KiotViet và gửi Zalo.

Cách dùng:
    python3 xuat_anh_kiotviet.py <infographic.html> <ten_san_pham.jpg> [--max-mb 1.8]

Làm gì:
1. Mở HTML bằng Chromium (Playwright), khung 1536 x 2048, chụp ở 2x (3072 x 4096)
   để chữ và nét vẽ mịn, không răng cưa.
2. Kiểm tra mọi ảnh trong trang (logo, ảnh sản phẩm, nền chìm) đã tải đủ;
   thiếu ảnh nào thì báo lỗi và dừng, không xuất ảnh hỏng.
3. Thu về 1536 x 2048 bằng LANCZOS + làm nét nhẹ.
4. Lưu JPG chroma 4:4:4 (giữ viền chữ màu sắc nét; JPG mặc định 4:2:0 làm nhoè chữ đỏ/xanh),
   tự hạ chất lượng từ 95 đến khi dưới --max-mb (KiotViet giới hạn ảnh hàng hóa 2 MB).
5. Tạo thêm bản xem thử như trên điện thoại (rộng 540 px): <ten>_xem-thu-dien-thoai.jpg
   để kiểm tra chữ nhỏ nhất còn đọc được không. Bản này chỉ để kiểm tra, không gửi anh.
"""
import argparse
import io
import os
import sys

from PIL import Image, ImageFilter


def chup(html, w, h, scale):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("LỖI: thiếu playwright. Chạy: pip install playwright --break-system-packages && playwright install chromium")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        pg.goto("file://" + os.path.abspath(html))
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        hong = pg.evaluate("""() => [...document.images]
            .filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'))""")
        font_thieu = pg.evaluate("""() => ['Anton','Be Vietnam Pro','Noto Emoji']
            .filter(f => !document.fonts.check('700 40px "' + f + '"') && !document.fonts.check('40px "' + f + '"'))""")
        tran = pg.evaluate("""() => {
            const loi = [...document.querySelectorAll('.o, .dai, .phu-de, .chan')]
              .filter(e => e.scrollHeight > e.clientHeight + 10 || e.scrollWidth > e.clientWidth + 4)
              .map(e => e.className + ': ' + e.innerText.slice(0, 40));
            const td = document.querySelector('.tieu-de');
            if (td && td.clientHeight > 270) loi.push('tieu-de dài quá 2 dòng: ' + td.innerText.slice(0, 40));
            const sp = document.querySelector('.san-pham');
            if (sp && sp.clientHeight < 400) loi.push('vùng ảnh sản phẩm còn quá thấp (' + sp.clientHeight + 'px)');
            return loi; }""")
        png = pg.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h})
        b.close()
    if hong:
        sys.exit(f"LỖI: ảnh không tải được: {hong}. Kiểm tra lại đường dẫn logo/ảnh sản phẩm/nền chìm.")
    if font_thieu:
        print(f"CẢNH BÁO: font chưa nạp: {font_thieu} — chạy lại chuan_bi.py.")
    if tran:
        print("CẢNH BÁO: chữ bị tràn khung, cần rút gọn hoặc giảm cỡ chữ:\n  " + "\n  ".join(tran))
    return Image.open(io.BytesIO(png)).convert("RGB")


def luu_jpg(im, out, max_mb):
    for q in range(95, 74, -3):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, subsampling=0, optimize=True, progressive=True, dpi=(300, 300))
        if buf.tell() <= max_mb * 1024 * 1024:
            open(out, "wb").write(buf.getvalue())
            return q, buf.tell()
    sys.exit("LỖI: không nén được dưới giới hạn dung lượng mà vẫn giữ chất lượng >= 75. Giảm chi tiết nền.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("html")
    p.add_argument("out")
    p.add_argument("--w", type=int, default=1536)
    p.add_argument("--h", type=int, default=2048)
    p.add_argument("--scale", type=int, default=2)
    p.add_argument("--max-mb", type=float, default=1.8)
    a = p.parse_args()

    to = chup(a.html, a.w, a.h, a.scale)
    anh = to.resize((a.w, a.h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.0, percent=45, threshold=2))
    q, size = luu_jpg(anh, a.out, a.max_mb)

    goc, _ = os.path.splitext(a.out)
    xem = goc + "_xem-thu-dien-thoai.jpg"
    anh.resize((540, round(540 * a.h / a.w)), Image.LANCZOS).save(xem, quality=90)
    print(f"OK: {a.out} — {a.w}x{a.h}px, JPG chất lượng {q}, {size / 1024 / 1024:.2f} MB (giới hạn {a.max_mb} MB)")
    print(f"Bản xem thử điện thoại: {xem}")


if __name__ == "__main__":
    main()
