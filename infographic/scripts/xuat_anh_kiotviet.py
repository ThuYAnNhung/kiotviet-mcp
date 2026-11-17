"""Chụp infographic HTML ra ảnh JPG dọc 9:16, chữ nét, không vỡ khi up KiotViet.

Cách dùng:
    python3 xuat_anh_kiotviet.py <file.html> <ten_san_pham>_<so>-<loai>.jpg            # 1080 x 1920 (mặc định)
    python3 xuat_anh_kiotviet.py <file.html> <ten>.jpg --co 4k                          # 2160 x 3840 (bản cũ)

Anh chốt 17/11 (lần 4): ảnh 4K up lên KiotViet bị KiotViet tự thu nhỏ/nén lại nên chữ vỡ;
cỡ chuẩn là 1080 x 1920 cho cả 5 ảnh. Bố cục, cỡ chữ giữ nguyên (cùng tỷ lệ).

Làm gì:
1. Mở HTML bằng Chromium (Playwright), khung bố cục 1536 x 2731 (9:16), chụp ở 2,5x (3840 x 6828)
   để chữ và nét vẽ mịn, không răng cưa.
2. Kiểm tra mọi ảnh trong trang (logo, ảnh sản phẩm, nền chìm) đã tải đủ;
   thiếu ảnh nào thì báo lỗi và dừng, không xuất ảnh hỏng.
3. Thu về 1080 x 1920 (hoặc 2160 x 3840 với --co 4k) bằng LANCZOS + làm nét nhẹ.
   Kiểm tra thêm: còn sót chỗ {{...}} chưa điền; chân trang bị cắt ở mép dưới
   (khung có overflow hidden nên không tự báo); ảnh MXH lỡ chứa hotline/website.
4. Lưu JPG chroma 4:4:4 (giữ viền chữ màu sắc nét; JPG mặc định 4:2:0 làm nhoè chữ đỏ/xanh),
   chọn chất lượng CAO NHẤT (tối đa --q-max) mà file vẫn ≤ --max-mb (1,9 MB, KiotViet giới hạn 2 MB).
   Bản 1080 thường chỉ 0,5–1 MB ở chất lượng 95: nhẹ nên KiotViet không phải nén lại.
   Bản 4K: chất lượng tối đa vẫn dưới --min-mb (1,5 MB) thì in ghi chú "đã là bản nét nhất".
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
        day_du = pg.evaluate("() => !!document.querySelector('.chan.day-du, img.qr')")
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


def luu_jpg(im, out, max_mb, min_mb, q_max=100):
    """Chọn chất lượng JPG cao nhất (≤ q_max) mà vẫn ≤ max_mb (tìm nhị phân trong 75..q_max)."""
    def nen(q):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, subsampling=0, optimize=True, progressive=True, dpi=(300, 300))
        return buf
    gioi_han = max_mb * 1_000_000  # MB thập phân như KiotViet đếm (2 MB = 2.000.000 byte)
    thap, cao, tot = 75, q_max, None
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
        print(f"Ghi chú: ảnh ít chi tiết, chất lượng tối đa {q} chỉ {buf.tell() / 1e6:.2f} MB (< {min_mb} MB) — đây đã là bản nét nhất.")
    return q, buf.tell()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("html")
    p.add_argument("out")
    p.add_argument("--co", choices=["1080", "4k"], default="1080",
                   help="1080 = 1080x1920 (mặc định, up KiotViet không vỡ chữ); 4k = 2160x3840")
    p.add_argument("--w", type=int, default=1536)
    p.add_argument("--h", type=int, default=2731)
    p.add_argument("--max-mb", type=float, default=1.9)
    a = p.parse_args()
    # Cỡ 1080: chụp 2x (3072 px) rồi thu ~2,8 lần → chữ mịn; nét nhẹ hơn vì ảnh nhỏ.
    CO = {"1080": dict(scale=2.0, ra=(1080, 1920), sharp=(0.8, 55, 2), q_max=95, min_mb=0),
          "4k":   dict(scale=2.5, ra=(2160, 3840), sharp=(1.2, 45, 2), q_max=100, min_mb=1.5)}[a.co]
    a.ra_w, a.ra_h = CO["ra"]
    a.min_mb = CO["min_mb"]

    to, co_qr = chup(a.html, a.w, a.h, CO["scale"], a.ra_w / a.w * 0.85)
    r, pc, th = CO["sharp"]
    anh = to.resize((a.ra_w, a.ra_h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=r, percent=pc, threshold=th))
    q, size = luu_jpg(anh, a.out, a.max_mb, a.min_mb, CO["q_max"])

    goc, _ = os.path.splitext(a.out)
    xem = goc + "_xem-thu-dien-thoai.jpg"
    anh.resize((540, round(540 * a.ra_h / a.ra_w)), Image.LANCZOS).save(xem, quality=90)
    print(f"OK: {a.out} — {a.ra_w}x{a.ra_h}px, JPG chất lượng {q}, {size / 1e6:.2f} MB (tối đa {a.max_mb} MB)")
    print(f"Bản xem thử điện thoại: {xem}")
    if co_qr:
        kiem_qr(a.out)


if __name__ == "__main__":
    main()
