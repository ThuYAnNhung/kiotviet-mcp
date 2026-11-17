"""Chụp infographic HTML ra ảnh JPG 4K dọc, nét, dung lượng 1,5–1,9 MB (KiotViet giới hạn 2 MB).

Cách dùng:
    python3 xuat_anh_kiotviet.py <file.html> <ten_san_pham>_<so>-<loai>.jpg

Làm gì:
1. Mở HTML bằng Chromium (Playwright), khung bố cục 1536 x 2731 (9:16), chụp ở 2,5x (3840 x 6828)
   để chữ và nét vẽ mịn, không răng cưa.
2. Kiểm tra mọi ảnh trong trang (logo, ảnh sản phẩm, nền chìm) đã tải đủ;
   thiếu ảnh nào thì báo lỗi và dừng, không xuất ảnh hỏng.
3. Thu về 4K dọc 2160 x 3840 bằng LANCZOS + làm nét nhẹ (anh chốt 17/11: ảnh 4K, 1,5–1,9 MB).
   Kiểm tra thêm: còn sót chỗ {{...}} chưa điền; chân trang bị cắt ở mép dưới
   (khung có overflow hidden nên không tự báo); ảnh MXH (không có QR) lỡ chứa
   hotline/website; ảnh có QR thì quét lại xem có ra đúng website không.
4. Lưu JPG chroma 4:4:4 (giữ viền chữ màu sắc nét; JPG mặc định 4:2:0 làm nhoè chữ đỏ/xanh),
   chọn chất lượng CAO NHẤT mà file vẫn ≤ --max-mb (1,9 MB) để up thẳng KiotViet/MXH không cần nén lại.
   Ảnh quá ít chi tiết mà chất lượng tối đa vẫn dưới --min-mb (1,5 MB) thì giữ chất lượng tối đa
   (đó đã là bản nét nhất) và in ghi chú.
5. Tạo thêm bản xem thử như trên điện thoại (rộng 540 px): <ten>_xem-thu-dien-thoai.jpg
   để kiểm tra chữ nhỏ nhất còn đọc được không. Bản này chỉ để kiểm tra, không gửi anh.
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
        hong = pg.evaluate("""() => [...document.images]
            .filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'))""")
        font_thieu = pg.evaluate("""() => ['Anton','Be Vietnam Pro'].concat(document.querySelector('.ic, .hinh') ? ['Noto Emoji'] : [])
            .filter(f => !document.fonts.check('700 40px "' + f + '"') && !document.fonts.check('40px "' + f + '"'))""")
        tran = pg.evaluate("""() => { const HE_SO = """ + f"{he_so_ra:.2f}" + """;
            const loi = [...document.querySelectorAll('.o, .dai, .phu-de, .chan')]
              .filter(e => e.scrollHeight > e.clientHeight + 10 || e.scrollWidth > e.clientWidth + 4)
              .map(e => e.className + ': ' + e.innerText.slice(0, 40));
            const td = document.querySelector('.tieu-de');
            if (td && td.clientHeight > 270) loi.push('tieu-de dài quá 2 dòng: ' + td.innerText.slice(0, 40));
            const sp = document.querySelector('.san-pham');
            if (sp && sp.clientHeight < 400) loi.push('vùng ảnh sản phẩm còn quá thấp (' + sp.clientHeight + 'px)');
            const im = document.querySelector('.san-pham img');
            if (im && im.naturalHeight && im.naturalHeight < im.clientHeight * HE_SO)
              loi.push('ảnh sản phẩm gốc chỉ cao ' + im.naturalHeight + 'px mà hiển thị ' + im.clientHeight + 'px: phóng to sẽ mờ, xin anh ảnh chụp rõ hơn');
            const chan = document.querySelector('.chan');
            if (chan && chan.getBoundingClientRect().bottom > window.innerHeight + 1)
              loi.push('chân trang bị cắt ở mép dưới (' + Math.round(chan.getBoundingClientRect().bottom) + 'px > ' + window.innerHeight + 'px) — rút gọn nội dung ô');
            return loi; }""")
        chu = pg.evaluate("() => document.body.innerText")
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
    if not co_qr and any(x in chu for x in ("0988", "370 387", "thuyannhung.com", "Tô Hiệu")):
        print("CẢNH BÁO: ảnh mạng xã hội không được có hotline, địa chỉ, website — xoá khỏi HTML.")
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
    gioi_han = max_mb * 1024 * 1024
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
    if buf.tell() < min_mb * 1024 * 1024:
        print(f"Ghi chú: ảnh ít chi tiết, chất lượng tối đa {q} chỉ {buf.tell() / 1048576:.2f} MB (< {min_mb} MB) — đây đã là bản nét nhất.")
    return q, buf.tell()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("html")
    p.add_argument("out")
    p.add_argument("--w", type=int, default=1536)
    p.add_argument("--h", type=int, default=2731)
    p.add_argument("--scale", type=float, default=2.5)
    p.add_argument("--ra-w", type=int, default=2160, help="chiều ngang ảnh xuất ra (4K dọc)")
    p.add_argument("--ra-h", type=int, default=3840)
    p.add_argument("--max-mb", type=float, default=1.9)
    p.add_argument("--min-mb", type=float, default=1.5)
    a = p.parse_args()

    to, co_qr = chup(a.html, a.w, a.h, a.scale, a.ra_w / a.w * 0.85)
    anh = to.resize((a.ra_w, a.ra_h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=2))
    q, size = luu_jpg(anh, a.out, a.max_mb, a.min_mb)

    goc, _ = os.path.splitext(a.out)
    xem = goc + "_xem-thu-dien-thoai.jpg"
    anh.resize((540, round(540 * a.ra_h / a.ra_w)), Image.LANCZOS).save(xem, quality=90)
    print(f"OK: {a.out} — {a.ra_w}x{a.ra_h}px, JPG chất lượng {q}, {size / 1024 / 1024:.2f} MB (mục tiêu {a.min_mb}–{a.max_mb} MB)")
    print(f"Bản xem thử điện thoại: {xem}")
    if co_qr:
        kiem_qr(a.out)


if __name__ == "__main__":
    main()
