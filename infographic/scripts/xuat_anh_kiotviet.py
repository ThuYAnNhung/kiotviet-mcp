"""Chụp infographic HTML ra ảnh JPG vuông 800 x 800, nét nhất có thể (anh chốt 17/11/2026: mọi ảnh chỉ một cỡ 800 x 800).

Cách dùng:
    python3 xuat_anh_kiotviet.py <file.html> <ten_san_pham>_<so>-<loai>.jpg

Làm gì:
1. Mở HTML bằng Chromium (Playwright), khung bố cục 1200 x 1200, chụp ở 2x (2400 x 2400)
   để chữ và nét vẽ mịn, không răng cưa.
2. Kiểm tra mọi ảnh trong trang (logo, ảnh sản phẩm, nền chìm) đã tải đủ;
   thiếu ảnh nào thì báo lỗi và dừng, không xuất ảnh hỏng.
3. Thu về 800 x 800 bằng LANCZOS + làm nét nhẹ.
   Kiểm tra thêm: còn sót chỗ {{...}} chưa điền; chân trang bị cắt ở mép dưới
   (khung có overflow hidden nên không tự báo); ảnh MXH lỡ chứa hotline/website.
4. Lưu JPG chroma 4:4:4 (giữ viền chữ màu sắc nét; JPG mặc định 4:2:0 làm nhoè chữ đỏ/xanh),
   chất lượng CAO NHẤT (thường 100); không đặt mức dung lượng tối thiểu. Chỉ chặn trên --max-mb (1,9 MB)
   cho chắc dưới giới hạn 2 MB của KiotViet — ảnh 800 x 800 thực tế chỉ vài trăm KB.
"""
import argparse
import io
import os
import sys

from PIL import Image, ImageFilter

WEBSITE = "https://www.thuyannhung.com"


def chup(html, w, h, scale, he_so_ra):
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
        pg.wait_for_timeout(300)  # chờ an_nhung_800.js tự thu gọn (nếu cần) xong
        hong = pg.evaluate("""() => [...document.images]
            .filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'))""")
        font_thieu = pg.evaluate("""() => ['Anton','Be Vietnam Pro'].concat(document.querySelector('.ic, .hinh') ? ['Noto Emoji'] : [])
            .filter(f => !document.fonts.check('700 40px "' + f + '"') && !document.fonts.check('40px "' + f + '"'))""")
        tran = pg.evaluate("""() => { const HE_SO = """ + f"{he_so_ra:.2f}" + """;
            const loi = [...document.querySelectorAll('.o, .dai, .phu-de, .chan, .cot')]
              .filter(e => e.scrollHeight > e.clientHeight + 10 || e.scrollWidth > e.clientWidth + 4)
              .map(e => e.className + ': ' + e.innerText.slice(0, 40));
            const td = document.querySelector('.tieu-de');
            if (td && td.clientHeight > parseFloat(getComputedStyle(td).lineHeight) * 2 + 4) loi.push('tieu-de dài quá 2 dòng: ' + td.innerText.slice(0, 40));
            const sp = document.querySelector('.san-pham');
            if (sp && sp.clientHeight < 300) loi.push('vùng ảnh sản phẩm còn quá thấp (' + sp.clientHeight + 'px)');
            const im = document.querySelector('.san-pham img');
            if (im && im.naturalHeight && im.naturalHeight < im.clientHeight * HE_SO)
              loi.push('ảnh sản phẩm gốc chỉ cao ' + im.naturalHeight + 'px mà hiển thị ' + im.clientHeight + 'px: phóng to sẽ mờ, xin anh ảnh chụp rõ hơn');
            const chan = document.querySelector('.chan');
            if (chan && chan.getBoundingClientRect().bottom > window.innerHeight + 1)
              loi.push('chân trang bị cắt ở mép dưới (' + Math.round(chan.getBoundingClientRect().bottom) + 'px > ' + window.innerHeight + 'px) — rút gọn nội dung ô');
            return loi; }""")
        chu = pg.evaluate("() => document.body.innerText")
        day_du = pg.evaluate("() => !!document.querySelector('.chan.day-du, img.qr')")
        trang = pg.evaluate("() => !!document.querySelector('.trang')")
        co_logo = pg.evaluate("() => !!document.querySelector('img.logo, img[src*=\"logo\"]')")
        co_qr = pg.evaluate("() => !!document.querySelector('img.qr')")
        png = pg.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h})
        b.close()
    if hong:
        sys.exit(f"LỖI: ảnh không tải được: {hong}. Kiểm tra lại đường dẫn logo/ảnh sản phẩm/nền chìm.")
    if font_thieu:
        print(f"CẢNH BÁO: font chưa nạp: {font_thieu} — chạy lại chuan_bi.py.")
    if tran:
        print("CẢNH BÁO bố cục (chữ tràn ô, chân trang bị cắt, ảnh sản phẩm quá nhỏ...):\n  " + "\n  ".join(tran))
    if "{{" in chu:
        print("CẢNH BÁO: còn chỗ {{...}} chưa điền nội dung.")
    if not day_du and any(x in chu for x in ("0988", "370 387", "thuyannhung.com", "Tô Hiệu")):
        print("CẢNH BÁO: ảnh không được có hotline, địa chỉ, website — xoá khỏi HTML.")
    if trang and (co_logo or "an nhung" in chu.lower()):
        print("CẢNH BÁO: ảnh 5 phiếu thông tin không thương hiệu không được có logo hay chữ An Nhung — xoá khỏi HTML.")
    return Image.open(io.BytesIO(png)).convert("RGB"), co_qr


def kiem_qr(jpg):
    """Quét lại mã QR trên ảnh đã xuất; cần opencv (không có thì bỏ qua, chỉ nhắc)."""
    try:
        import cv2
    except ImportError:
        print("Ghi chú: chưa có opencv-python-headless nên chưa quét thử QR.")
        return
    noi_dung, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(jpg))
    if noi_dung.rstrip("/") == WEBSITE:
        print(f"QR OK: {noi_dung}")
    else:
        print(f"CẢNH BÁO: QR quét ra '{noi_dung}' thay vì {WEBSITE} — kiểm tra lại qr_web.png.")


def luu_jpg(im, out, max_mb, min_mb):
    """Chọn chất lượng JPG cao nhất mà vẫn ≤ max_mb (tìm nhị phân trong 75..100)."""
    def nen(q):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, subsampling=0, optimize=True, progressive=True, dpi=(300, 300))
        return buf
    gioi_han = max_mb * 1_000_000  # MB thập phân như KiotViet đếm (2 MB = 2.000.000 byte)
    if nen(100).tell() <= gioi_han:  # 800 x 800 gần như luôn lọt: lấy luôn bản nét nhất
        buf = nen(100)
        open(out, "wb").write(buf.getvalue())
        return 100, buf.tell()
    thap, cao, tot = 75, 100, None
    while thap <= cao:
        q = (thap + cao) // 2
        buf = nen(q)
        if buf.tell() <= gioi_han:
            tot, thap = (q, buf), q + 1
        else:
            cao = q - 1
    if tot is None:
        sys.exit("LỖI: chất lượng 75 vẫn quá giới hạn dung lượng. Giảm chi tiết nền (--do-dam) rồi xuất lại.")
    q, buf = tot
    open(out, "wb").write(buf.getvalue())
    if min_mb and buf.tell() < min_mb * 1_000_000:
        print(f"Ghi chú: chất lượng {q}, {buf.tell() / 1e6:.2f} MB.")
    return q, buf.tell()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("html")
    p.add_argument("out")
    p.add_argument("--w", type=int, default=1200, help="khung bố cục (an_nhung_800.css)")
    p.add_argument("--h", type=int, default=1200)
    p.add_argument("--scale", type=float, default=2)
    p.add_argument("--ra-w", type=int, default=800, help="ảnh xuất ra: chỉ một cỡ 800 x 800")
    p.add_argument("--ra-h", type=int, default=800)
    p.add_argument("--max-mb", type=float, default=1.9)
    p.add_argument("--min-mb", type=float, default=0)
    a = p.parse_args()

    to, co_qr = chup(a.html, a.w, a.h, a.scale, a.ra_w / a.w * 0.85)
    anh = to.resize((a.ra_w, a.ra_h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=2))
    q, size = luu_jpg(anh, a.out, a.max_mb, a.min_mb)
    print(f"OK: {a.out} — {a.ra_w}x{a.ra_h}px, JPG chất lượng {q}, {size / 1000:.0f} KB")
    if co_qr:
        kiem_qr(a.out)


if __name__ == "__main__":
    main()
