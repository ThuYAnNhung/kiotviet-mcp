"""Lấy bộ màu cho infographic từ chính bao bì sản phẩm.

Cách dùng:
    python3 lay_mau_bao_bi.py <anh_san_pham.png> [--html infographic.html]

Làm gì:
1. Gom màu trên bao bì (bỏ nền trong suốt, bỏ trắng/đen/xám) và xếp theo diện tích.
2. Chọn tối đa 4 màu khác sắc rõ ràng (lệch nhau >= 40 độ trên vòng màu).
3. Bao bì ít hơn 4 màu: bù bằng màu khác sắc, cùng độ đậm, lệch dần quanh màu chủ đạo
   (lệch 90 độ hai phía rồi đối sắc) để 4 ô vẫn dễ phân biệt mà hài hòa.
4. Đưa cả 4 màu về cùng độ đậm (tương phản ~5.8:1 với nền trắng, tối thiểu 4.5:1)
   để chữ đọc rõ và trông đồng bộ, vẫn giữ sắc màu của bao bì.
In ra MAU, MAU_DAM, MAU_O1..MAU_O4 (O1 = Thành phần, O2 = Đối tượng, O3 = Công dụng, O4 = Liều dùng).
Có --html thì điền thẳng vào các chỗ {{MAU}}, {{MAU_DAM}}, {{MAU_O1}}.. trong file đó.
"""
import argparse
import colorsys
import sys

from PIL import Image


def lum(rgb):
    def k(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (k(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def tuong_phan_trang(rgb):
    return 1.05 / (lum(rgb) + 0.05)


def hls_rgb(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (round(r * 255), round(g * 255), round(b * 255))


def lam_doc_ro(h, s, muc=5.8):
    """Giữ sắc h, ép độ bão hòa vừa phải, chọn độ sáng sao cho tương phản với nền trắng
    gần đúng mức `muc` (>= 4.5 là chữ đọc rõ). Mọi màu cùng một mức nên trông cùng độ đậm."""
    s = min(max(s, 0.5), 0.72)
    tot = min((abs(tuong_phan_trang(hls_rgb(h, l / 100, s)) - muc), l) for l in range(12, 61))
    rgb = hls_rgb(h, tot[1] / 100, s)
    if tuong_phan_trang(rgb) < 4.5:  # an toàn: không bao giờ dưới 4.5
        return lam_doc_ro(h, s, muc + 0.5)
    return rgb


def hex_(rgb):
    return "#%02X%02X%02X" % rgb


def lech_sac(a, b):
    d = abs(a - b) % 1
    return min(d, 1 - d) * 360


def mau_bao_bi(path):
    try:
        im = Image.open(path).convert("RGBA")
    except Exception as e:
        sys.exit(f"LỖI: không mở được ảnh {path} ({e})")
    im.thumbnail((300, 300))
    du_lieu = im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()
    px = [p[:3] for p in du_lieu if p[3] > 200]
    if not px:
        sys.exit("LỖI: ảnh không có điểm ảnh rõ (nền trong suốt toàn bộ?).")
    q = Image.new("RGB", (len(px), 1))
    q.putdata(px)
    q = q.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    dem = sorted(q.getcolors(), reverse=True)
    ket = []
    for n, i in dem:
        rgb = tuple(pal[i * 3:i * 3 + 3])
        h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
        if s < 0.25 or l > 0.9 or l < 0.1:      # trắng, đen, xám: không lấy
            continue
        if n / len(px) < 0.01:                  # vệt quá nhỏ (chữ in, bóng) bỏ qua
            continue
        if all(lech_sac(h, h2) >= 40 for h2, _ in ket):
            ket.append((h, s))
    return ket


def main():
    p = argparse.ArgumentParser()
    p.add_argument("anh")
    p.add_argument("--html")
    a = p.parse_args()

    goc = mau_bao_bi(a.anh)[:4]
    if not goc:
        print("CẢNH BÁO: bao bì gần như chỉ trắng/đen/xám — dùng xanh lá thương hiệu làm màu chủ đạo.")
        goc = [(colorsys.rgb_to_hls(0x0B / 255, 0x6E / 255, 0x4F / 255)[0], 0.8)]
    so_mau_bao_bi = len(goc)
    h0, s0 = goc[0]
    # Bù màu: thử lệch dần quanh màu chủ đạo, lấy sắc nào cách đủ xa các màu đã có
    # thứ tự thử: lệch 90 độ hai phía rồi đối sắc 180 độ (bộ 4 màu cân đối quanh vòng màu),
    # sau đó các góc trung gian nếu vẫn trùng với màu bao bì
    for d in (90, -90, 180, 135, -135, 45, -45):
        if len(goc) >= 4:
            break
        h = (h0 + d / 360) % 1
        if all(lech_sac(h, h2) >= 40 for h2, _ in goc):
            goc.append((h, s0))

    o = [lam_doc_ro(h, s) for h, s in goc[:4]]
    mau = lam_doc_ro(h0, s0, 5.0)
    mau_dam = lam_doc_ro(h0, s0, 9.0)
    gia_tri = {"MAU": hex_(mau), "MAU_DAM": hex_(mau_dam),
               **{f"MAU_O{i + 1}": hex_(c) for i, c in enumerate(o)}}
    print(f"Màu lấy từ bao bì: {so_mau_bao_bi}, màu bù thêm: {4 - so_mau_bao_bi}")
    for k, v in gia_tri.items():
        print(f"{k} = {v}")

    if a.html:
        try:
            s = open(a.html, encoding="utf-8").read()
            for k, v in gia_tri.items():
                s = s.replace("{{" + k + "}}", v)
            open(a.html, "w", encoding="utf-8").write(s)
            print(f"OK: đã điền màu vào {a.html}")
        except Exception as e:
            sys.exit(f"LỖI: không ghi được {a.html} ({e})")


if __name__ == "__main__":
    main()
