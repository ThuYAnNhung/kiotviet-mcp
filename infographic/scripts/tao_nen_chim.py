"""Tạo ảnh nền có biểu tượng chìm: con vật trong liều dùng + mầm bệnh trong công dụng.

Cách dùng:
    python3 tao_nen_chim.py --vat-nuoi heo,bo,ga --mam-benh vi-khuan,virus \
        --mau "#1E7B3A" --font <thu_muc>/fonts/NotoEmoji.ttf --out <thu_muc>/nen_chim.png

Tham số:
    --vat-nuoi   các loài có trong LIỀU DÙNG (xem bảng VAT_NUOI bên dưới)
    --mam-benh   các nhóm mầm bệnh bị diệt trong CÔNG DỤNG (xem bảng MAM_BENH)
    --mau        màu chủ đạo lấy từ bao bì (mã hex)
    --do-dam     độ đậm biểu tượng chìm, mặc định 0.08 (0.06–0.12 là dễ nhìn)
    --w --h      kích thước khung, mặc định 1536 x 2048
    --scale      nhân độ phân giải, mặc định 2 (khớp với lúc chụp HTML ở 2x)

Ảnh nền ra là nền sáng (trắng pha rất nhẹ màu chủ đạo) + biểu tượng dạng nét mảnh,
rải đều, xoay nhẹ, xen kẽ con vật và mầm bệnh. Biểu tượng được làm thưa ở vùng giữa
(chỗ đặt ảnh sản phẩm) để sản phẩm luôn nổi bật.
"""
import argparse
import math
import random
import sys

from PIL import Image, ImageDraw, ImageFont

# Mã loài -> ký tự trong font Noto Emoji (bản đơn sắc, giấy phép OFL, dùng thương mại được)
VAT_NUOI = {
    "heo": "🐖", "lon": "🐖", "nai": "🐖", "heo-con": "🐷",
    "bo": "🐄", "be": "🐄", "trau": "🐃", "nghe": "🐃",
    "de": "🐐", "cuu": "🐑", "ngua": "🐎",
    "ga": "🐔", "ga-trong": "🐓", "vit": "🦆", "ngan": "🦆", "ngong": "🦆", "cut": "🐦", "chim": "🐦",
    "cho": "🐕", "meo": "🐈", "tho": "🐇",
    "ca": "🐟", "tom": "🦐", "ong": "🐝",
}
MAM_BENH = ["vi-khuan", "cau-khuan", "virus", "xoan-khuan", "mycoplasma",
            "cau-trung", "ky-sinh-trung", "giun", "nam", "ve-ghe", "con-trung"]


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------- Vẽ mầm bệnh dạng nét (toạ độ trong ô vuông kích thước s) ----------
def ve_virus(d, s, c, lw):
    cx = cy = s / 2
    r = s * 0.24
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=lw)
    for k in range(12):
        a = 2 * math.pi * k / 12
        x1, y1 = cx + r * math.cos(a), cy + r * math.sin(a)
        x2, y2 = cx + r * 1.65 * math.cos(a), cy + r * 1.65 * math.sin(a)
        d.line([x1, y1, x2, y2], fill=c, width=lw)
        rr = lw * 1.6
        d.ellipse([x2 - rr, y2 - rr, x2 + rr, y2 + rr], fill=c)
    for (dx, dy) in [(-0.3, -0.2), (0.25, 0.1), (-0.05, 0.35)]:
        rr = r * 0.12
        d.ellipse([cx + dx * r - rr, cy + dy * r - rr, cx + dx * r + rr, cy + dy * r + rr], outline=c, width=max(1, lw // 2))


def ve_vi_khuan(d, s, c, lw):
    # trực khuẩn: hình con nhộng + lông roi
    x0, y0, x1, y1 = s * 0.08, s * 0.33, s * 0.7, s * 0.67
    d.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) / 2, outline=c, width=lw)
    d.line([x0 + s * 0.12, (y0 + y1) / 2, x1 - s * 0.12, (y0 + y1) / 2], fill=c, width=max(1, lw // 2))
    for k, oy in enumerate((-0.06, 0.0, 0.06)):
        pts = []
        for t in range(0, 31):
            x = x1 + t * s * 0.0085
            y = (y0 + y1) / 2 + oy * s + math.sin(t / 3 + k) * s * 0.025
            pts.append((x, y))
        d.line(pts, fill=c, width=max(1, lw // 2), joint="curve")


def ve_cau_khuan(d, s, c, lw):
    r = s * 0.13
    for (x, y) in [(0.3, 0.3), (0.56, 0.28), (0.43, 0.52), (0.7, 0.52), (0.22, 0.6), (0.53, 0.76)]:
        d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], outline=c, width=lw)


def ve_xoan_khuan(d, s, c, lw):
    pts = [(s * 0.12 + t * s * 0.0076, s / 2 + math.sin(t / 10 * math.pi * 1.2) * s * 0.12) for t in range(101)]
    d.line(pts, fill=c, width=lw, joint="curve")


def ve_mycoplasma(d, s, c, lw):
    rnd = random.Random(7)
    for _ in range(5):
        x, y = rnd.uniform(0.3, 0.7) * s, rnd.uniform(0.3, 0.7) * s
        rx, ry = rnd.uniform(0.1, 0.17) * s, rnd.uniform(0.08, 0.13) * s
        d.ellipse([x - rx, y - ry, x + rx, y + ry], outline=c, width=lw)


def ve_cau_trung(d, s, c, lw):
    cx = cy = s / 2
    d.ellipse([cx - s * 0.2, cy - s * 0.28, cx + s * 0.2, cy + s * 0.28], outline=c, width=lw)
    for (dx, dy) in [(-0.07, -0.1), (0.07, -0.1), (-0.07, 0.1), (0.07, 0.1)]:
        d.ellipse([cx + dx * s - s * 0.05, cy + dy * s - s * 0.08, cx + dx * s + s * 0.05, cy + dy * s + s * 0.08],
                  outline=c, width=max(1, lw // 2))


def ve_nam(d, s, c, lw):
    d.line([s * 0.5, s * 0.85, s * 0.5, s * 0.3], fill=c, width=lw)
    d.line([s * 0.5, s * 0.6, s * 0.3, s * 0.4], fill=c, width=lw)
    d.line([s * 0.5, s * 0.55, s * 0.7, s * 0.35], fill=c, width=lw)
    for (x, y) in [(0.5, 0.25), (0.28, 0.36), (0.72, 0.31)]:
        r = s * 0.07
        d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], outline=c, width=lw)


def ve_ve_ghe(d, s, c, lw):
    cx, cy = s / 2, s / 2
    d.ellipse([cx - s * 0.16, cy - s * 0.2, cx + s * 0.16, cy + s * 0.22], outline=c, width=lw)
    d.ellipse([cx - s * 0.06, cy - s * 0.3, cx + s * 0.06, cy - s * 0.19], outline=c, width=lw)
    for side in (-1, 1):
        for k, oy in enumerate((-0.1, -0.03, 0.04, 0.11)):
            x1, y1 = cx + side * s * 0.15, cy + oy * s
            x2, y2 = cx + side * s * (0.3 + 0.02 * k), cy + oy * s + (k - 1.5) * s * 0.04
            d.line([x1, y1, x2, y2], fill=c, width=max(1, lw // 2))


VE = {"virus": ve_virus, "vi-khuan": ve_vi_khuan, "cau-khuan": ve_cau_khuan, "xoan-khuan": ve_xoan_khuan,
      "mycoplasma": ve_mycoplasma, "cau-trung": ve_cau_trung, "nam": ve_nam, "ve-ghe": ve_ve_ghe}
EMOJI_MAM = {"giun": "🪱", "ky-sinh-trung": "🪱", "con-trung": "🦟"}


def o_bieu_tuong(loai, ma, s, mau, font_path):
    """Trả về ảnh RGBA s x s của một biểu tượng."""
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = max(2, int(s * 0.035))
    if loai == "vat" or ma in EMOJI_MAM:
        ch = VAT_NUOI.get(ma) or EMOJI_MAM[ma]
        f = ImageFont.truetype(font_path, int(s * 0.8))
        try:
            f.set_variation_by_axes([350])  # nét mảnh cho nền chìm
        except Exception:
            pass
        bb = d.textbbox((0, 0), ch, font=f)
        d.text(((s - (bb[2] - bb[0])) / 2 - bb[0], (s - (bb[3] - bb[1])) / 2 - bb[1]), ch, font=f, fill=mau)
    else:
        VE[ma](d, s, mau, lw)
    return im


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--vat-nuoi", default="")
    p.add_argument("--mam-benh", default="")
    p.add_argument("--mau", default="#1E7B3A")
    p.add_argument("--font", required=True, help="đường dẫn NotoEmoji.ttf (do chuan_bi.py tải về)")
    p.add_argument("--out", required=True)
    p.add_argument("--do-dam", type=float, default=0.08)
    p.add_argument("--w", type=int, default=1536)
    p.add_argument("--h", type=int, default=2048)
    p.add_argument("--scale", type=int, default=2)
    p.add_argument("--seed", type=int, default=3)
    a = p.parse_args()

    vat = [v.strip() for v in a.vat_nuoi.split(",") if v.strip()]
    mam = [m.strip() for m in a.mam_benh.split(",") if m.strip()]
    sai = [v for v in vat if v not in VAT_NUOI] + [m for m in mam if m not in MAM_BENH]
    if sai:
        sys.exit(f"LỖI: mã không có trong bảng: {sai}. Loài hợp lệ: {sorted(VAT_NUOI)}; mầm bệnh: {MAM_BENH}")
    ds = [("vat", v) for v in dict.fromkeys(vat)] + [("mam", m) for m in dict.fromkeys(mam)]
    if not ds:
        sys.exit("LỖI: cần ít nhất 1 loài hoặc 1 mầm bệnh.")

    W, H, S = a.w * a.scale, a.h * a.scale, a.scale
    r, g, b = hex_rgb(a.mau)
    # nền: trắng pha 3% màu chủ đạo
    nen = Image.new("RGBA", (W, H), (int(255 * 0.97 + r * 0.03), int(255 * 0.97 + g * 0.03), int(255 * 0.97 + b * 0.03), 255))
    lop = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rnd = random.Random(a.seed)
    mau = (r, g, b, int(255 * a.do_dam))

    o = 250 * S  # bước lưới
    cot, hang = math.ceil(W / o) + 1, math.ceil(H / o) + 1
    thu_tu = []  # xáo trộn để con vật và mầm bệnh xen kẽ đều khắp ảnh
    for hy in range(hang):
        for cx in range(cot):
            x = cx * o + (o / 2 if hy % 2 else 0) + rnd.uniform(-0.18, 0.18) * o
            y = hy * o + rnd.uniform(-0.18, 0.18) * o
            # làm thưa vùng giữa (ảnh sản phẩm) — bỏ qua 2/3 biểu tượng ở đó
            if 0.25 * W < x < 0.75 * W and 0.2 * H < y < 0.52 * H and rnd.random() < 0.67:
                continue
            if not thu_tu:
                thu_tu = ds[:]
                rnd.shuffle(thu_tu)
            loai, ma = thu_tu.pop()
            s = int(rnd.uniform(120, 175) * S)
            ic = o_bieu_tuong(loai, ma, s, mau, a.font).rotate(rnd.uniform(-22, 22), resample=Image.BICUBIC, expand=True)
            px, py = int(x - ic.width / 2), int(y - ic.height / 2)
            # cắt phần tràn mép trái/trên (alpha_composite không nhận toạ độ âm)
            ic = ic.crop((max(0, -px), max(0, -py), ic.width, ic.height))
            lop.alpha_composite(ic, (max(0, px), max(0, py)))
    nen.alpha_composite(lop)
    nen.convert("RGB").save(a.out)
    print(f"OK: nền chìm {W}x{H}px, {len(ds)} loại biểu tượng ({', '.join(m for _, m in ds)}), đậm {a.do_dam} -> {a.out}")


if __name__ == "__main__":
    main()
